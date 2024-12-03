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

from dash import no_update
from dash.dependencies import Input, Output, State

from nemo_inspector.callbacks import app
from nemo_inspector.layouts import (
    get_tables_layout,
    get_stats_input,
)
from nemo_inspector.settings.constants import CHOOSE_GENERATION
from nemo_inspector.utils.common import get_excluded_row, get_table_data


@app.callback(
    [
        Output("compare_models_rows", "children", allow_duplicate=True),
        Output("loading_container", "children", allow_duplicate=True),
    ],
    Input("base_model_answers_selector", "value"),
    State("loading_container", "children"),
    prevent_initial_call=True,
)
def choose_base_model(
    base_model: str,
    loading_container: str,
) -> Tuple[List, bool]:
    if base_model == CHOOSE_GENERATION:
        return no_update, no_update
    get_excluded_row().clear()
    return (
        get_tables_layout(
            base_model=base_model,
        ),
        loading_container + " ",
    )


@app.callback(
    Output("datatable", "data"),
    [
        Input("datatable", "page_current"),
        Input("datatable", "page_size"),
    ],
    State("base_model_answers_selector", "value"),
)
def change_page(page_current: int, page_size: int, base_model: str) -> List[Dict]:
    if not get_table_data():
        return no_update
    return [
        data[base_model][0]
        for data in get_table_data()[
            page_current * page_size : (page_current + 1) * page_size
        ]
        if base_model in data.keys()
    ]


@app.callback(
    [
        Output("stats_input_container", "children", allow_duplicate=True),
        Output("js_container", "children", allow_duplicate=True),
        Output("js_trigger", "children", allow_duplicate=True),
    ],
    Input("stats_modes", "value"),
    State("js_trigger", "children"),
    prevent_initial_call=True,
)
def change_stats_mode(modes: List[str], js_trigger: str) -> str:
    if modes is None:
        return no_update, no_update, no_update
    return get_stats_input(modes), "", js_trigger + " "
