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

import random
import re
import string
from typing import Dict, List, Union

from ansi2html import Ansi2HTMLConverter
from dash import dcc, html
from nemo_inspector.settings.constants import ANSI, COMPARE, LATEX, MARKDOWN
from nemo_inspector.utils.decoration.latex import preprocess_latex


def design_text_output(
    texts: List[Union[str, str]], style={}, text_modes: List[str] = [LATEX, ANSI]
) -> html.Div:
    conv = Ansi2HTMLConverter()
    ansi_escape = re.compile(r"\x1b\[[0-9;]*m")
    full_text = "".join(map(lambda x: x[0], texts))
    if ANSI in text_modes:
        if (
            bool(ansi_escape.search(full_text))
            or "ipython-input" in full_text
            or "Traceback" in full_text
        ):
            if bool(ansi_escape.search(full_text)):
                full_text = conv.convert(full_text, full=False)
            else:
                full_text = conv.convert(full_text.replace("[", "\u001b["), full=False)
            return html.Div(
                iframe_template(
                    '<link rel="stylesheet" type="text/css" href="/assets/ansi_styles.css" href="/assets/compare_styles.css">',
                    f"<pre>{full_text}</pre>",
                ),
                style=style,
            )
    return html.Div(
        (
            dcc.Markdown(
                preprocess_latex(full_text, escape=MARKDOWN not in text_modes),
                mathjax=True,
                dangerously_allow_html=True,
            )
            if LATEX in text_modes and COMPARE not in text_modes
            else (
                dcc.Markdown(full_text)
                if MARKDOWN in text_modes and COMPARE not in text_modes
                else [
                    html.Span(text, style={**inner_style, "whiteSpace": "pre-wrap"})
                    for text, inner_style in texts
                ]
            )
        ),
        style=style,
    )  # TODO make classes


def get_height_adjustment() -> html.Iframe:
    return html.Iframe(
        id="query_params_iframe",
        srcDoc="""
        <!DOCTYPE html>
        <html>
        <head>
        </head>
        <body>
            <script>
                window.addEventListener('DOMContentLoaded', function() {
                    parent.registerTextarea();
                });
            </script>
        </body>
        </html>
        """,
        style={"visibility": "hidden"},
    )


def update_height_js(iframe_id: str) -> str:
    return f"""
        function updateHeight() {{
            var body = document.body,
                html = document.documentElement;
            
            var height = Math.max(body.scrollHeight, body.offsetHeight,
                                    html.clientHeight, html.scrollHeight, html.offsetHeight);
            
            parent.postMessage({{ frameHeight: height, frameId: '{iframe_id}' }}, '*');
        }}
        window.onload = updateHeight;
        window.onresize = updateHeight;
    """


def get_random_id() -> str:
    return "".join(random.choices(string.ascii_letters + string.digits, k=20))


def iframe_template(
    header: str, content: str, style: Dict = {}, iframe_id: str = None
) -> html.Iframe:
    if not iframe_id:
        iframe_id = get_random_id()

    iframe_style = {
        "width": "100%",
        "border": "none",
        "overflow": "hidden",
    }

    iframe_style.update(style)

    return html.Iframe(
        id=iframe_id,
        srcDoc=f"""
        <!DOCTYPE html>
        <html>
        <head>
            {header}
        </head>
        <body>
            {content}
        </body>
        </html>
        """,
        style=iframe_style,
    )
