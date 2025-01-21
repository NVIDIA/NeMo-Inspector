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

import functools
import inspect
import json
import logging
import os
import re
from collections import defaultdict
from dataclasses import fields, is_dataclass
from types import NoneType, UnionType
from typing import (
    Any,
    Callable,
    Dict,
    Iterable,
    List,
    Optional,
    Set,
    Tuple,
    Union,
    get_args,
    get_origin,
    get_type_hints,
)

from flask import current_app
from joblib import Parallel, delayed

from nemo_inspector.settings.constants import (
    EXPECTED_ANSWER_FIELD,
    CUSTOM,
    ERROR_MESSAGE_TEMPLATE,
    FILE_NAME,
    GENERAL_STATS,
    IGNORE_FIELDS,
    INLINE_STATS,
    PARAMS_TO_REMOVE,
    QUESTION_FIELD,
    RETRIEVAL_FIELDS,
    SEPARATOR_DISPLAY,
    SETTING_PARAMS,
    STATS_KEYS,
    UNDEFINED,
)

from nemo_skills.evaluation.metrics.utils import is_correct_judgement
from nemo_skills.prompt.few_shot_examples import examples_map
from nemo_skills.prompt.utils import PromptConfig, PromptTemplate

custom_stats = {}
general_custom_stats = {}
deleted_stats = set()
excluded_rows = set()
editable_rows = set()
compared_rows = set()
stats_raw = {INLINE_STATS: {CUSTOM: ""}, GENERAL_STATS: {CUSTOM: ""}}

dataset_data = []
labels = []


def get_examples_map() -> Set:
    return examples_map


def get_editable_rows() -> Set:
    return editable_rows


def get_excluded_row() -> Set:
    return excluded_rows


def get_deleted_stats() -> Set:
    return deleted_stats


def get_custom_stats() -> Dict:
    return custom_stats


def get_compared_rows() -> Dict:
    return compared_rows


def get_general_custom_stats() -> Dict:
    return general_custom_stats


def get_stats_raw() -> Dict:
    return stats_raw


def clear_table_data() -> None:
    global dataset_data
    dataset_data = []


def get_table_data() -> List:
    return dataset_data


def get_labels() -> List:
    return labels


def parse_model_answer(answer: str) -> List[Dict]:
    """
    Parses a model answer and extracts code blocks, explanations, and outputs preserving their sequence.

    Args:
        answer (str): The model answer to parse.

    Returns:
        List[Dict]: A list of dictionaries containing the parsed results. Each dictionary
        contains the following keys:
            - 'explanation': The explanation text before the code block.
            - 'code': The code block.
            - 'output': The output of the code block.

    """
    config = current_app.config["nemo_inspector"]
    code_start, code_end = map(
        re.escape,
        config["inspector_params"]["code_separators"],
    )
    output_start, output_end = map(
        re.escape,
        config["inspector_params"]["code_output_separators"],
    )
    code_pattern = re.compile(rf"{code_start}(.*?){code_end}", re.DOTALL)
    code_output_pattern = re.compile(
        rf"{code_start}(.*?){code_end}\s*{output_start}(.*?){output_end}",
        re.DOTALL,
    )
    code_matches = list(code_pattern.finditer(answer))
    code_output_matches = list(code_output_pattern.finditer(answer))
    parsed_results = []
    last_index = 0
    for code_match in code_matches:
        explanation = answer[last_index : code_match.start()].strip()
        code_text = code_match.group(1).strip()
        output_text = None
        if code_output_matches and code_output_matches[0].start() == code_match.start():
            output_match = code_output_matches.pop(0)
            output_text = output_match.group(2).strip()
        parsed_results.append(
            {
                "explanation": explanation,
                "code": code_text,
                "output": output_text,
            }
        )
        last_index = code_match.end()
        if output_text is not None:
            last_index = output_match.end()
    if last_index < len(answer):
        trailing_text = answer[last_index:].strip()
        if code_start.replace("\\", "") in trailing_text:
            code_start_index = trailing_text.find(code_start.replace("\\", ""))
            parsed_results.append(
                {
                    "explanation": trailing_text[0:code_start_index].strip(),
                    "code": trailing_text[
                        code_start_index + len(code_start.replace("\\", "")) :
                    ],
                    "output": "code_block was not finished",
                    "wrong_code_block": True,
                }
            )
            trailing_text = None
        if trailing_text:
            parsed_results.append(
                {"explanation": trailing_text, "code": None, "output": None}
            )
    return parsed_results


