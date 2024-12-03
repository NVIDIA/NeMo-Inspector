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

from typing import List, Tuple

from dash import ALL, html, no_update
from dash.dependencies import Input, Output, State

from nemo_inspector.callbacks import app
from nemo_inspector.layouts import get_updated_tables_layout
from nemo_inspector.settings.constants import CHOOSE_GENERATION


@app.callback(
    [
        Output("update_dataset_modal", "is_open", allow_duplicate=True),
        Output("js_container", "children", allow_duplicate=True),
        Output("js_trigger", "children", allow_duplicate=True),
    ],
    [
        Input("update_dataset_button", "n_clicks"),
        Input("apply_update_dataset_button", "n_clicks"),
    ],
    [State("update_dataset_modal", "is_open"), State("js_trigger", "children")],
    prevent_initial_call=True,
)
def open_update_dataset_modal(n1: int, n2: int, is_open: bool, js_trigger: str) -> bool:
    if n1 or n2:
        is_open = not is_open
        return is_open, "", js_trigger + " "
    return is_open, "", js_trigger + " "


@app.callback(
    [
        Output("compare_models_rows", "children", allow_duplicate=True),
        Output("loading_container", "children", allow_duplicate=True),
    ],
    Input("apply_update_dataset_button", "n_clicks"),
    [
        State("update_dataset_input", "value"),
        State({"type": "model_selector", "id": ALL}, "value"),
        State("base_model_answers_selector", "value"),
        State("loading_container", "children"),
    ],
    prevent_initial_call=True,
)
def update_dataset(
    n_ckicks: int,
    update_function: str,
    models: List[str],
    base_model: str,
    loading_container: str,
) -> Tuple[List[html.Tr], bool]:
    if base_model == CHOOSE_GENERATION or not update_function:
        return no_update, no_update
    return (
        get_updated_tables_layout(
            base_model=base_model, update_function=update_function, models=models
        ),
        loading_container + " ",
    )
