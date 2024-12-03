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

from typing import Dict, List, Tuple, Union

import dash_bootstrap_components as dbc
from dash import ALL
from dash._callback import NoUpdate
from dash.dependencies import Input, Output, State

from nemo_inspector.callbacks import app
from nemo_inspector.layouts import get_query_params_layout
from nemo_inspector.settings.constants.common import (
    QUERY_INPUT_TYPE,
    UNDEFINED,
)
from nemo_inspector.utils.common import (
    extract_query_params,
    get_dataset_sample,
    get_values_from_input_group,
)
from nemo_inspector.inference_page_strategies.strategy_maker import RunPromptStrategyMaker


@app.callback(
    [
        Output("prompt_params_input", "children", allow_duplicate=True),
        Output("js_container", "children", allow_duplicate=True),
        Output("js_trigger", "children", allow_duplicate=True),
        Output("results_content", "children", allow_duplicate=True),
    ],
    Input("run_mode_options", "value"),
    [
        State("utils_group", "children"),
        State("js_trigger", "children"),
    ],
    prevent_initial_call=True,
)
def change_mode(
    run_mode: str, utils: List[Dict], js_trigger: str
) -> Tuple[List[dbc.AccordionItem], None]:
    utils = get_values_from_input_group(utils)
    return (
        get_query_params_layout(run_mode, utils.get("input_file", UNDEFINED)),
        "",
        js_trigger + " ",
        None,
    )


@app.callback(
    [
        Output("query_input_children", "children", allow_duplicate=True),
        Output({"type": "query_store", "id": ALL}, "data", allow_duplicate=True),
        Output("js_container", "children", allow_duplicate=True),
        Output("js_trigger", "children", allow_duplicate=True),
    ],
    [
        Input("query_search_button", "n_clicks"),
        Input("input_file", "value"),
        Input("run_mode_options", "value"),
    ],
    [
        State("query_search_input", "value"),
        State(
            {
                "type": "text_modes",
                "id": QUERY_INPUT_TYPE,
            },
            "value",
        ),
        State("js_trigger", "children"),
    ],
    prevent_initial_call=True,
)
def prompt_search(
    n_clicks: int,
    input_file: str,
    run_mode: str,
    index: int,
    text_modes: List[str],
    js_trigger: str,
) -> Tuple[Union[List[str], NoUpdate]]:
    query_data = get_dataset_sample(index, input_file)[0]
    return (
        RunPromptStrategyMaker()
        .get_strategy()
        .get_query_input_children_layout(
            query_data,
            text_modes,
        ),
        [query_data],
        "",
        js_trigger + " ",
    )


@app.callback(
    [
        Output("query_input_children", "children", allow_duplicate=True),
        Output({"type": "query_store", "id": ALL}, "data", allow_duplicate=True),
        Output("js_container", "children", allow_duplicate=True),
        Output("js_trigger", "children", allow_duplicate=True),
    ],
    [
        Input(
            {
                "type": "text_modes",
                "id": QUERY_INPUT_TYPE,
            },
            "value",
        ),
    ],
    [
        State({"type": "query_store", "id": ALL}, "data"),
        State({"type": QUERY_INPUT_TYPE, "id": ALL}, "value"),
        State({"type": QUERY_INPUT_TYPE, "id": ALL}, "id"),
        State("js_trigger", "children"),
    ],
    prevent_initial_call=True,
)
def change_prompt_search_mode(
    text_modes: List[str],
    query_store: List[Dict[str, str]],
    query_params: List[str],
    query_params_ids: List[int],
    js_trigger: str,
) -> Tuple[Union[List[str], NoUpdate]]:
    if None not in query_params:
        query_store = [extract_query_params(query_params_ids, query_params)]

    return (
        RunPromptStrategyMaker()
        .get_strategy()
        .get_query_input_children_layout(
            query_store[0],
            text_modes,
        ),
        query_store,
        "",
        js_trigger + " ",
    )
