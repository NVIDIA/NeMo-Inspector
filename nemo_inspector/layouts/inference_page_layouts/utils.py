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

from typing import Dict, List, Union

import dash_bootstrap_components as dbc
from dash import html
from flask import current_app

from nemo_inspector.layouts.common_layouts import (
    get_selector_layout,
    get_single_prompt_output_layout,
)
from nemo_inspector.settings.constants import SEPARATOR_DISPLAY, SEPARATOR_ID, UNDEFINED


def validation_parameters(name: str, value: Union[str, int, float]) -> Dict[str, str]:
    parameters = {"type": "text"}
    if str(value).replace(".", "", 1).replace("-", "", 1).isdigit():
        parameters["type"] = "number"

    if str(value).isdigit():
        parameters["min"] = 0

    if "." in str(value) and str(value).replace(".", "", 1).isdigit():
        parameters["min"] = 0
        parameters["max"] = 1 if name != "temperature" else 100
        parameters["step"] = 0.1

    return parameters


def get_input_group_layout(
    name: str, value: Union[str, int, float, bool]
) -> dbc.InputGroup:
    input_function = dbc.Textarea
    additional_params = {
        "style": {
            "width": "100%",
        },
        "debounce": True,
    }
    if (
        name.split(SEPARATOR_DISPLAY)[-1]
        in current_app.config["nemo_inspector"]["types"].keys()
    ):
        input_function = get_selector_layout
        additional_params = {
            "options": current_app.config["nemo_inspector"]["types"][
                name.split(SEPARATOR_DISPLAY)[-1]
            ],
        }
        if value is None:
            value = UNDEFINED
    elif isinstance(value, bool):
        input_function = get_selector_layout
        additional_params = {"options": [True, False]}
    elif isinstance(value, (float, int)):
        input_function = dbc.Input
        additional_params = validation_parameters(name, value)
        additional_params["debounce"] = True

    return dbc.InputGroup(
        [
            dbc.InputGroupText(name),
            input_function(
                value=get_utils_field_representation(value),
                id=name.replace(SEPARATOR_DISPLAY, SEPARATOR_ID),
                **additional_params,
            ),
        ],
        className="mb-3",
    )


def get_utils_field_representation(
    value: Union[str, int, float, bool], key: str = ""
) -> str:
    return (
        UNDEFINED
        if value is None
        and key.split(SEPARATOR_ID)[-1] in current_app.config["nemo_inspector"]["types"]
        else value if value == "" or str(value).strip() != "" else repr(value)[1:-1]
    )


def get_text_area_layout(
    id: str, value: str, text_modes: List[str] = []
) -> Union[dbc.Textarea, html.Pre]:
    if text_modes == []:
        component = dbc.Textarea
        children = {"value": value}
    else:
        component = html.Pre
        children = {"children": get_single_prompt_output_layout(value, text_modes)}
    return component(
        **children,
        id=id,
        style={
            "width": "100%",
            "border": "1px solid #dee2e6",
        },
    )