@functools.lru_cache()
def get_dataset_sample(index: int, dataset: str) -> Tuple[Dict, int]:
    if not dataset or dataset == UNDEFINED or os.path.isfile(dataset) is False:
        return {QUESTION_FIELD: "", EXPECTED_ANSWER_FIELD: ""}, 0
    with open(dataset) as file:
        tests = file.readlines()
        index = max(min(len(tests), index), 1)
        test = (
            json.loads(tests[index - 1])
            if index != 0
            else {QUESTION_FIELD: "", EXPECTED_ANSWER_FIELD: ""}
        )
    return test, index


def get_values_from_input_group(children: Iterable) -> Dict:
    values = {}
    for child in children:
        for input_group_child in child["props"]["children"]:
            if (
                "id" in input_group_child["props"].keys()
                and "value" in input_group_child["props"].keys()
            ):
                type_function = str
                value = input_group_child["props"]["value"]
                id = (
                    input_group_child["props"]["id"]["id"]
                    if isinstance(input_group_child["props"]["id"], Dict)
                    else input_group_child["props"]["id"]
                )
                if value is None:
                    values[id] = None
                    continue
                if str(value).isdigit() or str(value).replace("-", "", 1).isdigit():
                    type_function = int
                elif str(value).replace(".", "", 1).replace("-", "", 1).isdigit():
                    type_function = float

                values[id] = type_function(str(value).replace("\\n", "\n"))

    return values


def extract_query_params(query_params_ids: List[Dict], query_params: List[Dict]) -> Dict:
    default_answer = {QUESTION_FIELD: "", "expected_answer": ""}
    try:
        query_params_extracted = {
            param_id["id"]: param
            for param_id, param in zip(query_params_ids, query_params)
        }
    except ValueError:
        query_params_extracted = default_answer

    return query_params_extracted or default_answer


def get_utils_from_config_helper(cfg: Dict, display_path: bool = True) -> Dict:
    config = {}
    for key, value in sorted(cfg.items()):
        if key in PARAMS_TO_REMOVE or key in SETTING_PARAMS:
            continue
        elif isinstance(value, Dict):
            config = {
                **config,
                **{
                    (
                        key + SEPARATOR_DISPLAY
                        if display_path and "template" in inner_key
                        else ""
                    )
                    + inner_key: value
                    for inner_key, value in get_utils_from_config_helper(value).items()
                },
            }
        elif not isinstance(value, List):
            config[key] = value
    return config


def get_utils_from_config(cfg: Dict, display_path: bool = True) -> Dict:
    return {
        SEPARATOR_DISPLAY.join(key.split(SEPARATOR_DISPLAY)[1:]) or key: value
        for key, value in get_utils_from_config_helper(cfg, display_path).items()
        if key not in RETRIEVAL_FIELDS + IGNORE_FIELDS
    }


def get_stats(all_files_data: List[Dict]) -> Tuple[float, float, float]:
    """Returns the percentage of correct, wrong, and no response answers in the given data.

    If not data is provided, returns -1 for all values.
    """
    correct = 0
    wrong = 0
    no_response = 0
    for data in all_files_data:
        if data.get("predicted_answer") is None:
            no_response += 1
        elif is_correct_judgement(data.get("judgement", "")):
            correct += 1
        else:
            wrong += 1

    if len(all_files_data):
        return (
            correct / len(all_files_data),
            wrong / len(all_files_data),
            no_response / len(all_files_data),
        )
    return -1, -1, -1


def get_metrics(all_files_data: List[Dict], errors_dict: Dict = {}) -> Dict:
    correct_responses, wrong_responses, no_response = get_stats(all_files_data)
    custom_stats = {}
    for name, func in get_custom_stats().items():
        if name not in errors_dict:
            errors_dict[name] = {}
        custom_stats[name] = catch_eval_exception(
            [],
            func,
            all_files_data,
            "Got error when applying function",
            errors_dict[name],
        )

    stats = {
        "correct_responses": round(correct_responses, 2),
        "wrong_responses": round(wrong_responses, 2),
        "no_response": round(no_response, 2),
        **custom_stats,
    }
    return stats


def get_eval_function(text):
    template = """
def eval_function(data):
{}
    return {}
"""
    code_lines = [""] + text.strip().split("\n")
    code = template.format(
        "\n    ".join(code_lines[:-1]),
        code_lines[-1:][0],
    )
    namespace = {}
    exec(code, namespace)
    return namespace["eval_function"]


