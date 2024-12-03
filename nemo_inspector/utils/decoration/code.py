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

from html import escape
from io import StringIO
from typing import Dict, List, Tuple

from dash import html
from pygments.formatters import HtmlFormatter
from pygments.lexers import PythonLexer

from nemo_inspector.utils.decoration.common import (
    get_random_id,
    iframe_template,
    update_height_js,
)


def highlight_code(codes: List[Tuple[str, Dict[str, str]]], **kwargs) -> html.Iframe:

    full_code = "".join([code for code, style in codes])

    # Track positions and styles
    positions = []
    current_pos = 0
    for code, style in codes:
        start_pos = current_pos
        end_pos = current_pos + len(code)
        if style:
            positions.append((start_pos, end_pos, style))
        current_pos = end_pos

    # Custom formatter to apply styles at correct positions
    class CustomHtmlFormatter(HtmlFormatter):
        def __init__(self, positions, **options):
            super().__init__(**options)
            self.positions = positions
            self.current_pos = 0

        def format(self, tokensource, outfile):
            style_starts = {start: style for start, _, style in self.positions}
            style_ends = {end: style for _, end, style in self.positions}
            active_styles = []

            for ttype, value in tokensource:
                token_length = len(value)
                token_start = self.current_pos

                # Apply styles character by character
                result = ""
                for i, char in enumerate(value):
                    char_pos = token_start + i

                    # Check if a style starts or ends here
                    if char_pos in style_starts:
                        style = style_starts[char_pos]
                        active_styles.append(style)
                    if char_pos in style_ends:
                        style = style_ends[char_pos]
                        if style in active_styles:
                            active_styles.remove(style)

                    # Get CSS class for syntax highlighting
                    css_class = self._get_css_class(ttype)
                    char_html = escape(char)
                    if css_class:
                        char_html = f'<span class="{css_class}">{char_html}</span>'

                    # Apply active styles
                    if active_styles:
                        combined_style = {}
                        for style_dict in active_styles:
                            combined_style.update(style_dict)
                        style_str = "; ".join(
                            f"{k}: {v}" for k, v in combined_style.items()
                        )
                        char_html = f'<span style="{style_str}">{char_html}</span>'

                    result += char_html

                outfile.write(result)
                self.current_pos += token_length

    # Use the custom formatter to highlight the code
    lexer = PythonLexer()
    formatter = CustomHtmlFormatter(positions, nowrap=True)
    style_defs = formatter.get_style_defs(".highlight")
    style_defs += """
.highlight {
    font-family: monospace;
}
"""

    output = StringIO()
    formatter.format(lexer.get_tokens(full_code), output)
    highlighted_code = output.getvalue()

    # Build the iframe content
    iframe_id = get_random_id()
    content = f"""
<div class="highlight" style="white-space: pre-wrap; background-color: #ebecf0d8;">{highlighted_code}</div>
<script>{update_height_js(iframe_id)}</script>
"""

    return html.Div(
        iframe_template(
            header=f"<style>{style_defs}</style>",
            content=content,
            iframe_id=iframe_id,
            style={"border": "black 1px solid", "background-color": "#ebecf0d8"},
        )
    )
