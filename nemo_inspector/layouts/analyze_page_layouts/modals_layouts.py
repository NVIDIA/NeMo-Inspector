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

import os
from typing import List

import dash_bootstrap_components as dbc
from dash import html
from flask import current_app

from nemo_inspector.layouts.common_layouts import (
    get_selector_layout,
    get_switch_layout,
)
from nemo_inspector.layouts.analyze_page_layouts.utils import (
    get_code_text_area_layout,
    get_filter_text,
    get_stats_input,
)
from nemo_inspector.settings.constants import (
    DELETE,
    FILES_ONLY,
    FILES_FILTERING,
    GENERAL_STATS,
)
from nemo_inspector.settings.constants.configurations import STATS_KEYS
from nemo_inspector.utils.common import get_labels, get_metrics, get_table_data


def get_filter_modal_layout(
    id: int = -1, available_filters: List[str] = [], mode: str = FILES_FILTERING
) -> html.Div:
    text = get_filter_text(available_filters, mode)

    filter_mode = (
        [
            get_switch_layout(
                id={"type": "filter_mode", "id": id},
                labels=["filter files"],
                is_active=True,
                additional_params={
                    "inline": True,
                    "style": {"margin-left": "10px"},
                },
            )
        ]
        if mode != FILES_ONLY
        else []
    )

    header = dbc.ModalHeader(
        (
            [
                dbc.ModalTitle(
                    "Set Up Your Filter",
                ),
            ]
            + filter_mode
        ),
        close_button=True,
    )
    body = dbc.ModalBody(
        html.Div(
            [
                html.Pre(text, id={"type": "filter_text", "id": id}),
                get_code_text_area_layout(
                    id={
                        "type": "filter_function_input",
                        "id": id,
                    },
                ),
            ]
        )
    )
    switch = get_switch_layout(
        {
            "type": "apply_on_filtered_data",
            "id": id,
        },
        ["Apply for filtered data"],
        additional_params={"style": {"margin-left": "10px"}},
    )
    footer = dbc.ModalFooter(
        dbc.Button(
            "Apply",
            id={"type": "apply_filter_button", "id": id},
            className="ms-auto",
            n_clicks=0,
        )
    )
    return html.Div(
        [
            dbc.Button(
                "Filters",
                id={"type": "set_filter_button", "id": id},
                class_name="button-class",
            ),
            dbc.Modal(
                [
                    header,
                    body,
                    switch,
                    footer,
                ],
                size="lg",
                id={"type": "filter", "id": id},
                centered=True,
                is_open=False,
            ),
        ],
        style={"display": "inline-block"},
    )


def get_sorting_modal_layout(id: int = -1, available_params: List[str] = []) -> html.Div:
    available_params = list(
        get_table_data()[0][list(get_table_data()[0].keys())[0]][0].keys()
        if len(get_table_data()) and not available_params
        else STATS_KEYS + list(get_metrics([]).keys()) + ["+ all fields in json"]
    )
    text = (
        "Write an expression to sort the data\n\n"
        "For example: len(data['question'])\n\n"
        "The function has to return sortable type\n\n"
        "Available parameters to sort data:\n"
        + "\n".join(
            [
                ", ".join(available_params[start : start + 5])
                for start in range(0, len(available_params), 5)
            ]
        )
    )
    header = dbc.ModalHeader(
        dbc.ModalTitle("Set Up Your Sorting Parameters"),
        close_button=True,
    )
    body = dbc.ModalBody(
        html.Div(
            [
                html.Pre(text),
                get_code_text_area_layout(
                    id={
                        "type": "sorting_function_input",
                        "id": id,
                    },
                ),
            ],
        )
    )
    footer = dbc.ModalFooter(
        dbc.Button(
            "Apply",
            id={"type": "apply_sorting_button", "id": id},
            className="ms-auto",
            n_clicks=0,
        )
    )
    return html.Div(
        [
            dbc.Button(
                "Sort",
                id={"type": "set_sorting_button", "id": id},
                class_name="button-class",
            ),
            dbc.Modal(
                [
                    header,
                    body,
                    footer,
                ],
                size="lg",
                id={"type": "sorting", "id": id},
                centered=True,
                is_open=False,
            ),
        ],
        style={"display": "inline-block"},
    )


def get_update_dataset_modal_layout() -> html.Div:
    text = (
        "Write an expression to modify the data\n\n"
        "For example: {**data, 'generation': data['generation'].strip()}\n\n"
        "The function has to return a new dict"
    )
    header = dbc.ModalHeader(
        dbc.ModalTitle("Update Dataset"),
        close_button=True,
    )
    body = dbc.ModalBody(
        html.Div(
            [
                html.Pre(text),
                get_code_text_area_layout(
                    id="update_dataset_input",
                ),
            ],
        )
    )
    footer = dbc.ModalFooter(
        dbc.Button(
            "Apply",
            id="apply_update_dataset_button",
            className="ms-auto",
            n_clicks=0,
        )
    )
    return html.Div(
        [
            dbc.Button(
                "Update dataset",
                id="update_dataset_button",
                class_name="button-class",
            ),
            dbc.Modal(
                [
                    header,
                    body,
                    footer,
                ],
                size="lg",
                id="update_dataset_modal",
                centered=True,
                is_open=False,
            ),
        ],
        style={"display": "inline-block"},
    )


