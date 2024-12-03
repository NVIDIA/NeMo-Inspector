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
from nemo_inspector.layouts import get_sorted_tables_layout
from nemo_inspector.settings.constants import CHOOSE_GENERATION


@app.callback(
    [
        Output({"type": "sorting", "id": ALL}, "is_open"),
        Output("js_container", "children", allow_duplicate=True),
        Output("js_trigger", "children", allow_duplicate=True),
    ],
    [
        Input({"type": "set_sorting_button", "id": ALL}, "n_clicks"),
        Input({"type": "apply_sorting_button", "id": ALL}, "n_clicks"),
    ],
    [
        State({"type": "sorting", "id": ALL}, "is_open"),
        State("js_trigger", "children"),
    ],
    prevent_initial_call=True,
)
def toggle_modal_sorting(n1: int, n2: int, is_open: bool, js_trigger: str) -> bool:
    ctx = callback_context
    if not ctx.triggered:
        return [no_update] * len(is_open), no_update, no_update

    button_id = json.loads(ctx.triggered[-1]["prop_id"].split(".")[0])["id"] + 1

    if not ctx.triggered[0]["value"]:
        return [no_update] * len(is_open), no_update, no_update

    if n1[button_id] or n2[button_id]:
        is_open[button_id] = not is_open[button_id]
        return is_open, "", js_trigger + " "
    return is_open, "", js_trigger + " "


@app.callback(
    [
        Output("compare_models_rows", "children", allow_duplicate=True),
        Output("sorting_container", "children"),
        Output("loading_container", "children", allow_duplicate=True),
    ],
    Input({"type": "apply_sorting_button", "id": -1}, "n_clicks"),
    [
        State({"type": "sorting_function_input", "id": -1}, "value"),
        State({"type": "model_selector", "id": ALL}, "value"),
        State("base_model_answers_selector", "value"),
        State("loading_container", "children"),
    ],
    prevent_initial_call=True,
)
def sorting_data(
    n_ckicks: int,
    sorting_function: str,
    models: List[str],
    base_model: str,
    loading_container: str,
) -> Tuple[List[html.Tr], bool]:
    if base_model == CHOOSE_GENERATION or not sorting_function:
        return no_update, no_update, no_update
    return (
        get_sorted_tables_layout(
            base_model=base_model,
            sorting_function=sorting_function,
            models=models,
        ),
        html.Pre(f"Sorting function:\n{sorting_function}"),
        loading_container + " ",
    )