def calculate_metrics_for_whole_data(table_data: List, model_id: str) -> Dict:
    errors_dict = {}
    for question_id in range(len(table_data)):
        stats = get_metrics(table_data[question_id][model_id], errors_dict)
        table_data[question_id][model_id] = list(
            map(
                lambda data: {**data, **stats},
                table_data[question_id][model_id],
            )
        )
    if len(errors_dict):
        for name, error_dict in errors_dict.items():
            if len(error_dict):
                logging.error(ERROR_MESSAGE_TEMPLATE.format(name, error_dict))


def catch_eval_exception(
    available_models: List[str],
    eval_func: Callable[[Dict], bool],
    data: Dict,
    default_answer: Union[bool, str],
    errors_dict: Optional[Dict] = {},
) -> bool:
    try:
        if eval_func is None:
            return default_answer
        return eval_func(data)
    except Exception as e:
        if str(e).split(" ")[-1].replace("'", "") not in available_models:
            if str(e) not in errors_dict:
                errors_dict[str(e)] = 0
            errors_dict[str(e)] += 1
        return default_answer


def custom_deepcopy(data) -> List:
    new_data = []
    for item in data:
        new_item = {}
        for key, value_list in item.items():
            new_item[key] = value_list
        new_data.append(new_item)
    return new_data


@functools.lru_cache(maxsize=1)
def get_data_from_files() -> List:
    base_config = current_app.config["nemo_inspector"]
    dataset = None
    if os.path.isfile(base_config["input_file"]):
        with open(base_config["input_file"]) as f:
            dataset = [json.loads(line) for line in f]

    available_models = {
        model_name: model_info["file_paths"]
        for model_name, model_info in get_available_models().items()
    }

    all_models_data_array = []

    def process_model_files(model_id, results_files, dataset):
        model_data = defaultdict(list)
        file_names = {}
        for file_id, path in enumerate(results_files):
            file_name = path.split("/")[-1].split(".")[0]
            if file_name in file_names:
                file_names[file_name] += 1
                file_name += f"_{file_names[file_name]}"
            else:
                file_names[file_name] = 1
            with open(path) as f:
                answers = map(json.loads, f)
                for question_index, answer in enumerate(answers):
                    result = {
                        FILE_NAME: file_name,
                        **(
                            dataset[question_index]
                            if dataset and len(dataset) > question_index
                            else {}
                        ),
                        "question_index": question_index + 1,
                        "page_index": file_id,
                        "labels": [],
                        **answer,
                    }
                    model_data[question_index].append(result)
        return model_id, model_data

    num_cores = -1
    model_data_list = Parallel(n_jobs=num_cores)(
        delayed(process_model_files)(model_id, results_files, dataset)
        for model_id, results_files in available_models.items()
    )

    for model_id, model_data in model_data_list:
        for question_index, results in model_data.items():
            if len(all_models_data_array) <= question_index:
                all_models_data_array.append({})
            all_models_data_array[question_index][model_id] = results
            stats = get_metrics(all_models_data_array[question_index][model_id])
            all_models_data_array[question_index][model_id] = list(
                map(
                    lambda data: {**data, **stats},
                    all_models_data_array[question_index][model_id],
                )
            )
    return all_models_data_array


def get_filtered_files(
    filter_function: str,
    sorting_function: str,
    array_to_filter: List,
) -> List:
    filter_lambda_functions = [
        get_eval_function(func.strip())
        for func in (filter_function if filter_function else "True").split("&&")
    ]
    available_models = get_available_models()
    filtered_data = [
        list(
            filter(
                lambda data: catch_eval_exception(
                    available_models, function, data, False
                ),
                array_to_filter,
            )
        )
        for function in filter_lambda_functions
    ]

    filtered_data = list(filter(lambda data: data != [], filtered_data))
    filtered_data = filtered_data[0] if len(filtered_data) > 0 else [{FILE_NAME: ""}]
    if sorting_function and filtered_data != [{FILE_NAME: ""}]:
        sorting_lambda_function = get_eval_function(sorting_function.strip())
        filtered_data.sort(
            key=lambda data: catch_eval_exception(
                available_models, sorting_lambda_function, data, 0
            )
        )

    return filtered_data


def is_detailed_answers_rows_key(key: str) -> bool:
    return (
        key not in get_deleted_stats()
        and "index" not in key
        and key not in STATS_KEYS + list(get_metrics([]).keys())
        or key == QUESTION_FIELD
    )