def get_change_label_modal_layout(
    id: int = -1, apply_for_all_files: bool = True
) -> html.Div:
    header = dbc.ModalHeader(
        dbc.ModalTitle("Manage labels"),
        close_button=True,
    )
    switch_layout = (
        [
            get_switch_layout(
                {
                    "type": "aplly_for_all_files",
                    "id": id,
                },
                ["Apply for all files"],
                additional_params={"style": {"margin-left": "10px"}},
            )
        ]
        if apply_for_all_files
        else []
    )
    body = dbc.ModalBody(
        html.Div(
            [
                get_selector_layout(
                    options=get_labels(),
                    id={"type": "label_selector", "id": id},
                    value="choose label",
                ),
                dbc.InputGroup(
                    [
                        dbc.Input(
                            id={
                                "type": "new_label_input",
                                "id": id,
                            },
                            placeholder="Enter new label",
                            type="text",
                        ),
                        dbc.Button(
                            "Add",
                            id={
                                "type": "add_new_label_button",
                                "id": id,
                            },
                        ),
                    ]
                ),
                *switch_layout,
                html.Pre("", id={"type": "chosen_label", "id": id}),
            ],
        )
    )
    footer = dbc.ModalFooter(
        html.Div(
            [
                dbc.Button(
                    children="Delete",
                    id={
                        "type": "delete_label_button",
                        "id": id,
                    },
                    className="ms-auto",
                    n_clicks=0,
                ),
                html.Pre(
                    " ",
                    style={"display": "inline-block", "font-size": "5px"},
                ),
                dbc.Button(
                    children="Apply",
                    id={"type": "apply_label_button", "id": id},
                    className="ms-auto",
                    n_clicks=0,
                ),
            ],
        ),
        style={"display": "inline-block"},
    )
    return html.Div(
        [
            dbc.Button(
                "Labels",
                id={"type": "set_file_label_button", "id": id},
                class_name="button-class",
            ),
            dbc.Modal(
                [header, body, footer],
                size="lg",
                id={"type": "label", "id": id},
                centered=True,
                is_open=False,
            ),
        ],
        style={"display": "inline-block"},
    )


def get_save_dataset_modal_layout() -> html.Div:
    return html.Div(
        [
            dbc.Button("Save dataset", id="save_dataset", class_name="button-class"),
            dbc.Modal(
                [
                    dbc.ModalBody(
                        [
                            dbc.InputGroup(
                                [
                                    dbc.InputGroupText("save_path"),
                                    dbc.Input(
                                        value=os.path.join(
                                            current_app.config["nemo_inspector"][
                                                "inspector_params"
                                            ]["save_generations_path"],
                                            "default_name",
                                        ),
                                        id="save_path",
                                        type="text",
                                    ),
                                ],
                                className="mb-3",
                            ),
                            dbc.Container(id="error_message"),
                        ]
                    ),
                    dbc.ModalFooter(
                        dbc.Button(
                            "Save",
                            id="save_dataset_button",
                            className="ms-auto",
                            n_clicks=0,
                        )
                    ),
                ],
                id="save_dataset_modal",
                is_open=False,
                style={
                    "text-align": "center",
                    "margin-top": "10px",
                    "margin-bottom": "10px",
                },
            ),
        ],
    )


def get_add_stats_modal_layout() -> html.Div:
    modal_header = dbc.ModalHeader(
        [
            dbc.ModalTitle("Set Up Your Stats"),
            get_switch_layout(
                id="stats_modes",
                labels=["general stats", "delete mode"],
                values=[GENERAL_STATS, DELETE],
                additional_params={"inline": True, "style": {"margin-left": "10px"}},
            ),
        ],
        close_button=True,
    )
    modal_body = dbc.ModalBody(
        html.Div(
            get_stats_input(),
            id="stats_input_container",
        )
    )
    modal_footer = dbc.ModalFooter(
        dbc.Button(
            "Apply",
            id="apply_new_stats",
            className="ms-auto",
            n_clicks=0,
        )
    )
    return html.Div(
        [
            dbc.Button(
                "Stats",
                id="set_new_stats_button",
                class_name="button-class",
            ),
            dbc.Modal(
                [
                    modal_header,
                    modal_body,
                    modal_footer,
                ],
                size="lg",
                id="new_stats",
                centered=True,
                is_open=False,
            ),
        ],
        style={"display": "inline-block"},
    )
