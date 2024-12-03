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

from typing import Dict, List, Tuple

import dash_bootstrap_components as dbc
from dash import dcc, html
from flask import current_app

from nemo_inspector.layouts.inference_page_layouts.utils import get_text_area_layout
from nemo_inspector.settings.constants import (
    PROMPT_BASED,
    FEW_SHOTS_INPUT,
    TEMPLATES_BASED,
)
from nemo_inspector.inference_page_strategies.strategy_maker import RunPromptStrategyMaker
from nemo_inspector.utils.common import get_examples_map


def get_few_shots_by_id_layout(
    page: int, examples_type: str, num_few_shots: int, text_modes: List[str]
) -> Tuple[html.Div]:
    examples_list = get_examples_map().get(
        examples_type,
        [{}],
    )[:num_few_shots]
    if not page or len(examples_list) < page:
        return html.Div()
    return (
        html.Div(
            [
                dbc.InputGroup(
                    [
                        dbc.InputGroupText(key),
                        get_text_area_layout(
                            {"type": FEW_SHOTS_INPUT, "id": key}, str(value), text_modes
                        ),
                    ],
                    className="mb-3",
                )
                for key, value in (examples_list[page - 1].items())
            ],
        ),
    )


def get_few_shots_layout(examples: List[Dict]) -> dbc.AccordionItem:
    example_layout = lambda example: [
        html.Div(
            [
                dcc.Markdown(f"**{name}**"),
                html.Pre(value),
            ]
        )
        for name, value in example.items()
    ]
    examples_layout = [
        dbc.Accordion(
            dbc.AccordionItem(
                example_layout(example),
                title=f"example {id}",
            ),
            start_collapsed=True,
            always_open=True,
        )
        for id, example in enumerate(examples)
    ]
    return dbc.AccordionItem(html.Div(examples_layout), title="Few shots")


def get_query_params_layout(
    mode: str = TEMPLATES_BASED, dataset: str = None
) -> List[dbc.AccordionItem]:
    strategy = RunPromptStrategyMaker(mode).get_strategy()
    return (
        strategy.get_utils_input_layout()
        + strategy.get_few_shots_input_layout()
        + strategy.get_query_input_layout(dataset)
    )


def get_utils_layout(utils: Dict) -> dbc.AccordionItem:
    input_groups = [
        dbc.InputGroup(
            [
                html.Pre(f"{name}: ", className="mr-2"),
                html.Pre(
                    (
                        value
                        if value == "" or str(value).strip() != ""
                        else repr(value)[1:-1]
                    ),
                    className="mr-2",
                    style={"overflow-x": "scroll"},
                ),
            ],
            className="mb-3",
        )
        for name, value in utils.items()
    ]
    return dbc.AccordionItem(
        html.Div(input_groups),
        title="Utils",
    )


def get_inference_mode_layout() -> html.Div:
    return html.Div(
        [
            dbc.RadioItems(
                id="run_mode_options",
                className="btn-group",
                inputClassName="btn-check",
                labelClassName="btn btn-outline-primary",
                labelCheckedClassName="active",
                options=[
                    {"label": PROMPT_BASED, "value": PROMPT_BASED},
                    {"label": TEMPLATES_BASED, "value": TEMPLATES_BASED},
                ],
                value=TEMPLATES_BASED,
            ),
        ],
        className="radio-group",
    )


def get_inference_layout() -> html.Div:
    return html.Div(
        [
            get_inference_mode_layout(),
            dbc.Accordion(
                get_query_params_layout(
                    dataset=current_app.config["nemo_inspector"]["input_file"]
                ),
                start_collapsed=True,
                always_open=True,
                id="prompt_params_input",
            ),
            dbc.Button(
                "preview",
                id="preview_button",
                outline=True,
                color="primary",
                className="me-1 mb-2",
            ),
            dbc.Button(
                "run",
                id="run_button",
                outline=True,
                color="primary",
                className="me-1 mb-2",
            ),
            dcc.Loading(
                children=dbc.Container(
                    id="loading_container", style={"display": "none"}, children=""
                ),
                type="circle",
                style={"margin-top": "50px"},
            ),
            dbc.Container(id="results_content"),
        ]
    )
