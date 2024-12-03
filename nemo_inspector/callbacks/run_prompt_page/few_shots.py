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

import copy
import json
import os
from typing import Dict, List, Optional, Tuple, Union

from dash import ALL, html, no_update
import dash_bootstrap_components as dbc
from dash._callback import NoUpdate
from dash.dependencies import Input, Output, State
from flask import current_app

from nemo_inspector.callbacks import app
from nemo_inspector.layouts import get_few_shots_by_id_layout
from nemo_inspector.settings.constants import (
    FEW_SHOTS_INPUT,
    RETRIEVAL,
    RETRIEVAL_FIELDS,
    SEPARATOR_ID,
)
from nemo_inspector.settings.constants.common import QUERY_INPUT_TYPE, UNDEFINED
from nemo_inspector.utils.common import (
    extract_query_params,
    get_examples_map,
    get_utils_dict,
    get_values_from_input_group,
    initialize_default,
)
from nemo_inspector.inference_page_strategies.strategy_maker import RunPromptStrategyMaker


@app.callback(
    [
        Output("utils_group", "children", allow_duplicate=True),
        Output("few_shots_div", "children"),
        Output("js_container", "children", allow_duplicate=True),
        Output("js_trigger", "children", allow_duplicate=True),
        Output("dummy_output", "children", allow_duplicate=True),
    ],
    [
        Input("examples_type", "value"),
        Input("input_file", "value"),
        Input({"type": RETRIEVAL, "id": ALL}, "value"),
        Input("dummy_output", "children"),
    ],
    [
        State("js_trigger", "children"),
        State("utils_group", "children"),
        State({"type": QUERY_INPUT_TYPE, "id": ALL}, "value"),
        State({"type": QUERY_INPUT_TYPE, "id": ALL}, "id"),
    ],
    prevent_initial_call=True,
)
def update_examples_type(
    examples_type: str,
    input_file: str,
    retrieval_fields: List,
    dummy_output: str,
    js_trigger: str,
    raw_utils: List[Dict],
    query_params: List[str],
    query_params_ids: List[Dict],
) -> Union[
    Union[NoUpdate, NoUpdate, NoUpdate, NoUpdate, NoUpdate],
    Union[List[Dict], dbc.AccordionItem, str, str, str],
]:
    if examples_type == UNDEFINED:
        return no_update, no_update, no_update, no_update, no_update
    input_file_index = 0
    retrieval_field_index = -1

    for retrieval_index, util in enumerate(raw_utils):
        name = util["props"]["children"][0]["props"]["children"]
        if name == "input_file":
            input_file_index = retrieval_index
        if name == "retrieval_field":
            retrieval_field_index = retrieval_index
        if name == "max_retrieved_chars_field":
            max_retrieved_chars_field_index = retrieval_index

    if examples_type == RETRIEVAL:
        utils = {
            key.split(SEPARATOR_ID)[-1]: value
            for key, value in get_values_from_input_group(raw_utils).items()
        }
        utils.pop("examples_type")
        if (
            "retrieval_file" in utils
            and utils["retrieval_file"]
            and os.path.isfile(utils["retrieval_file"])
            and os.path.isfile(input_file)
        ):
            with open(utils["retrieval_file"], "r") as retrieval_file, open(
                input_file, "r"
            ) as input_file:
                types = current_app.config["nemo_inspector"]["types"]
                sample = {
                    key: value
                    for key, value in json.loads(retrieval_file.readline()).items()
                    if key in json.loads(input_file.readline())
                }
            types["retrieval_field"] = list(
                filter(lambda key: isinstance(sample[key], str), sample.keys())
            )
            types["max_retrieved_chars_field"] = types["retrieval_field"]
            for index, name in [
                (retrieval_field_index, "retrieval_field"),
                (max_retrieved_chars_field_index, "max_retrieved_chars_field"),
            ]:
                if index != -1:
                    retrieval_field = raw_utils[index]["props"]["children"][1]["props"]
                    retrieval_field_value = raw_utils[index]["props"]["children"][1][
                        "props"
                    ]["value"]
                    retrieval_field["options"] = types[name]
                    if retrieval_field_value in types[name]:
                        retrieval_field["value"] = retrieval_field_value
                    else:
                        retrieval_field["value"] = types[name][0]
                    utils[name] = retrieval_field["value"]

        if (
            raw_utils[input_file_index + 1]["props"]["children"][0]["props"]["children"]
            not in RETRIEVAL_FIELDS
        ):
            for retrieval_field in RETRIEVAL_FIELDS:
                raw_utils.insert(
                    input_file_index + 1,
                    get_utils_dict(
                        retrieval_field,
                        current_app.config["nemo_inspector"]["retrieval_fields"][
                            retrieval_field
                        ],
                        {"type": RETRIEVAL, "id": retrieval_field},
                    ),
                )
        try:
            prompt = nemo_skills.prompt.utils.Prompt(
                config=nemo_skills.prompt.utils.PromptConfig(
                    user="",
                    few_shot_examples=initialize_default(
                        nemo_skills.prompt.utils.FewShotExamplesConfig, utils
                    ),
                )
            )
            get_examples_map()[examples_type] = prompt.build_examples_dict(
                extract_query_params(query_params_ids, query_params)
            )
        except (ValueError, KeyError, FileNotFoundError) as e:
            get_examples_map()[examples_type] = []

    else:
        while (
            input_file_index + 1 < len(raw_utils)
            and raw_utils[input_file_index + 1]["props"]["children"][0]["props"][
                "children"
            ]
            in RETRIEVAL_FIELDS
        ):
            raw_utils.pop(input_file_index + 1)

    size = len(get_examples_map().get(examples_type, []))
    return (
        raw_utils,
        RunPromptStrategyMaker().get_strategy().get_few_shots_div_layout(size),
        "",
        js_trigger + " ",
        dummy_output + " ",
    )


