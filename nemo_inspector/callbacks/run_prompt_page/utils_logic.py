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
from dataclasses import asdict
from typing import Optional, Tuple, Union

import dash_bootstrap_components as dbc
from dash import no_update
from dash._callback import NoUpdate
from dash.dependencies import Input, Output, State
from flask import current_app

from nemo_inspector.callbacks import app
from nemo_inspector.layouts import (
    get_utils_field_representation,
)
from nemo_inspector.settings.constants import (
    CODE_BEGIN,
    CODE_END,
    CODE_OUTPUT_BEGIN,
    CODE_OUTPUT_END,
    SEPARATOR_DISPLAY,
    SEPARATOR_ID,
)
from nemo_inspector.utils.common import (
    get_utils_from_config,
    initialize_default,
)

from nemo_skills.prompt.utils import PromptConfig, get_prompt, load_config


@app.callback(
    [
        Output(
            SEPARATOR_ID.join(field.split(SEPARATOR_DISPLAY)),
            "value",
            allow_duplicate=True,
        )
        for field in get_utils_from_config(
            {"prompt": asdict(initialize_default(PromptConfig))}
        ).keys()
    ]
    + [
        Output("js_container", "children", allow_duplicate=True),
        Output("js_trigger", "children", allow_duplicate=True),
    ],
    [
        Input("prompt_config", "value"),
        Input("prompt_template", "value"),
    ],
    State("js_trigger", "children"),
    prevent_initial_call=True,
)
def update_prompt_type(
    config_path: Optional[str], prompt_template: str, js_trigger: str
) -> Union[NoUpdate, dbc.AccordionItem]:
    if (
        "used_prompt" in current_app.config["nemo_inspector"]["prompt"]
        and (str(config_path), str(prompt_template))
        == current_app.config["nemo_inspector"]["prompt"]["used_prompt"]
    ):
        output_len = len(
            get_utils_from_config(asdict(initialize_default(PromptConfig))).keys()
        )
        return [no_update] * (output_len + 2)

    current_app.config["nemo_inspector"]["prompt"]["used_prompt"] = (
        str(config_path),
        str(prompt_template),
    )
    if not os.path.isfile(str(config_path)) and not os.path.isfile(str(prompt_template)):
        output_len = len(
            get_utils_from_config(asdict(initialize_default(PromptConfig))).keys()
        )
        return [no_update] * (output_len + 2)
    elif not os.path.isfile(str(config_path)):
        prompt_config = initialize_default(PromptConfig, load_config(prompt_template))
    elif not os.path.isfile(str(prompt_template)):
        prompt_config = initialize_default(
            PromptConfig, asdict(get_prompt(config_path).config)
        )
    else:
        prompt_config = initialize_default(
            PromptConfig, asdict(get_prompt(config_path, prompt_template).config)
        )

    current_app.config["nemo_inspector"]["prompt"][
        "stop_phrases"
    ] = prompt_config.template.stop_phrases

    return [
        get_utils_field_representation(value, key)
        for key, value in get_utils_from_config(asdict(prompt_config)).items()
    ] + ["", js_trigger + " "]


@app.callback(
    Output("dummy_output", "children", allow_duplicate=True),
    [
        Input(CODE_BEGIN, "value"),
        Input(CODE_END, "value"),
        Input(CODE_OUTPUT_BEGIN, "value"),
        Input(CODE_OUTPUT_END, "value"),
    ],
    State(
        "dummy_output",
        "children",
    ),
    prevent_initial_call=True,
)
def update_code_separators(
    code_begin: str,
    code_end: str,
    code_output_begin: str,
    code_output_end: str,
    dummy_data: str,
) -> str:
    current_app.config["nemo_inspector"]["inspector_params"]["code_separators"] = (
        code_begin,
        code_end,
    )
    current_app.config["nemo_inspector"]["inspector_params"]["code_output_separators"] = (
        code_output_begin,
        code_output_end,
    )

    return dummy_data + "1"


@app.callback(
    [
        Output("js_container", "children", allow_duplicate=True),
        Output("js_trigger", "children", allow_duplicate=True),
    ],
    Input("prompt_params_input", "active_item"),
    [
        State("js_container", "children"),
        State("js_trigger", "children"),
    ],
    prevent_initial_call=True,
)
def adjust_params_height(
    active_item: bool, js_container: str, js_trigger: str
) -> Tuple[str, str]:
    return "", js_trigger + " "
