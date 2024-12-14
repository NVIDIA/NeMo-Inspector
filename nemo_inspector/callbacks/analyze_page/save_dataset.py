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
import os
from typing import List, Tuple

from dash import callback_context, html, no_update
from dash.dependencies import Input, Output, State

from nemo_inspector.callbacks import app
from nemo_inspector.settings.constants import (
    EXTRA_FIELDS,
    FILE_NAME,
)
from nemo_inspector.settings.constants.paths import PATH_TO_THE_REPOSITORY
from nemo_inspector.utils.common import get_table_data


@app.callback(
    Output("save_dataset_modal", "is_open", allow_duplicate=True),
    Input("save_dataset", "n_clicks"),
    prevent_initial_call=True,
)
def open_save_dataset_modal(n1: int) -> bool:
    ctx = callback_context
    if not ctx.triggered:
        return no_update

    return True


@app.callback(
    [
        Output("save_dataset_modal", "is_open", allow_duplicate=True),
        Output("error_message", "children"),
    ],
    Input("save_dataset_button", "n_clicks"),
    [
        State("base_model_answers_selector", "value"),
        State("save_path", "value"),
    ],
    prevent_initial_call=True,
)
def save_dataset(n_click: int, base_model: str, save_path: str) -> Tuple[List, bool]:
    if not n_click or not save_path or not base_model:
        return no_update, no_update
    if save_path.startswith("nemo_inspector"):
        save_path = os.path.join(PATH_TO_THE_REPOSITORY, save_path)
    if not os.path.exists(save_path):
        try:
            os.mkdir(save_path)
        except:
            return True, html.Pre(f"could not save generations by path {save_path}")

    new_data = {}

    for data in get_table_data():
        for file_data in data[base_model]:
            file_name = file_data[FILE_NAME]
            if file_name not in new_data:
                new_data[file_name] = []
            new_data[file_name].append(
                {
                    key: value
                    for key, value in file_data.items()
                    if key not in EXTRA_FIELDS
                }
            )

    for file_name, data in new_data.items():
        with open(os.path.join(save_path, file_name + ".jsonl"), "w") as file:
            file.write("\n".join([json.dumps(line) for line in data]))

    return False, ""
