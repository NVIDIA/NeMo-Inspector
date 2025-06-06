# Copyright (c) 2024, NVIDIA CORPORATION.  All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import inspect
import logging
from typing import Callable, Dict, List, Union

import dash_bootstrap_components as dbc
import requests
from dash import dcc, html
from flask import current_app

from nemo_skills.code_execution.sandbox import get_sandbox
from nemo_skills.evaluation.math_grader import extract_answer
from nemo_skills.inference.server.code_execution_model import get_code_execution_model
from nemo_skills.inference.server.model import get_model
from nemo_skills.prompt.utils import Prompt, PromptConfig

from nemo_inspector.layouts import (
    get_input_group_layout,
    get_results_content_layout,
    get_single_prompt_output_layout,
    get_text_area_layout,
    get_text_modes_layout,
)
from nemo_inspector.settings.constants import (
    FEW_SHOTS_INPUT,
    QUERY_INPUT_TYPE,
    RETRIEVAL,
    RETRIEVAL_FIELDS,
    SEPARATOR_ID,
)
from nemo_inspector.utils.common import (
    get_examples_map,
    get_utils_from_config,
    initialize_default,
)


class ModeStrategies:
    def __init__(self):
        self.sandbox = None

    def sandbox_init(self):
        if self.sandbox is None and "sandbox" in current_app.config["nemo_inspector"]:
            self.sandbox = get_sandbox(
                **current_app.config["nemo_inspector"]["sandbox"],
            )

    def get_utils_input_layout(
        self,
        condition: Callable[
            [str, Union[str, int, float, bool]], bool
        ] = lambda key, value: True,
        disabled: bool = False,
    ) -> List[dbc.AccordionItem]:
        utils = get_utils_from_config(current_app.config["nemo_inspector"]).items()
        input_group_layout = html.Div(
            (
                [
                    get_input_group_layout(
                        name,
                        value,
                    )
                    for name, value in sorted(
                        utils,
                        key=lambda item: (
                            "a" + str(item[0])
                            if not isinstance(item[1], str)
                            else "z" + str(item[0])
                        ),
                    )
                    if condition(name, value)
                ]
            ),
            id="utils_group",
        )
        utils_group_layout = [
            dbc.AccordionItem(
                html.Div(
                    [
                        input_group_layout,
                    ]
                ),
                title="Utils",
            )
        ]
        return utils_group_layout

    def get_few_shots_input_layout(self) -> List[dbc.AccordionItem]:
        config = current_app.config["nemo_inspector"]
        size = len(get_examples_map().get(config["examples_type"], []))
        return [
            dbc.AccordionItem(
                self.get_few_shots_div_layout(size),
                title="Few shots",
                id="few_shots_group",
            )
        ]

    def get_query_input_layout(
        self, query_data: Dict[str, str], is_prompt_search: bool = True
    ) -> List[dbc.AccordionItem]:
        switch_layout = [
            get_text_modes_layout(
                QUERY_INPUT_TYPE,
                False,
            )
        ]
        search_layout = [self._get_search_prompt_layout()] if is_prompt_search else []
        query_input = [
            html.Div(
                self.get_query_input_children_layout(query_data),
                id="query_input_children",
            )
        ]
        query_store = [dcc.Store(id={"type": "query_store", "id": 1}, data=query_data)]
        return [
            dbc.AccordionItem(
                html.Div(
                    switch_layout + search_layout + query_input + query_store,
                ),
                title="Input",
                id="query_input_content",
            )
        ]

    def get_query_input_children_layout(
        self, query_data: Dict[str, str], text_modes: List[str] = []
    ) -> List[dbc.InputGroup]:
        return [
            dbc.InputGroup(
                [
                    dbc.InputGroupText(key),
                    get_text_area_layout(
                        id={
                            "type": QUERY_INPUT_TYPE,
                            "id": key,
                        },
                        value=str(value),
                        text_modes=text_modes,
                    ),
                ],
                className="mb-3",
            )
            for key, value in query_data.items()
        ]

    def get_few_shots_div_layout(self, size: int) -> html.Div:
        return html.Div(
            [
                html.Div(
                    [
                        dbc.Pagination(
                            id="few_shots_pagination",
                            max_value=size,
                            active_page=1,
                        ),
                        html.Div(
                            [
                                dbc.Button(
                                    "add example",
                                    id="add_example_button",
                                    outline=True,
                                    size="sm",
                                    color="primary",
                                    className="me-1",
                                ),
                                dbc.Button(
                                    "delete current example",
                                    id="del_example_button",
                                    outline=True,
                                    size="sm",
                                    color="primary",
                                    className="me-1",
                                ),
                            ],
                            style={"display": "block"},
                        ),
                        get_text_modes_layout(FEW_SHOTS_INPUT, False),
                    ]
                ),
                dbc.Container(id="few_shots_pagination_content"),
            ],
            id="few_shots_div",
        )

    def run(self, utils: Dict, params: Dict) -> html.Div:
        utils = {key.split(SEPARATOR_ID)[-1]: value for key, value in utils.items()}
        self.sandbox_init()
        if utils.get("code_execution", False) and str(utils["code_execution"]) == "True":
            llm = get_code_execution_model(
                **current_app.config["nemo_inspector"]["server"],
                sandbox=self.sandbox,
            )
        else:
            llm = get_model(**current_app.config["nemo_inspector"]["server"])

        generate_params = {
            key: value
            for key, value in utils.items()
            if key in inspect.signature(llm.generate).parameters
        }
        logging.info(f"query to process: {params['prompts']}")
        retry_attempts = 5
        for i in range(retry_attempts):
            try:
                outputs = llm.generate(
                    prompts=params["prompts"],
                    stop_phrases=current_app.config["nemo_inspector"]["prompt"].get(
                        "stop_phrases", []
                    ),
                    **generate_params,
                )
                break
            except requests.exceptions.ConnectionError as e:
                if i + 1 == retry_attempts:
                    return self._get_connection_error_message()
            except Exception as e:
                if i + 1 == retry_attempts:
                    logging.error(f"error during run prompt: {e}")
                    logging.error(f"error type: {type(e)}")
                    logging.error(f"Got error: {e}")
                    return html.Div(f"Got error\n{e}")

        logging.info(f"query's answer: {outputs[0]}")

        try:
            predicted_answer = extract_answer(outputs[0]["generation"])
            color, background, is_correct = (
                ("#d4edda", "#d4edda", "correct")
                if predicted_answer == params["expected_answer"]
                or self.sandbox.is_output_correct(
                    predicted_answer, params["expected_answer"]
                )
                else ("#fecccb", "#fecccb", "incorrect")
            )
        except Exception as e:
            color, background, is_correct = "black", "white", "unknown"
        return html.Div(
            [
                get_results_content_layout(
                    outputs[0]["generation"],
                    get_single_prompt_output_layout(
                        outputs[0]["generation"],
                    ),
                    style={"border": f"2px solid {color}"},
                    is_formatted=True,
                ),
                html.Div(
                    (
                        f"Answer {predicted_answer} is {is_correct}"
                        if is_correct != "unknown"
                        else "Could not evaluate the answer"
                    ),
                    style={"background-color": background},
                ),
            ]
        )

    def get_prompt(self, utils: Dict, input_dict: Dict[str, str]) -> str:
        import nemo_skills

        buid_examples_dict = nemo_skills.prompt.utils.Prompt.build_examples_dict
        nemo_skills.prompt.utils.Prompt.build_examples_dict = (
            lambda x, y: get_examples_map().get(utils.get("examples_type"), [])
        )
        utils = {
            key.split(SEPARATOR_ID)[-1]: value
            for key, value in utils.items()
            if key != RETRIEVAL and key not in RETRIEVAL_FIELDS
        }
        prompt_config = initialize_default(PromptConfig, {**utils})
        prompt = Prompt(config=prompt_config)
        if current_app.config["nemo_inspector"]["server"]["server_type"] == "openai":
            prompt.config.template = None
        prompt_text = prompt.fill(input_dict)
        nemo_skills.prompt.utils.Prompt.build_examples_dict = buid_examples_dict
        return prompt_text

    def _get_search_prompt_layout(self) -> dbc.InputGroup:
        return dbc.InputGroup(
            [
                dbc.InputGroupText("Index of test"),
                dbc.Input(
                    value=1,
                    id="query_search_input",
                    type="number",
                    size="sm",
                ),
                dbc.Button(
                    "Search",
                    id="query_search_button",
                    outline=True,
                    size="sm",
                    color="primary",
                    className="me-1",
                ),
            ],
            className="mb-3",
        )

    def _get_connection_error_message(self):
        return html.Div(
            html.P(
                [
                    "Could not connect to the server. Please check that the server is running (look at ",
                    html.A(
                        "inference.md",
                        href="https://github.com/NVIDIA/NeMo-Skills/blob/main/docs/basics/inference.md",
                    ),
                    " for more information). ",
                    "Also check that you have provided correct host, ssh_key_path and ssh_server parameters",
                ]
            )
        )
