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

import itertools
from typing import Dict, Iterable, List, Optional, Union

import dash_bootstrap_components as dbc
from dash import html

from nemo_inspector.settings.constants import (
    ANSI,
    CODE,
    COMPARE,
    LATEX,
    MARKDOWN,
)
from nemo_inspector.utils.common import parse_model_answer
from nemo_inspector.utils.decoration import (
    color_text_diff,
    design_text_output,
    highlight_code,
)


def get_switch_layout(
    id: Union[Dict, str],
    labels: List[str],
    values: Optional[List[str]] = None,
    disabled: List[bool] = [False],
    is_active: bool = False,
    chosen_values: Optional[List[str]] = None,
    additional_params: Dict = {},
) -> dbc.Checklist:
    if values is None:
        values = labels
    return dbc.Checklist(
        id=id,
        options=[
            {
                "label": label,
                "value": value,
                "disabled": is_disabled,
            }
            for label, value, is_disabled in itertools.zip_longest(
                labels, values, disabled, fillvalue=False
            )
        ],
        value=(chosen_values if chosen_values else [values[0]] if is_active else []),
        **additional_params,
    )


def get_selector_layout(options: Iterable, id: str, value: str = "") -> dbc.Select:
    if value not in options:
        options = [value] + list(options)
    return dbc.Select(
        id=id,
        options=[
            {
                "label": str(value),
                "value": value,
            }
            for value in options
        ],
        value=str(value),
    )


def get_single_prompt_output_layout(
    answer: str, text_modes: List[str] = [CODE, LATEX, ANSI], compare_to: str = ""
) -> List[html.Div]:
    parsed_answers = (
        parse_model_answer(answer)
        if CODE in text_modes
        else [{"explanation": answer, "code": None, "output": None}]
    )
    parsed_compared_answers = (
        (
            parse_model_answer(compare_to)
            if CODE in text_modes
            else [{"explanation": compare_to, "code": None, "output": None}]
        )
        if COMPARE in text_modes
        else parsed_answers
    )

    items = []
    styles = {
        "explanation": {"default": {}, "wrong": {}},
        "code": {"default": {}, "wrong": {}},
        "output": {
            "default": {
                "border": "1px solid black",
                "background-color": "#cdd4f1c8",
                "marginBottom": "10px",
                "marginTop": "-6px",
            },
            "wrong": {
                "border": "1px solid red",
                "marginBottom": "10px",
                "marginTop": "-6px",
            },
        },
    }

    functions = {
        "explanation": design_text_output,
        "code": highlight_code,
        "output": design_text_output,
    }

    def check_existence(array: List[Dict[str, str]], i: int, key: str):
        return i < len(array) and key in array[i] and array[i][key]

    for i in range(max(len(parsed_answers), len(parsed_compared_answers))):
        for key in ["explanation", "code", "output"]:
            if check_existence(parsed_answers, i, key) or check_existence(
                parsed_compared_answers, i, key
            ):
                diff = color_text_diff(
                    (
                        parsed_answers[i][key]
                        if check_existence(parsed_answers, i, key)
                        else ""
                    ),
                    (
                        parsed_compared_answers[i][key]
                        if check_existence(parsed_compared_answers, i, key)
                        else ""
                    ),
                )
                style_type = (
                    "default"
                    if not check_existence(parsed_answers, i, key)
                    or "wrong_code_block" not in parsed_answers[i][key]
                    else "wrong"
                )
                style = styles[key][style_type]
                item = functions[key](diff, style=style, text_modes=text_modes)
                items.append(item)
    return items


def get_text_modes_layout(id: str, is_formatted: bool = True):
    return get_switch_layout(
        id={
            "type": "text_modes",
            "id": id,
        },
        labels=[CODE, LATEX, MARKDOWN, ANSI],
        chosen_values=[CODE, LATEX, ANSI] if is_formatted else [],
        additional_params={
            "style": {
                "display": "inline-flex",
                "flex-wrap": "wrap",
            },
            "inputStyle": {"margin-left": "-10px"},
            "labelStyle": {"margin-left": "3px"},
        },
    )
