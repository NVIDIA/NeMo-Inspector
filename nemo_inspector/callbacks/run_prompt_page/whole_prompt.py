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

from dash import ALL, html, no_update
from dash._callback import NoUpdate
from dash.dependencies import Input, Output, State

from nemo_inspector.callbacks import app
from nemo_inspector.layouts import (
    get_results_content_layout,
    get_single_prompt_output_layout,
)
from nemo_inspector.settings.constants.common import QUERY_INPUT_TYPE
from nemo_inspector.utils.common import (
    extract_query_params,
    get_values_from_input_group,
)
from nemo_inspector.inference_page_strategies.strategy_maker import RunPromptStrategyMaker


@app.callback(
    [
        Output("results_content", "children"),
        Output("loading_container", "children", allow_duplicate=True),
    ],
    Input("run_button", "n_clicks"),
    [
        State("utils_group", "children"),
        State("run_mode_options", "value"),
        State({"type": QUERY_INPUT_TYPE, "id": ALL}, "value"),
        State({"type": QUERY_INPUT_TYPE, "id": ALL}, "id"),
        State({"type": "query_store", "id": ALL}, "data"),
        State("loading_container", "children"),
    ],
    prevent_initial_call=True,
)
def get_run_test_results(
    n_clicks: int,
    utils: List[Dict],
    run_mode: str,
    query_params: List[str],
    query_params_ids: List[Dict],
    query_store: List[Dict[str, str]],
    loading_container: str,
) -> Union[Tuple[html.Div, str], Tuple[NoUpdate, NoUpdate]]:
    if n_clicks is None:
        return no_update, no_update

    utils = get_values_from_input_group(utils)
    if "examples_type" in utils and utils["examples_type"] is None:
        utils["examples_type"] = ""

    if None not in query_params:
        query_store = [extract_query_params(query_params_ids, query_params)]

    return (
        RunPromptStrategyMaker(run_mode)
        .get_strategy()
        .run(
            utils,
            query_store[0],
        ),
        loading_container + " ",
    )


@app.callback(
    Output("results_content", "children", allow_duplicate=True),
    Input("preview_button", "n_clicks"),
    [
        State("run_mode_options", "value"),
        State("utils_group", "children"),
        State({"type": QUERY_INPUT_TYPE, "id": ALL}, "value"),
        State({"type": QUERY_INPUT_TYPE, "id": ALL}, "id"),
        State({"type": "query_store", "id": ALL}, "data"),
    ],
    prevent_initial_call=True,
)
def preview(
    n_clicks: int,
    run_mode: str,
    utils: List[Dict],
    query_params: List[str],
    query_params_ids: List[int],
    query_store: List[Dict[str, str]],
) -> html.Pre:
    if None not in query_params:
        query_store = [extract_query_params(query_params_ids, query_params)]

    utils = get_values_from_input_group(utils)

    prompt = (
        RunPromptStrategyMaker(run_mode).get_strategy().get_prompt(utils, query_store[0])
    )
    return get_results_content_layout(str(prompt))


@app.callback(
    Output("results_content_text", "children", allow_duplicate=True),
    Input(
        {
            "type": "text_modes",
            "id": "results_content",
        },
        "value",
    ),
    State("text_store", "data"),
    prevent_initial_call=True,
)
def change_results_content_mode(text_modes: List[str], text: str) -> html.Pre:
    return (
        get_single_prompt_output_layout(text, text_modes)
        if text_modes and len(text_modes)
        else text
    )
