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


def color_text_diff(text1: str, text2: str) -> str:
    if text1 == text2:
        return [(text1, {})]
    matcher = SequenceMatcher(None, text1, text2)
    result = []
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            result.append((text2[j1:j2], {}))
        elif tag == "replace":
            result.append((text1[i1:i2], {"background-color": "#c8e6c9"}))
            result.append(
                (
                    text2[j1:j2],
                    {"background-color": "#ffcdd2", "text-decoration": "line-through"},
                )
            )
        elif tag == "insert":
            result.append(
                (
                    text2[j1:j2],
                    {"background-color": "#ffcdd2", "text-decoration": "line-through"},
                )
            )
        elif tag == "delete":
            result.append((text1[i1:i2], {"background-color": "#c8e6c9"}))
    return result
