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
from typing import Dict, List, Tuple

from dash import ALL, callback_context, no_update
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate

from nemo_inspector.callbacks import app
from nemo_inspector.layouts import (
    get_detailed_info_table_column,
    get_table_column_header,
    get_detailed_info_table_row_content,
    get_detailed_info_table_content,
)
from nemo_inspector.settings.constants import (
    EDIT_ICON_PATH,
    FILE_NAME,
    MODEL_SELECTOR_ID,
    SAVE_ICON_PATH,
)
from nemo_inspector.utils.common import (
    get_available_models,
    get_compared_rows,
    get_editable_rows,
    get_excluded_row,
    get_filtered_files,
    get_table_data,
)


@app.callback(
    [
        Output("js_container", "children", allow_duplicate=True),
        Output("js_trigger", "children", allow_duplicate=True),
    ],
    Input({"type": "editable_row", "id": ALL, "model_name": ALL}, "value"),
    [
        State({"type": "model_selector", "id": ALL}, "value"),
        State("datatable", "selected_rows"),
        State("datatable", "page_current"),
        State("datatable", "page_size"),
        State({"type": "editable_row", "id": ALL, "model_name": ALL}, "id"),
        State({"type": "file_selector", "id": ALL}, "value"),
        State("js_trigger", "children"),
    ],
    prevent_initial_call=True,
)
def update_data_table(
    new_rows_values: List[str],
    models: List[str],
    idx: List[int],
    current_page: int,
    page_size: int,
    new_rows_ids: List[str],
    file_names: List[str],
    js_trigger: str,
) -> Tuple[str, str]:
    ctx = callback_context
    if not ctx.triggered or not idx:
        return no_update, no_update

    file_ids = {}
    question_id = current_page * page_size + idx[0]
    for model_id, name in enumerate(file_names):
        for file_id, file in enumerate(
            get_table_data()[question_id][models[model_id]]
            if len(get_table_data())
            else []
        ):
            if file[FILE_NAME] == name:
                file_ids[models[model_id]] = file_id

    for new_rows_id, new_rows_value in zip(new_rows_ids, new_rows_values):
        updated_field = new_rows_id["id"]
        updated_model = new_rows_id["model_name"]
        get_table_data()[question_id][updated_model][file_ids[updated_model]][
            updated_field
        ] = new_rows_value

    return "", js_trigger + " "


@app.callback(
    [
        Output(
            {"type": "detailed_models_answers", "id": ALL},
            "children",
            allow_duplicate=True,
        ),
        Output(
            {"type": "filter_function_input", "id": ALL},
            "value",
            allow_duplicate=True,
        ),
        Output(
            {"type": "sorting_function_input", "id": ALL},
            "value",
            allow_duplicate=True,
        ),
    ],
    [
        Input("datatable", "selected_rows"),
        Input(
            "dummy_output",
            "children",
        ),
    ],
    [
        State({"type": "model_selector", "id": ALL}, "value"),
        State({"type": "sorting_function_input", "id": ALL}, "value"),
        State({"type": "filter_function_input", "id": ALL}, "value"),
        State({"type": "row_name", "id": ALL}, "children"),
        State("datatable", "page_current"),
        State("datatable", "page_size"),
        State({"type": "file_selector", "id": ALL}, "value"),
        State({"type": "text_modes", "id": ALL}, "value"),
    ],
    prevent_initial_call=True,
)
def show_item(
    idx: List[int],
    dummmy_trigger: str,
    models: List[str],
    sorting_functions: List[str],
    filter_functions: List[str],
    rows_names: List[str],
    current_page: int,
    page_size: int,
    file_names: List[str],
    text_modes: List[List[str]],
) -> List[str]:
    if not idx:
        raise PreventUpdate
    ctx = callback_context
    if not ctx.triggered:
        return [no_update, no_update, no_update]
    elif ctx.triggered[0]["prop_id"] == "datatable.selected_rows":
        filter_functions = [filter_functions[0]] + [""] * (len(filter_functions) - 1)
        sorting_functions = [sorting_functions[0]] + [None] * (len(sorting_functions) - 1)
    question_id = current_page * page_size + idx[0]
    file_ids = [0] * len(models)
    for model_id, name in enumerate(file_names):
        for file_id, file in enumerate(
            get_table_data()[question_id][models[model_id]]
            if len(get_table_data())
            else []
        ):
            if file[FILE_NAME] == name:
                file_ids[model_id] = file_id
    return [
        get_detailed_info_table_content(
            question_id=question_id,
            rows_names=rows_names,
            models=models,
            files_id=file_ids,
            filter_functions=filter_functions[1:],
            sorting_functions=sorting_functions[1:],
            text_modes=text_modes,
        ),
        [""] * len(filter_functions),
        sorting_functions,
    ]


