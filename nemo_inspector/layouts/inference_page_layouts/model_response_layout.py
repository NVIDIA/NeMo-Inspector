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

from typing import Dict

import dash_bootstrap_components as dbc
from dash import dcc, html

from nemo_inspector.layouts.common_layouts import get_text_modes_layout


def get_results_content_layout(
    text: str, content: str = None, style: Dict = {}, is_formatted: bool = False
) -> html.Div:
    return html.Div(
        [
            get_text_modes_layout("results_content", is_formatted),
            html.Pre(
                content if content else text,
                id="results_content_text",
                style={"margin-bottom": "10px"},
            ),
            dcc.Store(data=text, id="text_store"),
        ],
        style=style,
    )
