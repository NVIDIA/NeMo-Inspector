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

from typing import Callable, Optional, Tuple


def get_starts_with_latex_tag_function(
    tag: str, default_index_move: int
) -> Callable[[str, int], Tuple[bool, int]]:
    def starts_with_tag_func_templ(text: str, index: int):
        is_starts_with_tag = text.startswith(tag, index)
        if not is_starts_with_tag:
            returning_index = index + default_index_move
        elif "{" not in tag:
            returning_index = index + len(tag)
        else:
            returning_index = text.find("}", index) % (len(text) + 1)

        return is_starts_with_tag, returning_index

    return starts_with_tag_func_templ


def proccess_latex_tag(
    text: str,
    start_index: int,
    detect_start_token: Callable[[str, int], Tuple[bool, int]],
    detect_end_token: Callable[[str, int], Tuple[bool, int]],
    end_sign: Optional[str],
    last_block_only: bool = False,
) -> int:
    count = 0
    index = start_index
    while index < len(text):
        if end_sign and text[index] == end_sign:
            return start_index, start_index + 1
        is_start_token, new_index = detect_start_token(text, index)
        count += is_start_token
        if last_block_only and is_start_token:
            start_index = index
            count = min(1, count)
        index = new_index
        is_end_token, index = detect_end_token(text, index)
        count -= is_end_token
        if count == 0:
            break
    return start_index, index + 1


def get_single_dollar_detection_functions(
    direction: int, default_index_move: int
) -> Callable[[str, int], Tuple[bool, int]]:
    return lambda text, index: (
        text[index] == "$" and not text[index + direction].isspace(),
        index + default_index_move,
    )


def get_latex_detection_functions(text, index) -> tuple[
    Callable[[str, int], Tuple[bool, int]],
    Callable[[str, int], Tuple[bool, int]],
    Optional[str],
    bool,
    bool,
]:
    multiline_tags = [("\\begin{", "\\end{", True), ("$$", "$$", False)]
    for start_tag, end_tag, add_dollars in multiline_tags:
        if text.startswith(start_tag, index):
            return (
                get_starts_with_latex_tag_function(start_tag, 1),
                get_starts_with_latex_tag_function(end_tag, 0),
                None,
                add_dollars,
                False,
            )

    starts_with_dollar_func = get_single_dollar_detection_functions(1, 1)
    ends_with_dollar_func = get_single_dollar_detection_functions(-1, 0)
    if starts_with_dollar_func(text, index)[0]:
        return starts_with_dollar_func, ends_with_dollar_func, "\n", False, True

    return None, None, None, None, None


def proccess_plain_text(text: str) -> str:
    special_chars = r"*_{}[]()#+-.!`"
    for character in special_chars:
        text = text.replace(character, "\\" + character)
    return text


def preprocess_latex(text: str, escape: bool = True) -> str:
    text = "\n" + text.replace("\\[", "\n$$\n").replace("\\]", "\n$$\n").replace(
        "\\(", " $"
    ).replace("\\)", "$ ")

    right_side_operations = ["-", "=", "+", "*", "/"]
    left_side_operations = ["=", "+", "*", "/"]
    for op in right_side_operations:
        text = text.replace(op + "$", op + " $")

    for op in left_side_operations:
        text = text.replace("$" + op, "$ " + op)

    text += "\n"
    index = 1
    texts = []
    start_plain_text_index = -1
    while index < len(text) - 1:
        (
            detect_start_token,
            detect_end_token,
            end_sign,
            add_dollars,
            use_last_block_only,
        ) = get_latex_detection_functions(text, index)
        if detect_start_token is not None:
            if start_plain_text_index != -1:
                texts.append(
                    proccess_plain_text(text[start_plain_text_index:index])
                    if escape
                    else text[start_plain_text_index:index]
                )
                start_plain_text_index = -1

            start_index, new_index = proccess_latex_tag(
                text,
                index,
                detect_start_token,
                detect_end_token,
                end_sign,
                use_last_block_only,
            )
            texts.append(
                proccess_plain_text(text[index:start_index])
                if escape
                else text[index:start_index]
            )
            if add_dollars:
                texts.append("\n$$\n")
                texts.append(text[start_index:new_index].strip())
                texts.append("\n$$\n")
            else:
                texts.append(text[start_index:new_index])
            index = new_index
        elif start_plain_text_index == -1:
            start_plain_text_index = index
            index += 1
        else:
            index += 1
    if start_plain_text_index != -1:
        texts.append(
            proccess_plain_text(text[start_plain_text_index:])
            if escape
            else text[start_plain_text_index:]
        )
    return "".join(texts).replace("\n", "\n\n").strip()