@app.callback(
    Output(
        "dummy_output",
        "children",
        allow_duplicate=True,
    ),
    Input({"type": "compare_texts_button", "id": ALL}, "n_clicks"),
    [
        State("dummy_output", "children"),
        State({"type": "row_name", "id": ALL}, "children"),
        State({"type": "compare_texts_button", "id": ALL}, "n_clicks"),
    ],
    prevent_initial_call=True,
)
def compare(n_clicks: List[int], dummy_data: str, row_names: str, button_ids: List[str]):
    ctx = callback_context
    if not ctx.triggered or not n_clicks:
        return no_update
    button_id = json.loads(ctx.triggered[0]["prop_id"].split(".")[0])["id"]
    if row_names[button_id] not in get_compared_rows():
        get_compared_rows().add(row_names[button_id])
    else:
        get_compared_rows().remove(row_names[button_id])
    return dummy_data + "1"


@app.callback(
    [
        Output(
            "dummy_output",
            "children",
            allow_duplicate=True,
        ),
        Output({"type": "edit_row_image", "id": ALL}, "src"),
    ],
    Input({"type": "edit_row_button", "id": ALL}, "n_clicks"),
    [
        State({"type": "row_name", "id": ALL}, "children"),
        State({"type": "edit_row_image", "id": ALL}, "id"),
        State({"type": "edit_row_image", "id": ALL}, "src"),
        State({"type": "model_selector", "id": ALL}, "value"),
        State("datatable", "selected_rows"),
        State("datatable", "page_current"),
        State("datatable", "page_size"),
        State({"type": "file_selector", "id": ALL}, "value"),
        State(
            "dummy_output",
            "children",
        ),
    ],
    prevent_initial_call=True,
)
def edit_row(
    n_clicks: List[int],
    rows: List[str],
    button_ids: List[Dict],
    edit_row_labels: List[str],
    models: List[str],
    idx: List[int],
    current_page: int,
    page_size: int,
    file_names: List[str],
    dummy_data: str,
) -> Tuple[str, List[str]]:
    ctx = callback_context
    if not ctx.triggered or not n_clicks or not idx:
        return no_update, [no_update] * len(button_ids)
    button_id = json.loads(ctx.triggered[0]["prop_id"].split(".")[0])["id"]
    row_index = 0
    for i, current_button_id in enumerate(button_ids):
        if current_button_id["id"] == button_id:
            row_index = i
            break
    file_ids = [0] * len(models)
    question_id = current_page * page_size + idx[0]
    for model_id, name in enumerate(file_names):
        for file_id, file in enumerate(
            get_table_data()[question_id][models[model_id]]
            if len(get_table_data())
            else []
        ):
            if file[FILE_NAME] == name:
                file_ids[model_id] = file_id

    if not n_clicks[row_index]:
        return no_update, [no_update] * len(button_ids)

    if rows[row_index] in get_editable_rows():
        edit_row_labels[row_index] = EDIT_ICON_PATH
        get_editable_rows().remove(rows[row_index])
    else:
        get_editable_rows().add(rows[row_index])
        edit_row_labels[row_index] = SAVE_ICON_PATH

    return dummy_data + "1", edit_row_labels


@app.callback(
    [
        Output(
            "dummy_output",
            "children",
            allow_duplicate=True,
        ),
        Output({"type": "del_row", "id": ALL}, "children"),
    ],
    Input({"type": "del_row", "id": ALL}, "n_clicks"),
    [
        State({"type": "row_name", "id": ALL}, "children"),
        State({"type": "del_row", "id": ALL}, "id"),
        State({"type": "del_row", "id": ALL}, "children"),
        State(
            "dummy_output",
            "children",
        ),
    ],
    prevent_initial_call=True,
)
def del_row(
    n_clicks: List[int],
    rows: List[str],
    button_ids: List[Dict],
    del_row_labels: List[str],
    dummy_data: str,
) -> Tuple[str, List[str]]:
    ctx = callback_context
    if not ctx.triggered or not n_clicks:
        return no_update, [no_update] * len(button_ids)
    button_id = json.loads(ctx.triggered[0]["prop_id"].split(".")[0])["id"]
    row_index = 0
    for i, current_button_id in enumerate(button_ids):
        if current_button_id["id"] == button_id:
            row_index = i
            break
    if not n_clicks[row_index]:
        return no_update, [no_update] * len(button_ids)
    if rows[row_index] in get_excluded_row():
        get_excluded_row().remove(rows[row_index])
        del_row_labels[row_index] = "-"
    else:
        get_excluded_row().add(rows[row_index])
        del_row_labels[row_index] = "+"

    return dummy_data + "1", del_row_labels


