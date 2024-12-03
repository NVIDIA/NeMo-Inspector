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

from typing import Dict, List

import dash_bootstrap_components as dbc
from dash import html

from nemo_inspector.settings.constants import TEMPLATES_BASED, SEPARATOR_ID
from nemo_inspector.utils.common import get_dataset_sample
from nemo_inspector.inference_page_strategies.base_strategy import ModeStrategies


class TemplateBasedModeStrategy(ModeStrategies):
    mode = TEMPLATES_BASED

    def __init__(self):
        super().__init__()

    def get_utils_input_layout(self) -> List[dbc.AccordionItem]:
        return super().get_utils_input_layout(disabled=True)

    def get_query_input_layout(self, dataset: str) -> List[dbc.AccordionItem]:
        return super().get_query_input_layout(get_dataset_sample(0, dataset)[0])

    def run(self, utils: Dict, params: Dict) -> html.Div:
        utils = {key.split(SEPARATOR_ID)[-1]: value for key, value in utils.items()}
        params["prompts"] = [self.get_prompt(utils, params)]
        return super().run(utils, params)
