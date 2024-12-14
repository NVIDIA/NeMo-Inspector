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

from difflib import SequenceMatcher
import re


def tokenize(text: str):
    """
    Tokenize the text into separate tokens for:
    - Whitespace sequences (\s+)
    - Word sequences (\w+)
    - Punctuation sequences ([^\w\s]+)

    The regex ensures we capture all text in order.
    """
    # This pattern will capture tokens in the order they appear:
    #   (\s+) => one or more whitespace chars
    #   (\w+) => one or more word chars
    #   ([^\w\s]+) => one or more chars that are not word chars or whitespace (punctuation)
    pattern = re.compile(r"(\s+|\w+|[^\w\s]+)")
    tokens = pattern.findall(text)
    return tokens


def color_text_diff(text1: str, text2: str):
    if text1 == text2:
        return [(text1, {})]

    tokens1 = tokenize(text1)
    tokens2 = tokenize(text2)

    matcher = SequenceMatcher(None, tokens1, tokens2)
    result = []

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            for k in range(j1, j2):
                result.append((tokens2[k], {}))

        elif tag == "replace":
            # Tokens from text1 (deleted)
            for k in range(i1, i2):
                result.append((tokens1[k], {"background-color": "#c8e6c9"}))
            # Tokens from text2 (inserted)
            for k in range(j1, j2):
                result.append(
                    (
                        tokens2[k],
                        {
                            "background-color": "#ffcdd2",
                            "text-decoration": "line-through",
                        },
                    )
                )

        elif tag == "insert":
            for k in range(j1, j2):
                result.append(
                    (
                        tokens2[k],
                        {
                            "background-color": "#ffcdd2",
                            "text-decoration": "line-through",
                        },
                    )
                )

        elif tag == "delete":
            for k in range(i1, i2):
                result.append((tokens1[k], {"background-color": "#c8e6c9"}))

    return result
