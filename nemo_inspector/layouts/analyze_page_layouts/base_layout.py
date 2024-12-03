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

import logging
from typing import List

import dash_bootstrap_components as dbc
from dash import dcc, html

from nemo_inspector.layouts.analyze_page_layouts.table_layouts import (
    get_detailed_info_table_layout,
    get_general_stats_layout,
    get_short_info_table_layout,
)
from nemo_inspector.layouts.common_layouts import (
    get_selector_layout,
)
from nemo_inspector.settings.constants import (
    BASE_GENERATION,
    CHOOSE_GENERATION,
    ERROR_MESSAGE_TEMPLATE,
    FILES_FILTERING,
)
from nemo_inspector.utils.common import (
    catch_eval_exception,
    custom_deepcopy,
    get_available_models,
    get_data_from_files,
    get_eval_function,
    get_metrics,
    get_table_data,
    is_detailed_answers_rows_key,
)
from nemo_inspector.layouts.analyze_page_layouts.modals_layouts import (
    get_add_stats_modal_layout,
    get_change_label_modal_layout,
    get_filter_modal_layout,
    get_sorting_modal_layout,
    get_update_dataset_modal_layout,
    get_save_dataset_modal_layout,
)


def get_compare_test_layout() -> html.Div:
    return html.Div(
        [
            dbc.InputGroup(
                [
                    get_sorting_modal_layout(),
                    get_filter_modal_layout(),
                    get_add_stats_modal_layout(),
                    get_change_label_modal_layout(apply_for_all_files=False),
                    get_update_dataset_modal_layout(),
                    get_save_dataset_modal_layout(),
                    dbc.Button(
                        "+",
                        id="add_model",
                        outline=True,
                        color="primary",
                        className="me-1",
                        class_name="button-class",
                        style={"margin-left": "1px"},
                    ),
                    get_selector_layout(
                        get_available_models().keys(),
                        "base_model_answers_selector",
                        value=CHOOSE_GENERATION,
                    ),
                ]
            ),
            html.Pre(id="filtering_container"),
            html.Pre(id="sorting_container"),
            dcc.Loading(
                children=dbc.Container(
                    id="loading_container", style={"display": "none"}, children=""
                ),
                type="circle",
                style={"margin-top": "50px"},
            ),
            html.Div(
                children=[],
                id="compare_models_rows",
            ),
        ],
    )


def get_updated_tables_layout(
    base_model: str, update_function: str, models: List[str]
) -> List[html.Tr]:
    errors_dict = {}
    global table_data
    if update_function:
        update_eval_function = get_eval_function(update_function.strip())
        available_models = {
            model_name: model_info["file_paths"]
            for model_name, model_info in get_available_models().items()
        }

        for question_id in range(len(table_data)):
            new_dicts = list(
                map(
                    lambda data: catch_eval_exception(
                        available_models,
                        update_eval_function,
                        data,
                        data,
                        errors_dict,
                    ),
                    table_data[question_id][base_model],
                )
            )
            for i, new_dict in enumerate(new_dicts):
                for key, value in new_dict.items():
                    table_data[question_id][base_model][i][key] = value

                keys = list(table_data[question_id][base_model][i].keys())
                for key in keys:
                    if key not in new_dict:
                        table_data[question_id][base_model][i].pop(key)

    if len(errors_dict):
        logging.error(ERROR_MESSAGE_TEMPLATE.format("update_dataset", errors_dict))

    return (
        get_short_info_table_layout()
        + get_general_stats_layout(base_model)
        + get_detailed_info_table_layout(
            models,
            list(
                filter(
                    is_detailed_answers_rows_key,
                    (
                        table_data[0][base_model][0].keys()
                        if len(table_data) and len(table_data[0][base_model])
                        else []
                    ),
                )
            ),
        )
    )


