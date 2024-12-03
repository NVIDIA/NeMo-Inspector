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

CODE_SEPARATORS = {
    "code_begin": "{code_begin}",
    "code_end": "{code_end}",
    "code_output_begin": "{code_output_begin}",
    "code_output_end": "{code_output_end}",
    "code_output_format": "llama",
}
DATA_PAGE_SIZE = 10
EXTRA_FIELDS = ["page_index", "file_name"]
IGNORE_FIELDS = ["stop_phrases", "used_prompt", "server_type"]
PARAMS_TO_REMOVE = [
    "output_file",
    "dataset",
    "split",
    "retriever",
    "_context_template",
    "save_generations_path",
]
RETRIEVAL_FIELDS = [
    "max_retrieved_chars_field",
    "retrieved_entries",
    "retrieval_file",
    "retrieval_field",
    "retrieved_few_shots",
    "max_retrieved_chars",
    "randomize_retrieved_entries",
]
SEPARATOR_DISPLAY = "."
SEPARATOR_ID = "->"
SETTING_PARAMS = [
    "server",
    "sandbox",
    "output_file",
    "inspector_params",
    "types",
    "stop_phrases",
]
STATS_KEYS = [
    "question_index",
    "problem",
]