@functools.lru_cache(maxsize=1)
def get_available_models() -> Dict:
    config = current_app.config["nemo_inspector"]["inspector_params"]
    runs_storage = {}
    for model_name, files in config["model_prediction"].items():
        runs_storage[model_name] = {
            "file_paths": files,
        }

    return runs_storage


def get_utils_dict(
    name: Union[str, Dict], value: Union[str, int], id: Union[str, Dict] = None
):
    if id is None:
        id = name
    if name in current_app.config["nemo_inspector"]["types"].keys():
        template = {
            "props": {
                "id": id,
                "options": [
                    {"label": value, "value": value}
                    for value in current_app.config["nemo_inspector"]["types"][name]
                ],
                "value": current_app.config["nemo_inspector"]["types"][name][0],
            },
            "type": "Select",
            "namespace": "dash_bootstrap_components",
        }
    elif isinstance(value, (int, float)):
        float_params = {"step": 0.1} if isinstance(value, float) else {}
        template = {
            "props": {
                "id": id,
                "debounce": True,
                "min": 0,
                "type": "number",
                "value": value,
                **float_params,
            },
            "type": "Input",
            "namespace": "dash_bootstrap_components",
        }
    else:
        template = {
            "props": {
                "id": id,
                "debounce": True,
                "style": {"width": "100%"},
                "value": value,
            },
            "type": "Textarea",
            "namespace": "dash_bootstrap_components",
        }
    return {
        "props": {
            "children": [
                {
                    "props": {"children": name},
                    "type": "InputGroupText",
                    "namespace": "dash_bootstrap_components",
                },
                template,
            ],
            "className": "mb-3",
        },
        "type": "InputGroup",
        "namespace": "dash_bootstrap_components",
    }


def get_file_id(file_names: List[str], files: List[Dict], column_id: str):
    file_id = 0
    file_name = (
        file_names[column_id]["value"]
        if isinstance(file_names[column_id], Dict)
        else file_names[column_id]
    )
    for i, file_data in enumerate(files):
        if file_data[FILE_NAME] == file_name:
            file_id = i
            break
    return file_id


def initialize_default(
    cls: Union[PromptTemplate, PromptConfig], specification: Dict = {}
) -> Union[PromptTemplate, PromptConfig]:
    if not specification:
        specification = {}

    def get_default(field, specification: Dict = None):
        if not specification:
            specification = {}
        _type = get_type_hints(cls)[field.name]
        if is_dataclass(_type):
            return initialize_default(
                _type,
                {
                    **specification,
                    **(
                        specification.get(field.name, {})
                        if isinstance(specification.get(field.name, {}), Dict)
                        else {}
                    ),
                },
            )
        if isinstance(specification, Dict) and field.name in specification:
            return specification[field.name]
        else:
            args = get_args(_type)
            if len(args):
                if NoneType in args:
                    return None
                else:
                    return args[0]()
            return (get_origin(_type) or _type)()

    return cls(**{field.name: get_default(field, specification) for field in fields(cls)})


def resolve_type(field_type):
    origin = get_origin(field_type)
    if origin is not None:
        # If the type is a generic, use its origin (e.g., list, dict)
        return origin
    elif isinstance(field_type, type):
        return field_type
    else:
        # For special cases like typing.Any, return str by default
        return str


def get_type_default(field_type):
    try:
        return resolve_type(field_type)()
    except Exception:
        return None


def resolve_union_or_any(field_type):
    """Resolve Union and Any types to concrete types"""
    origin_type = get_origin(field_type)
    if origin_type is UnionType:
        args = get_args(field_type)
        non_none_args = [arg for arg in args if arg is not type(None)]
        return non_none_args[0] if non_none_args else str
    elif field_type is Any:
        return str
    else:
        return resolve_type(field_type)


def get_init_params(cls):
    params = {}

    # Iterate through the class and its base classes in MRO
    for base_cls in inspect.getmro(cls):
        if base_cls is object:
            continue  # Skip the base `object` class

        # Get the __init__ method
        init_method = base_cls.__init__
        init_signature = inspect.signature(init_method)
        type_hints = get_type_hints(init_method)

        for name, param in init_signature.parameters.items():
            if name in ["self", "args", "kwargs"] or name in params:
                continue  # Skip 'self' and already processed parameters

            # Determine default value
            if param.default is not inspect.Parameter.empty:
                # If a default value exists, use it
                params[name] = param.default
            else:
                # If no default value, use the type initializer
                param_type = type_hints.get(name, None)
                params[name] = get_type_default(resolve_union_or_any(param_type))
    return params
