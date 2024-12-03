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

import json
from typing import List, Tuple

from dash import ALL, callback_context, html, no_update
from dash.dependencies import Input, Output, State

from nemo_inspector.callbacks import app
from nemo_inspector.layouts import (
    get_filtered_tables_layout,
    get_filter_text,
    get_sorted_tables_layout,
)
from nemo_inspector.settings.constants import (
    CHOOSE_GENERATION,
    FILES_FILTERING,
    QUESTIONS_FILTERING,
)
from nemo_inspector.utils.common import get_table_data


@app.callback(
    [
        Output({"type": "filter", "id": ALL}, "is_open"),
        Output("js_container", "children", allow_duplicate=True),
        Output("js_trigger", "children", allow_duplicate=True),
    ],
    [
        Input({"type": "set_filter_button", "id": ALL}, "n_clicks"),
        Input({"type": "apply_filter_button", "id": ALL}, "n_clicks"),
    ],
    [
        State({"type": "filter", "id": ALL}, "is_open"),
        State("js_trigger", "children"),
    ],
    prevent_initial_call=True,
)
def toggle_modal_filter(n1: int, n2: int, is_open: bool, js_trigger: str) -> bool:
    ctx = callback_context
    if not ctx.triggered:
        return [no_update] * len(is_open), no_update, no_update
    button_id = json.loads(ctx.triggered[-1]["prop_id"].split(".")[0])["id"] + 1
    if not ctx.triggered[0]["value"]:
        return [no_update] * len(is_open), "", js_trigger + " "

    if n1[button_id] or n2[button_id]:
        is_open[button_id] = not is_open[button_id]
        return is_open, "", js_trigger + " "
    return is_open, "", js_trigger + " "


@app.callback(
    [
        Output("compare_models_rows", "children", allow_duplicate=True),
        Output("filtering_container", "children"),
        Output("loading_container", "children", allow_duplicate=True),
    ],
    [
        Input({"type": "apply_filter_button", "id": -1}, "n_clicks"),
    ],
    [
        State({"type": "filter_function_input", "id": -1}, "value"),
        State({"type": "apply_on_filtered_data", "id": -1}, "value"),
        State({"type": "filter_mode", "id": -1}, "value"),
        State({"type": "sorting_function_input", "id": -1}, "value"),
        State({"type": "model_selector", "id": ALL}, "value"),
        State("base_model_answers_selector", "value"),
        State("filtering_container", "children"),
        State("loading_container", "children"),
    ],
    prevent_initial_call=True,
)
def filter_data(
    n_ckicks: int,
    filter_function: str,
    apply_on_filtered_data: int,
    filter_mode: List[str],
    sorting_function: str,
    models: List[str],
    base_model: str,
    filtering_functions: str,
    loading_container: str,
) -> Tuple[List[html.Tr], bool]:
    if not n_ckicks:
        return no_update, no_update, no_update
    if apply_on_filtered_data and filtering_functions:
        filtering_functions["props"]["children"] += f"\n{filter_function}"
    if base_model == CHOOSE_GENERATION:
        return [], no_update, no_update
    if len(get_table_data()) == 0:  # TODO fix
        models = [models[0]]
    get_filtered_tables_layout(
        base_model=base_model,
        filtering_function=filter_function,
        filter_mode=(
            FILES_FILTERING if filter_mode and len(filter_mode) else QUESTIONS_FILTERING
        ),
        apply_on_filtered_data=(apply_on_filtered_data if apply_on_filtered_data else 0),
        models=models,
    )
    return (
        get_sorted_tables_layout(
            base_model=base_model,
            sorting_function=sorting_function,
            models=models,
        ),
        (
            html.Pre(f"Filtering function:\n{filter_function}")
            if not apply_on_filtered_data or not filtering_functions
            else filtering_functions
        ),
        loading_container + " ",
    )


@app.callback(
    [
        Output(
            {"type": "filter_text", "id": -1},
            "children",
            allow_duplicate=True,
        ),
        Output("js_container", "children", allow_duplicate=True),
        Output("js_trigger", "children", allow_duplicate=True),
    ],
    Input({"type": "filter_mode", "id": -1}, "value"),
    State("js_trigger", "children"),
    prevent_initial_call=True,
)
def change_filter_mode(modes: List[str], js_trigger: str) -> str:
    if modes is None:
        return no_update, no_update, no_update
    mode = FILES_FILTERING if modes and len(modes) else QUESTIONS_FILTERING
    text = get_filter_text(mode=mode)
    return (
        text,
        "",
        js_trigger + " ",
    )
