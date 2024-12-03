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

from nemo_inspector.layouts.analyze_page_layouts.base_layout import (
    get_compare_test_layout,
    get_filtered_tables_layout,
    get_tables_layout,
    get_updated_tables_layout,
    get_sorted_tables_layout,
)
from nemo_inspector.layouts.analyze_page_layouts.utils import (
    get_stats_input,
    get_stats_text,
    get_filter_text,
)
from nemo_inspector.layouts.base_layouts import (
    get_main_page_layout,
)
from nemo_inspector.layouts.common_layouts import (
    get_selector_layout,
    get_single_prompt_output_layout,
    get_switch_layout,
    get_text_modes_layout,
)

from nemo_inspector.layouts.inference_page_layouts.utils import (
    get_input_group_layout,
    get_text_area_layout,
    get_utils_field_representation,
)
from nemo_inspector.layouts.analyze_page_layouts.table_layouts import (
    get_detailed_info_table_column,
    get_filter_modal_layout,
    get_table_column_header,
    get_detailed_info_table_row_content,
    get_single_prompt_output_layout,
    get_short_info_table_layout,
    get_detailed_info_table_content,
)
from nemo_inspector.layouts.inference_page_layouts.model_response_layout import (
    get_results_content_layout,
)
from nemo_inspector.layouts.inference_page_layouts.base_layouts import (
    get_few_shots_by_id_layout,
    get_few_shots_layout,
    get_inference_layout,
    get_query_params_layout,
    get_utils_layout,
)