@app.callback(
    [
        Output("few_shots_pagination_content", "children"),
        Output("js_container", "children", allow_duplicate=True),
        Output("js_trigger", "children", allow_duplicate=True),
    ],
    [
        Input("few_shots_pagination", "active_page"),
        Input(
            {
                "type": "text_modes",
                "id": FEW_SHOTS_INPUT,
            },
            "value",
        ),
        Input("dummy_output", "children"),
    ],
    [
        State("examples_type", "value"),
        State("js_trigger", "children"),
    ],
    prevent_initial_call=True,
)
def change_examples_page(
    page: int,
    text_modes: List[str],
    dummy_output: str,
    examples_type: str,
    js_trigger: str,
) -> Tuple[Tuple[html.Div], str, str]:
    return (
        get_few_shots_by_id_layout(
            page,
            examples_type,
            len(get_examples_map().get(examples_type, [])),
            text_modes,
        ),
        "",
        js_trigger + "",
    )


@app.callback(
    [
        Output("few_shots_pagination", "max_value", allow_duplicate=True),
        Output("few_shots_pagination", "active_page", allow_duplicate=True),
        Output("examples_type", "value", allow_duplicate=True),
    ],
    Input("add_example_button", "n_clicks"),
    [
        State("examples_type", "value"),
        State("few_shots_pagination", "max_value"),
    ],
    prevent_initial_call=True,
)
def add_example(
    n_clicks: int, examples_type: str, last_page: int
) -> Tuple[int, int, int]:
    if not n_clicks:
        return no_update, no_update, no_update
    if examples_type != UNDEFINED:
        get_examples_map()[UNDEFINED] = copy.deepcopy(
            get_examples_map().get(examples_type, [])
        )
    examples_type = UNDEFINED
    examples_type_keys = (
        list(get_examples_map().keys())[0]
        if not len(get_examples_map()[examples_type])
        else examples_type
    )
    get_examples_map()[examples_type].append(
        {key: "" for key in get_examples_map()[examples_type_keys][0].keys()}
    )
    return (last_page + 1, last_page + 1, examples_type)


@app.callback(
    [
        Output("few_shots_pagination", "max_value", allow_duplicate=True),
        Output("few_shots_pagination", "active_page", allow_duplicate=True),
        Output("few_shots_pagination_content", "children", allow_duplicate=True),
        Output("examples_type", "value", allow_duplicate=True),
    ],
    Input("del_example_button", "n_clicks"),
    [
        State("few_shots_pagination", "active_page"),
        State("examples_type", "value"),
        State("few_shots_pagination", "max_value"),
        State(
            {
                "type": "text_modes",
                "id": FEW_SHOTS_INPUT,
            },
            "value",
        ),
    ],
    prevent_initial_call=True,
)
def del_example(
    n_clicks: int,
    page: int,
    examples_type: str,
    last_page: int,
    text_modes: List[str],
) -> Tuple[
    Union[int, NoUpdate],
    Union[int, NoUpdate],
    Union[Tuple[html.Div], NoUpdate],
]:
    if not n_clicks or last_page == 0:
        return no_update, no_update, no_update, no_update

    if examples_type != UNDEFINED:
        get_examples_map()[UNDEFINED] = copy.deepcopy(
            get_examples_map().get(examples_type, [])
        )
    examples_type = UNDEFINED

    if last_page:
        prev_pagination_page = page if page < last_page else page - 1
        get_examples_map()[examples_type].pop(page - 1)
        return (
            last_page - 1,
            prev_pagination_page,
            get_few_shots_by_id_layout(
                prev_pagination_page, examples_type, last_page - 1, text_modes
            ),
            examples_type,
        )
    return no_update, no_update, no_update, no_update


@app.callback(
    Output("examples_type", "value", allow_duplicate=True),
    Input({"type": FEW_SHOTS_INPUT, "id": ALL}, "value"),
    [
        State({"type": FEW_SHOTS_INPUT, "id": ALL}, "id"),
        State("few_shots_pagination", "active_page"),
        State("examples_type", "value"),
        State(
            {
                "type": "text_modes",
                "id": FEW_SHOTS_INPUT,
            },
            "value",
        ),
    ],
    prevent_initial_call=True,
)
def update_examples(
    page_content: Optional[List[str]],
    page_content_ids: List[int],
    page: int,
    examples_type: str,
    text_modes: List[str],
) -> NoUpdate:
    if (
        text_modes
        and len(text_modes)
        or not page_content
        or set(get_examples_map().get(examples_type, [""])[page - 1].values())
        == set(page_content)
    ):
        return no_update
    if examples_type != UNDEFINED:
        get_examples_map()[UNDEFINED] = copy.deepcopy(
            get_examples_map().get(examples_type, [])
        )
    examples_type = UNDEFINED
    last_page = len(get_examples_map()[examples_type])
    if last_page:
        get_examples_map()[examples_type][page - 1 if page else 0] = {
            key["id"]: value for key, value in zip(page_content_ids, page_content)
        }
    return examples_type