def get_sorted_tables_layout(
    base_model: str, sorting_function: str, models: List[str]
) -> List[html.Tr]:
    errors_dict = {}
    global table_data
    if sorting_function:
        sortting_eval_function = get_eval_function(sorting_function.strip())
        available_models = {
            model_name: model_info["file_paths"]
            for model_name, model_info in get_available_models().items()
        }

        for question_id in range(len(table_data)):
            for model in table_data[question_id].keys():
                table_data[question_id][model].sort(
                    key=lambda data: catch_eval_exception(
                        available_models,
                        sortting_eval_function,
                        data,
                        0,
                        errors_dict,
                    )
                )

        table_data.sort(
            key=lambda single_question_data: tuple(
                map(
                    lambda data: catch_eval_exception(
                        available_models,
                        sortting_eval_function,
                        data,
                        0,
                        errors_dict,
                    ),
                    single_question_data[base_model],
                )
            )
        )
    if len(errors_dict):
        logging.error(ERROR_MESSAGE_TEMPLATE.format("sorting", errors_dict))

    return (
        get_short_info_table_layout()
        + get_general_stats_layout(base_model)
        + get_detailed_info_table_layout(
            models,
            list(
                filter(
                    is_detailed_answers_rows_key,
                    (
                        table_data[0][base_model][0].keys()
                        if len(table_data) and len(table_data[0][base_model])
                        else []
                    ),
                )
            ),
        )
    )


def get_filtered_tables_layout(
    base_model: str,
    filtering_function: str,
    apply_on_filtered_data: bool,
    models: List[str],
    filter_mode: str,
) -> List[html.Tr]:
    global table_data
    clean_table_data = []
    if not apply_on_filtered_data:
        table_data = custom_deepcopy(get_data_from_files())
        for question_id in range(len(table_data)):
            for model_id, files_data in table_data[question_id].items():
                stats = get_metrics(files_data)
                table_data[question_id][model_id] = list(
                    map(
                        lambda data: {**data, **stats},
                        table_data[question_id][model_id],
                    )
                )

    errors_dict = {}
    if filtering_function:
        available_models = {
            model_name: model_info["file_paths"]
            for model_name, model_info in get_available_models().items()
        }
        filter_lines = filtering_function.strip().split("\n")
        common_expressions, splitted_filters = (
            "\n".join(filter_lines[:-1]),
            filter_lines[-1],
        )
        full_splitted_filters = [
            common_expressions + "\n" + single_filter
            for single_filter in splitted_filters.split("&&")
        ]
        filtering_functions = (
            list(
                [
                    get_eval_function(f"{BASE_GENERATION} = '{base_model}'\n" + func)
                    for func in full_splitted_filters
                ]
            )
            if filtering_function
            else []
        )

        if filter_mode == FILES_FILTERING:
            for question_id in range(len(table_data)):
                good_data = True
                for model_id in table_data[question_id].keys():

                    def filtering_key_function(file_dict):
                        data = {model_id: file_dict}
                        return all(
                            [
                                catch_eval_exception(
                                    available_models,
                                    filter_function,
                                    data,
                                    True,
                                    errors_dict,
                                )
                                for filter_function in filtering_functions
                            ],
                        )

                    table_data[question_id][model_id] = list(
                        filter(
                            filtering_key_function,
                            table_data[question_id][model_id],
                        )
                    )
                    stats = get_metrics(table_data[question_id][model_id])
                    table_data[question_id][model_id] = list(
                        map(
                            lambda data: {**data, **stats},
                            table_data[question_id][model_id],
                        )
                    )

                    if table_data[question_id][model_id] == []:
                        good_data = False
                if good_data:
                    clean_table_data.append(table_data[question_id])
        else:
            func = get_eval_function(
                f"{BASE_GENERATION} = '{base_model}'\n" + filtering_function.strip()
            )
            clean_table_data = list(
                filter(
                    lambda data: catch_eval_exception(
                        available_models=[],
                        eval_func=func,
                        data=data,
                        default_answer=True,
                        errors_dict=errors_dict,
                    ),
                    table_data,
                )
            )
        table_data = clean_table_data
    if len(errors_dict):
        logging.error(ERROR_MESSAGE_TEMPLATE.format("filtering", errors_dict))

    return (
        get_short_info_table_layout()
        + get_general_stats_layout(base_model)
        + get_detailed_info_table_layout(
            models,
            list(
                filter(
                    is_detailed_answers_rows_key,
                    (
                        table_data[0][base_model][0].keys()
                        if len(table_data) and len(table_data[0][base_model])
                        else []
                    ),
                )
            ),
        )
    )


def get_tables_layout(base_model: str) -> List:
    get_table_data().extend(custom_deepcopy(get_data_from_files()))
    return (
        get_short_info_table_layout()
        + get_general_stats_layout(base_model)
        + get_detailed_info_table_layout(
            [base_model],
            list(
                filter(
                    is_detailed_answers_rows_key,
                    (
                        get_table_data()[0][base_model][0].keys()
                        if len(get_table_data()) and len(get_table_data()[0][base_model])
                        else []
                    ),
                )
            ),
        )
    )
