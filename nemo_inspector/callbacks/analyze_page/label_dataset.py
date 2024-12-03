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

from dash import ALL, callback_context, no_update
from dash.dependencies import Input, Output, State

from nemo_inspector.callbacks import app
from nemo_inspector.settings.constants import (
    CHOOSE_LABEL,
    FILE_NAME,
    LABEL,
    LABEL_SELECTOR_ID,
)
from nemo_inspector.utils.common import (
    get_labels,
    get_table_data,
)


@app.callback(
    Output({"type": "label", "id": ALL}, "is_open"),
    [
        Input({"type": "set_file_label_button", "id": ALL}, "n_clicks"),
        Input({"type": "apply_label_button", "id": ALL}, "n_clicks"),
        Input({"type": "delete_label_button", "id": ALL}, "n_clicks"),
    ],
    [State({"type": "label", "id": ALL}, "is_open")],
)
def toggle_modal_label(n1: int, n2: int, n3: int, is_open: bool) -> bool:
    ctx = callback_context
    if not ctx.triggered:
        return [no_update] * len(is_open)

    button_id = json.loads(ctx.triggered[-1]["prop_id"].split(".")[0])["id"] + 1
    if not ctx.triggered[0]["value"]:
        return [no_update] * len(is_open)

    if n1[button_id] or n2[button_id] or n3[button_id]:
        is_open[button_id] = not is_open[button_id]
        return is_open
    return is_open


@app.callback(
    Output(
        "dummy_output",
        "children",
        allow_duplicate=True,
    ),
    [
        Input({"type": "apply_label_button", "id": ALL}, "n_clicks"),
        Input({"type": "delete_label_button", "id": ALL}, "n_clicks"),
    ],
    [
        State(
            {"type": "aplly_for_all_files", "id": ALL},
            "value",
        ),
        State({"type": "label_selector", "id": ALL}, "value"),
        State({"type": "label_selector", "id": ALL}, "id"),
        State("datatable", "page_current"),
        State("datatable", "page_size"),
        State("datatable", "selected_rows"),
        State({"type": "model_selector", "id": ALL}, "value"),
        State("base_model_answers_selector", "value"),
        State({"type": "file_selector", "id": ALL}, "value"),
        State({"type": "file_selector", "id": ALL}, "options"),
        State(
            "dummy_output",
            "children",
        ),
    ],
    prevent_initial_call=True,
)
def change_label(
    n_click_apply: List[int],
    n_click_del: List[int],
    apply_for_all: List[bool],
    labels: List[str],
    label_ids: List[int],
    current_page: int,
    page_size: int,
    idx: List[int],
    models: List[str],
    base_model: str,
    file_names: List[str],
    file_options: List[str],
    dummy_data: str,
) -> List[List[str]]:
    ctx = callback_context
    if not ctx.triggered:
        return no_update

    button_id = label_ids.index(
        json.loads(
            LABEL_SELECTOR_ID.format(
                json.loads(ctx.triggered[-1]["prop_id"].split(".")[0])["id"]
            )
        )
    )
    is_apply = (
        json.loads(ctx.triggered[-1]["prop_id"].split(".")[0])["type"]
        == "apply_label_button"
    )
    if not ctx.triggered[0]["value"] or labels[button_id] == CHOOSE_LABEL:
        return no_update

    ALL_FILES = "ALL_FILES"
    if button_id == 0:
        files = [ALL_FILES]
        file = [ALL_FILES]
        models_to_process = [(base_model, files, file)]
        apply_for_all = [[True] * len(models)]
        question_ids = list(range(len(get_table_data())))
    else:
        if not idx:
            return no_update
        models_to_process = [
            (
                models[button_id - 1],
                file_options[button_id - 1],
                file_names[button_id - 1],
            )
        ]
        question_ids = [current_page * page_size + idx[0]]

    apply_for_all_files = bool(len(apply_for_all[button_id - 1]))
    for question_id in question_ids:
        for model, current_file_options, current_file in models_to_process:
            options = (
                current_file_options
                if button_id != 0
                else [
                    {"value": file[FILE_NAME]}
                    for file in get_table_data()[question_id][model]
                ]
            )
            for file in options:
                if not apply_for_all_files and not file["value"] == current_file:
                    continue

                file_id = 0
                for i, model_file in enumerate(get_table_data()[question_id][model]):
                    if model_file[FILE_NAME] == file["value"]:
                        file_id = i
                        break

                if (
                    labels[button_id]
                    not in get_table_data()[question_id][model][file_id][LABEL]
                ):
                    if is_apply:
                        get_table_data()[question_id][model][file_id][LABEL].append(
                            labels[button_id]
                        )

                elif not is_apply:
                    get_table_data()[question_id][model][file_id][LABEL].remove(
                        labels[button_id]
                    )

    return dummy_data + "1"


@app.callback(
    [
        Output({"type": "new_label_input", "id": ALL}, "value"),
        Output({"type": "label_selector", "id": ALL}, "options"),
        Output({"type": "label_selector", "id": ALL}, "value"),
    ],
    Input({"type": "add_new_label_button", "id": ALL}, "n_clicks"),
    [
        State({"type": "new_label_input", "id": ALL}, "value"),
        State({"type": "label_selector", "id": ALL}, "options"),
        State({"type": "label_selector", "id": ALL}, "value"),
        State({"type": "label_selector", "id": ALL}, "id"),
    ],
)
def add_new_label(
    n_click: int,
    new_labels: List[str],
    options: List[List[str]],
    values: List[str],
    label_ids: List[int],
) -> Tuple[List[List[str]], List[str]]:
    ctx = callback_context
    no_updates = [no_update] * len(new_labels)
    if not ctx.triggered:
        return no_updates, no_updates, no_updates

    button_id = label_ids.index(
        json.loads(
            LABEL_SELECTOR_ID.format(
                json.loads(ctx.triggered[-1]["prop_id"].split(".")[0])["id"]
            )
        )
    )

    if not ctx.triggered[0]["value"]:
        return no_updates, no_updates, no_updates

    if new_labels[button_id] and new_labels[button_id] not in options[button_id]:
        for i in range(len(options)):
            new_label = {"label": new_labels[button_id], "value": new_labels[button_id]}
            if new_label not in options[i]:
                options[i].append(
                    {"label": new_labels[button_id], "value": new_labels[button_id]}
                )
        values[button_id] = new_labels[button_id]
    else:
        return no_updates, no_updates, no_updates

    get_labels().append(new_labels[button_id])
    new_labels[button_id] = ""

    return new_labels, options, values


@app.callback(
    Output({"type": "chosen_label", "id": ALL}, "children"),
    Input({"type": "label_selector", "id": ALL}, "value"),
    [
        State({"type": "label_selector", "id": ALL}, "id"),
        State({"type": "chosen_label", "id": ALL}, "children"),
    ],
)
def choose_label(
    label: List[str], label_ids: List[int], chosen_labels: List[str]
) -> Tuple[List[List[str]], List[str]]:
    ctx = callback_context
    if not ctx.triggered:
        return [no_update] * len(chosen_labels)

    for trigger in ctx.triggered:
        button_id = label_ids.index(
            json.loads(
                LABEL_SELECTOR_ID.format(
                    json.loads(trigger["prop_id"].split(".")[0])["id"]
                )
            )
        )

        if not ctx.triggered[0]["value"] or label[button_id] == CHOOSE_LABEL:
            chosen_labels[button_id] = ""
        else:
            chosen_labels[button_id] = f"chosen label: {label[button_id]}"

    return chosen_labels
