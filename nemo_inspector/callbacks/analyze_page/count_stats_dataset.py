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

import logging
from typing import List

from dash import no_update
from dash.dependencies import Input, Output, State

from nemo_inspector.callbacks import app
from nemo_inspector.layouts import (
    get_tables_layout,
    get_stats_input,
)
from nemo_inspector.settings.constants import (
    CHOOSE_GENERATION,
    DELETE,
    ERROR_MESSAGE_TEMPLATE,
    GENERAL_STATS,
    INLINE_STATS,
)
from nemo_inspector.utils.common import (
    calculate_metrics_for_whole_data,
    get_custom_stats,
    get_deleted_stats,
    get_general_custom_stats,
    get_stats_raw,
    get_table_data,
)


@app.callback(
    [
        Output("new_stats", "is_open"),
        Output("stats_input_container", "children", allow_duplicate=True),
        Output("js_container", "children", allow_duplicate=True),
        Output("js_trigger", "children", allow_duplicate=True),
    ],
    [
        Input("set_new_stats_button", "n_clicks"),
        Input("apply_new_stats", "n_clicks"),
    ],
    [
        State("new_stats", "is_open"),
        State("stats_modes", "value"),
        State("js_trigger", "children"),
    ],
    prevent_initial_call=True,
)
def toggle_modal_stats(
    n1: int, n2: int, is_open: bool, modes: List[str], js_trigger: str
) -> bool:
    if not n1 and not n2:
        return no_update, no_update, no_update, no_update

    if n1 or n2:
        is_open = not is_open
        return is_open, get_stats_input(modes), "", js_trigger + " "
    return is_open, get_stats_input(modes), "", js_trigger + " "


@app.callback(
    Output("compare_models_rows", "children", allow_duplicate=True),
    Input("apply_new_stats", "n_clicks"),
    [
        State("stats_input", "value"),
        State("base_model_answers_selector", "value"),
        State("stats_modes", "value"),
    ],
    prevent_initial_call=True,
)
def apply_new_stat(
    n_click: int,
    code_raw: str,
    base_model: str,
    stats_modes: List[str],
) -> List:
    if not n_click or code_raw == "":
        return no_update
    code_raw_lines = code_raw.strip().split("\n")
    if not stats_modes or DELETE not in stats_modes:
        code = "\n".join(code_raw_lines[:-1]) + "\nnew_stats = " + code_raw_lines[-1]
    else:
        code = "delete_stats = " + f"'{code_raw_lines[-1]}'"
    namespace = {}
    try:
        exec(code, namespace)
    except Exception as e:
        logging.error(ERROR_MESSAGE_TEMPLATE.format(code, str(e)))
        return no_update
    if stats_modes and GENERAL_STATS in stats_modes:
        if DELETE in stats_modes:
            get_general_custom_stats().pop(namespace["delete_stats"], None)
        else:
            get_general_custom_stats().update(namespace["new_stats"])
            get_stats_raw()[GENERAL_STATS][
                " ".join(namespace["new_stats"].keys())
            ] = code_raw
    else:
        if stats_modes and DELETE in stats_modes:
            get_custom_stats().pop(namespace["delete_stats"], None)
            get_deleted_stats().update(namespace["delete_stats"])
        else:
            get_custom_stats().update(namespace["new_stats"])
            get_stats_raw()[INLINE_STATS][
                " ".join(namespace["new_stats"].keys())
            ] = code_raw
    if base_model == CHOOSE_GENERATION:
        return []
    calculate_metrics_for_whole_data(get_table_data(), base_model)
    return get_tables_layout(base_model=base_model)


@app.callback(
    [
        Output("stats_input", "value", allow_duplicate=True),
        Output("js_container", "children", allow_duplicate=True),
        Output("js_trigger", "children", allow_duplicate=True),
    ],
    Input("stats_extractor", "value"),
    [
        State("stats_modes", "value"),
        State("js_trigger", "children"),
    ],
    prevent_initial_call=True,
)
def apply_new_stat(stat: str, stats_modes: List[str], js_trigger: str) -> List:
    mode = GENERAL_STATS if GENERAL_STATS in stats_modes else INLINE_STATS
    return get_stats_raw()[mode][stat], " ", js_trigger + " "
