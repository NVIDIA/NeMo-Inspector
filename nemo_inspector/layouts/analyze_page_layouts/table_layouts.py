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
import logging
import math
from typing import Dict, List


import dash_bootstrap_components as dbc
from dash import dash_table, html

from nemo_inspector.layouts.analyze_page_layouts.modals_layouts import (
    get_change_label_modal_layout,
    get_filter_modal_layout,
    get_sorting_modal_layout,
)
from nemo_inspector.layouts.common_layouts import (
    get_selector_layout,
    get_single_prompt_output_layout,
    get_text_modes_layout,
)
from nemo_inspector.settings.constants import (
    ANSI,
    CODE,
    COMPARE,
    COMPARE_ICON_PATH,
    DATA_PAGE_SIZE,
    EDIT_ICON_PATH,
    ERROR_MESSAGE_TEMPLATE,
    FILE_NAME,
    FILES_ONLY,
    LABEL,
    LATEX,
    MODEL_SELECTOR_ID,
    STATS_KEYS,
)
from nemo_inspector.utils.common import (
    catch_eval_exception,
    get_available_models,
    get_compared_rows,
    get_editable_rows,
    get_excluded_row,
    get_filtered_files,
    get_general_custom_stats,
    get_metrics,
    get_table_data,
    is_detailed_answers_rows_key,
)


def get_short_info_table_layout() -> List[dbc.Row]:
    return [
        dbc.Row(
            dbc.Col(
                dash_table.DataTable(
                    id="datatable",
                    columns=[
                        {
                            "name": name,
                            "id": name,
                            "hideable": True,
                        }
                        for name in STATS_KEYS + list(get_metrics([]).keys())
                    ],
                    row_selectable="single",
                    cell_selectable=False,
                    page_action="custom",
                    page_current=0,
                    page_size=DATA_PAGE_SIZE,
                    page_count=math.ceil(len(get_table_data()) / DATA_PAGE_SIZE),
                    style_cell={
                        "overflow": "hidden",
                        "textOverflow": "ellipsis",
                        "maxWidth": 0,
                        "textAlign": "center",
                    },
                    style_header={
                        "color": "text-primary",
                        "text_align": "center",
                        "height": "auto",
                        "whiteSpace": "normal",
                    },
                    css=[
                        {
                            "selector": ".dash-spreadsheet-menu",
                            "rule": "position:absolute; bottom: 8px",
                        },
                        {
                            "selector": ".dash-filter--case",
                            "rule": "display: none",
                        },
                        {
                            "selector": ".column-header--hide",
                            "rule": "display: none",
                        },
                    ],
                ),
            )
        ),
    ]


def get_table_column_header(
    models: List[str], name: str, id: int, add_del_button: bool = False
) -> dbc.Col:
    del_model_layout = (
        [
            dbc.Button(
                "-",
                id={"type": "del_model", "id": id},
                outline=True,
                color="primary",
                className="me-1",
                style={"height": "40px"},
            ),
        ]
        if add_del_button
        else []
    )
    return dbc.Col(
        html.Div(
            [
                html.Div(
                    get_selector_layout(
                        models,
                        json.loads(MODEL_SELECTOR_ID.format(id)),
                        name,
                    ),
                ),
                get_sorting_modal_layout(id),
                get_filter_modal_layout(id, mode=FILES_ONLY),
                get_change_label_modal_layout(id),
            ]
            + del_model_layout
            + [get_text_modes_layout(id)],
            style={"display": "inline-flex"},
        ),
        class_name="mt-1 bg-light font-monospace text-break small rounded border",
        id={"type": "column_header", "id": id},
    )


def get_table_header(models: List[str]) -> List[dbc.Row]:
    return [
        dbc.Row(
            [
                dbc.Col(
                    html.Div(
                        "",
                    ),
                    width=2,
                    class_name="mt-1 bg-light font-monospace text-break small rounded border",
                    id="first_column",
                )
            ]
            + [
                get_table_column_header(get_available_models(), name, i, i != 0)
                for i, name in enumerate(models)
            ],
            id="detailed_answers_header",
        )
    ]


def get_detailed_info_table_column(id: int, file_id=None) -> dbc.Col:
    return dbc.Col(
        html.Div(
            children=(
                get_selector_layout([], {"type": "file_selector", "id": file_id}, "")
                if file_id is not None
                else ""
            ),
            id={
                "type": "detailed_models_answers",
                "id": id,
            },
        ),
        class_name="mt-1 bg-light font-monospace text-break small rounded border",
    )