@app.callback(
    [
        Output(
            "detailed_answers_header",
            "children",
            allow_duplicate=True,
        ),
        Output(
            {"type": "detailed_answers_row", "id": ALL},
            "children",
            allow_duplicate=True,
        ),
    ],
    Input("add_model", "n_clicks"),
    [
        State("detailed_answers_header", "children"),
        State({"type": "detailed_answers_row", "id": ALL}, "children"),
        State({"type": "model_selector", "id": ALL}, "id"),
        State("datatable", "selected_rows"),
    ],
    prevent_initial_call=True,
)
def add_model(
    n_clicks: int,
    header: List,
    rows: List,
    selectors_ids: List[int],
    idx: List[int],
) -> Tuple[List, List]:
    if not n_clicks:
        return no_update, [no_update] * len(rows)
    available_models = list(get_available_models().keys())
    last_header_id = selectors_ids[-1]["id"] if selectors_ids != [] else -1
    header.append(
        get_table_column_header(
            available_models, available_models[0], last_header_id + 1, True
        )
    )
    last_cell_id = rows[-1][-1]["props"]["children"]["props"]["id"]["id"]
    for i, row in enumerate(rows):
        row.append(
            get_detailed_info_table_column(
                last_cell_id + i + 1,
                file_id=last_header_id + 1 if i == 0 and idx else None,
            )
        )

    return header, rows


@app.callback(
    [
        Output("detailed_answers_header", "children"),
        Output({"type": "detailed_answers_row", "id": ALL}, "children"),
    ],
    Input({"type": "del_model", "id": ALL}, "n_clicks"),
    [
        State("detailed_answers_header", "children"),
        State({"type": "detailed_answers_row", "id": ALL}, "children"),
        State({"type": "del_model", "id": ALL}, "id"),
    ],
    prevent_initial_call=True,
)
def del_model(
    n_clicks: List[int],
    header: List,
    rows: List,
    id_del: List[int],
) -> Tuple[List, List]:
    ctx = callback_context
    if not ctx.triggered:
        return no_update, [no_update] * len(rows)

    button_id = json.loads(ctx.triggered[0]["prop_id"].split(".")[0])["id"]

    if not ctx.triggered[0]["value"]:
        return no_update, [no_update] * len(rows)

    for i, id in enumerate(id_del):
        if id["id"] == button_id:
            index = i + 2

    header.pop(index)
    for i, row in enumerate(rows):
        row.pop(index)

    return header, rows


