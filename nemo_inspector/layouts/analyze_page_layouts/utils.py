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

from typing import List

from dash import html
import dash_ace

from nemo_inspector.layouts.common_layouts import get_selector_layout
from nemo_inspector.settings.constants import STATS_KEYS
from nemo_inspector.utils.common import get_metrics, get_table_data
from nemo_inspector.settings.constants.common import (
    CUSTOM,
    DELETE,
    FILES_FILTERING,
    FILES_ONLY,
    GENERAL_STATS,
    INLINE_STATS,
    QUESTIONS_FILTERING,
)
from nemo_inspector.utils.common import (
    get_custom_stats,
    get_general_custom_stats,
    get_stats_raw,
)


def get_filter_text(
    available_filters: List[str] = [], mode: str = FILES_FILTERING
) -> str:
    available_filters = list(
        get_table_data()[0][list(get_table_data()[0].keys())[0]][0].keys()
        if len(get_table_data()) and not available_filters
        else STATS_KEYS + list(get_metrics([]).keys()) + ["+ all fields in json"]
    )
    if mode == FILES_ONLY:
        return (
            "Write an expression to filter the data\n\n"
            + "For example:\ndata['is_correct'] and not data['error_message']\n\n"
            + "The expression has to return bool.\n\n"
            + "Available parameters to filter data:\n"
            + "\n".join(
                [
                    ", ".join(available_filters[start : start + 5])
                    for start in range(0, len(available_filters), 5)
                ]
            ),
        )
    elif mode == FILES_FILTERING:
        return (
            "Write an expression to filter the data\n"
            + "Separate expressions for different generations with &&\n"
            + "You can use base_generation variable to access data from the current generation\n\n"
            + "For example:\ndata['generation1']['correct_responses'] > 0.5 && data[base_generation]['no_response'] < 0.2\n\n"
            + "The expression has to return bool.\n\n"
            + "Available parameters to filter data:\n"
            + "\n".join(
                [
                    ", ".join(available_filters[start : start + 5])
                    for start in range(0, len(available_filters), 5)
                ]
            ),
        )
    elif mode == QUESTIONS_FILTERING:
        return (
            "Write an expression to filter the data\n"
            + "You can operate with a dictionary containing keys representing generation names\n"
            + "and a list of values as JSON data from your generation from each file.\n"
            + "You can use base_generation variable to access data from the current generation\n\n"
            + "For example:\ndata['generation1'][0]['is_correct'] != data[base_generation][0]['is_correct']\n\n"
            + "The expression has to return bool.\n\n"
            + "Available parameters to filter data:\n"
            + "\n".join(
                [
                    ", ".join(available_filters[start : start + 5])
                    for start in range(0, len(available_filters), 5)
                ]
            ),
        )


def get_stats_text(general_stats: bool = False, delete: bool = False):
    if delete:
        return "Choose the name of the statistic you want to delete"
    else:
        if general_stats:
            return (
                "Creating General Custom Statistics:\n\n"
                "To introduce new general custom statistics:\n"
                "1. Create a dictionary where keys are the names of your custom stats.\n"
                "2. Assign functions as values. These functions should accept arrays where first dimension\n"
                "is a question index and second is a file number (both sorted and filtered).\n\n"
                "Example:\n\n"
                "Define a custom function to integrate into your stats:\n\n"
                "def my_func(datas):\n"
                "    correct_responses = 0\n"
                "    for question_data in datas:\n"
                "        for file_data in question_data:\n"
                "            correct_responses += file_data['is_correct']\n"
                "    return correct_responses\n"
                "{'correct_responses': my_func}"
            )
        else:
            return (
                "Creating Custom Statistics:\n\n"
                "To introduce new custom statistics:\n"
                "1. Create a dictionary where keys are the names of your custom stats.\n"
                "2. Assign functions as values. These functions should accept arrays containing data\n"
                "from all relevant files.\n\n"
                "Note: Do not use names that already exist in the current stats or JSON fields\n"
                "to avoid conflicts.\n\n"
                "Example:\n\n"
                "Define a custom function to integrate into your stats:\n\n"
                "def unique_error_counter(datas):\n"
                "    unique_errors = set()\n"
                "    for data in datas:\n"
                "        unique_errors.add(data.get('error_message'))\n"
                "    return len(unique_errors)\n\n"
                "{'unique_error_count': unique_error_counter}"
            )


def get_code_text_area_layout(id) -> dash_ace.DashAceEditor:
    return dash_ace.DashAceEditor(
        id=id,
        theme="tomorrow_night",
        mode="python",
        tabSize=4,
        enableBasicAutocompletion=True,
        enableLiveAutocompletion=True,
        placeholder="Write your code here...",
        value="",
        style={"width": "100%", "height": "300px"},
    )


def get_stats_input(modes: List[str] = []) -> List:
    body = []
    if DELETE in modes:
        delete_options = list(
            get_general_custom_stats().keys()
            if GENERAL_STATS in modes
            else get_custom_stats().keys()
        )
        body += [
            get_selector_layout(
                delete_options,
                "stats_input",
                delete_options[0] if delete_options else "",
            )
        ]
    else:
        mode = GENERAL_STATS if GENERAL_STATS in modes else INLINE_STATS
        extractor_options = list(get_stats_raw()[mode].keys())
        body += [
            get_selector_layout(extractor_options, "stats_extractor", CUSTOM),
            get_code_text_area_layout(id="stats_input"),
        ]
    return [
        html.Pre(
            get_stats_text(GENERAL_STATS in modes, DELETE in modes), id="stats_text"
        ),
    ] + body
