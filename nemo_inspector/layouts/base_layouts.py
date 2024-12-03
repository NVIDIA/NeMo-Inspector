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

import dash_bootstrap_components as dbc
from dash import dcc, html


def get_main_page_layout() -> html.Div:
    nav_items = [
        dbc.NavItem(
            dbc.NavLink(
                "Inference",
                id="run_mode_link",
                href="/",
                active=True,
            )
        ),
        dbc.NavItem(dbc.NavLink("Analyze", id="analyze_link", href="/analyze")),
    ]
    return html.Div(
        [
            dcc.Location(id="url", refresh=False),
            dbc.NavbarSimple(
                children=nav_items,
                brand="NeMo Inspector",
                sticky="top",
                color="blue",
                dark=True,
                class_name="mb-2",
            ),
            dbc.Container(id="page_content"),
            dbc.Container(id="js_trigger", style={"display": "none"}, children=""),
            dbc.Container(id="js_container"),
            dbc.Container(id="dummy_output", style={"display": "none"}, children=""),
        ]
    )