@app.callback(
    [
        Output(
            {"type": "detailed_models_answers", "id": ALL},
            "children",
            allow_duplicate=True,
        ),
        Output(
            "dummy_output",
            "children",
            allow_duplicate=True,
        ),
    ],
    [
        Input({"type": "file_selector", "id": ALL}, "value"),
        Input({"type": "text_modes", "id": ALL}, "value"),
    ],
    [
        State("datatable", "selected_rows"),
        State({"type": "file_selector", "id": ALL}, "options"),
        State({"type": "model_selector", "id": ALL}, "value"),
        State({"type": "model_selector", "id": ALL}, "id"),
        State({"type": "row_name", "id": ALL}, "children"),
        State("datatable", "page_current"),
        State("datatable", "page_size"),
        State(
            {"type": "detailed_models_answers", "id": ALL},
            "children",
        ),
        State("dummy_output", "children"),
    ],
    prevent_initial_call=True,
)
def change_file(
    file_names: List[str],
    text_modes: List[List[str]],
    idx: List[int],
    file_options: List[str],
    models: List[str],
    model_ids: List[int],
    rows_names: List[str],
    current_page: int,
    page_size: int,
    table_data: List[str],
    dummy_data: str,
) -> List[str]:
    if not idx:
        raise PreventUpdate

    ctx = callback_context
    if not ctx.triggered:
        return [no_update] * len(table_data), no_update

    question_id = page_size * current_page + idx[0]
    for trigger in ctx.triggered:
        try:
            button_id = model_ids.index(
                json.loads(
                    MODEL_SELECTOR_ID.format(
                        json.loads(trigger["prop_id"].split(".")[0])["id"]
                    )
                )
            )
        except ValueError:
            continue

        model = models[button_id]

        def get_file_id(name_id: str):
            file_id = 0
            file_name = (
                file_names[name_id]["value"]
                if isinstance(file_names[name_id], Dict)
                else file_names[name_id]
            )
            for i, file_data in enumerate(get_table_data()[question_id][model]):
                if file_data[FILE_NAME] == file_name:
                    file_id = i
                    break
            return file_id

        file_id = get_file_id(button_id)
        base_file_id = get_file_id(0)

        question_id = current_page * page_size + idx[0]
        table_data[button_id * len(rows_names) : (button_id + 1) * len(rows_names)] = (
            get_detailed_info_table_row_content(
                question_id=question_id,
                model=model,
                file_id=file_id,
                rows_names=rows_names,
                files_names=[option["value"] for option in file_options[button_id]],
                col_id=button_id,
                text_modes=text_modes[button_id],
                compare_to=get_table_data()[question_id][models[0]][base_file_id],
            )
        )
    return table_data, dummy_data + "1" if button_id == 0 else dummy_data


@app.callback(
    [
        Output({"type": "file_selector", "id": ALL}, "options"),
        Output({"type": "file_selector", "id": ALL}, "value"),
    ],
    [
        Input({"type": "apply_filter_button", "id": ALL}, "n_clicks"),
        Input({"type": "apply_sorting_button", "id": ALL}, "n_clicks"),
        Input({"type": "model_selector", "id": ALL}, "value"),
    ],
    [
        State({"type": "model_selector", "id": ALL}, "id"),
        State({"type": "sorting_function_input", "id": ALL}, "value"),
        State({"type": "filter_function_input", "id": ALL}, "value"),
        State({"type": "apply_on_filtered_data", "id": ALL}, "value"),
        State("datatable", "page_current"),
        State("datatable", "page_size"),
        State("datatable", "selected_rows"),
        State({"type": "file_selector", "id": ALL}, "options"),
        State({"type": "file_selector", "id": ALL}, "value"),
    ],
    prevent_initial_call=True,
)
def change_files_order(
    filter_n_click: int,
    sorting_n_click: int,
    models: List[str],
    model_ids: List[int],
    sorting_functions: List[str],
    filter_functions: List[str],
    apply_on_filtered_data: List[int],
    current_page: int,
    page_size: int,
    idx: List[int],
    file_selector_options: List[str],
    file_selector_values: List[str],
) -> Tuple[List[List[str]], List[str]]:
    no_updates = [no_update] * len(file_selector_options)
    if not filter_n_click and not sorting_n_click:
        return no_updates, no_updates
    if not idx:
        raise PreventUpdate
    ctx = callback_context
    if not ctx.triggered:
        return no_updates, no_updates
    try:
        button_id = model_ids.index(
            json.loads(
                MODEL_SELECTOR_ID.format(
                    json.loads(ctx.triggered[-1]["prop_id"].split(".")[0])["id"]
                )
            )
        )
    except ValueError:
        return no_updates, no_updates

    if not ctx.triggered[0]["value"] or button_id == -1:
        return no_updates, no_updates
    model = models[button_id]
    question_id = current_page * page_size + idx[0]
    array_to_filter = (
        get_table_data()[question_id][model]
        if not apply_on_filtered_data or not apply_on_filtered_data[button_id]
        else list(
            filter(
                lambda data: data[FILE_NAME]
                in [file_name["label"] for file_name in file_selector_options],
                get_table_data()[question_id][model],
            )
        )
    )
    file_selector_options[button_id] = [
        {"label": data[FILE_NAME], "value": data[FILE_NAME]}
        for data in get_filtered_files(
            filter_functions[button_id + 1],
            sorting_functions[button_id + 1],
            array_to_filter,
        )
    ]
    file_selector_values[button_id] = file_selector_options[button_id][0]

    return file_selector_options, file_selector_values