def get_detailed_info_table_rows(keys: List[str], colums_number: int) -> List[dbc.Row]:
    return [
        dbc.Row(
            [
                dbc.Col(
                    html.Div(
                        html.Div(
                            [
                                html.Div(
                                    key,
                                    id={"type": "row_name", "id": i},
                                    style={"display": "inline-block"},
                                ),
                                dbc.Button(
                                    html.Img(
                                        src=EDIT_ICON_PATH,
                                        id={"type": "edit_row_image", "id": i},
                                        style={
                                            "height": "15px",
                                            "display": "inline-block",
                                        },
                                    ),
                                    id={"type": "edit_row_button", "id": i},
                                    outline=True,
                                    color="primary",
                                    className="me-1",
                                    style={
                                        "border": "none",
                                        "line-height": "1.2",
                                        "display": "inline-block",
                                        "margin-left": "1px",
                                        "display": (
                                            "none"
                                            if key in (FILE_NAME, LABEL)
                                            else "inline-block"
                                        ),
                                    },
                                ),
                                dbc.Button(
                                    html.Img(
                                        src=COMPARE_ICON_PATH,
                                        id={"type": "compare_texts", "id": i},
                                        style={
                                            "height": "15px",
                                            "display": "inline-block",
                                        },
                                    ),
                                    id={"type": "compare_texts_button", "id": i},
                                    outline=True,
                                    color="primary",
                                    className="me-1",
                                    style={
                                        "border": "none",
                                        "line-height": "1.2",
                                        "display": "inline-block",
                                        "margin-left": "-10px" if key != LABEL else "1px",
                                        "display": (
                                            "none" if key == FILE_NAME else "inline-block"
                                        ),
                                    },
                                ),
                                dbc.Button(
                                    "-",
                                    id={"type": "del_row", "id": i},
                                    outline=True,
                                    color="primary",
                                    className="me-1",
                                    style={
                                        "border": "none",
                                        "display": "inline-block",
                                        "margin-left": (
                                            "-9px" if key != FILE_NAME else "1px"
                                        ),
                                    },
                                ),
                            ],
                            style={"display": "inline-block"},
                        ),
                    ),
                    width=2,
                    class_name="mt-1 bg-light font-monospace text-break small rounded border",
                )
            ]
            + [
                get_detailed_info_table_column(j * len(keys) + i)
                for j in range(colums_number)
            ],
            id={"type": "detailed_answers_row", "id": i},
        )
        for i, key in enumerate(keys)
    ]


def get_detailed_info_table_layout(
    models: List[str],
    keys: List[str],
) -> List[dbc.Row]:
    return get_table_header(models) + get_detailed_info_table_rows(keys, len(models))


def get_detailed_info_table_row_content(
    question_id: int,
    model: str,
    rows_names: List[str],
    files_names: List[str],
    file_id: int,
    col_id: int,
    compare_to: Dict = {},
    text_modes: List[str] = [CODE, LATEX, ANSI],
) -> List:
    table_data = get_table_data()[question_id].get(model, [])
    row_data = []
    empty_list = False
    if table_data[file_id].get(FILE_NAME, None) not in files_names:
        empty_list = True
    for key in filter(
        lambda key: is_detailed_answers_rows_key(key),
        rows_names,
    ):
        if file_id < 0 or len(table_data) <= file_id or key in get_excluded_row():
            value = ""
        elif key == FILE_NAME:
            value = get_selector_layout(
                files_names,
                {"type": "file_selector", "id": col_id},
                (table_data[file_id].get(key, None) if not empty_list else ""),
            )
        elif empty_list:
            value = ""
        elif key in get_editable_rows():
            value = str(table_data[file_id].get(key, None))
        else:
            value = get_single_prompt_output_layout(
                str(table_data[file_id].get(key, None)),
                text_modes + ([COMPARE] if key in get_compared_rows() else []),
                str(compare_to.get(key, "")),
            )
        row_data.append(
            value
            if key not in get_editable_rows()
            else dbc.Textarea(
                id={"type": "editable_row", "id": key, "model_name": model}, value=value
            )
        )
    return row_data


def get_detailed_info_table_content(
    question_id: int,
    rows_names: List[str],
    models: List[str],
    files_id: List[int],
    filter_functions: List[str],
    sorting_functions: List[str],
    text_modes: List[List[str]],
) -> List:
    table_data = []
    for col_id, (model, file_id, filter_function, sorting_function, modes) in enumerate(
        zip(models, files_id, filter_functions, sorting_functions, text_modes)
    ):
        row_data = get_detailed_info_table_row_content(
            question_id=question_id,
            model=model,
            rows_names=rows_names,
            files_names=[
                file[FILE_NAME]
                for file in get_filtered_files(
                    filter_function,
                    sorting_function,
                    get_table_data()[question_id][model] if len(get_table_data()) else [],
                )
            ],
            file_id=file_id,
            col_id=col_id,
            text_modes=modes,
            compare_to=get_table_data()[question_id][models[0]][files_id[0]],
        )
        table_data.extend(row_data)
    return table_data


def get_general_stats_layout(
    base_model: str,
) -> html.Div:
    data_for_base_model = [data.get(base_model, []) for data in get_table_data()]
    custom_stats = {}
    for name, func in get_general_custom_stats().items():
        errors_dict = {}
        custom_stats[name] = catch_eval_exception(
            [],
            func,
            data_for_base_model,
            "Got error when applying function",
            errors_dict,
        )
        if len(errors_dict):
            logging.error(ERROR_MESSAGE_TEMPLATE.format(name, errors_dict))

    overall_samples = sum(len(question_data) for question_data in data_for_base_model)
    dataset_size = len(list(filter(lambda x: bool(x), data_for_base_model)))
    stats = {
        "dataset size": dataset_size,
        "overall number of samples": overall_samples,
        "generations per sample": (overall_samples / dataset_size if dataset_size else 0),
        **custom_stats,
    }
    return [html.Div([html.Pre(f"{name}: {value}") for name, value in stats.items()])]
