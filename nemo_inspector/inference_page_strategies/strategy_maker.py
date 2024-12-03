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

from typing import Optional

from nemo_inspector.settings.constants import PROMPT_BASED, TEMPLATES_BASED
from nemo_inspector.inference_page_strategies.base_strategy import ModeStrategies
from nemo_inspector.inference_page_strategies.prompt_based import PromptBasedStrategy
from nemo_inspector.inference_page_strategies.template_based import (
    TemplateBasedModeStrategy,
)


class RunPromptStrategyMaker:
    strategies = {
        TEMPLATES_BASED: TemplateBasedModeStrategy,
        PROMPT_BASED: PromptBasedStrategy,
    }

    def __init__(self, mode: Optional[str] = None):
        self.mode = mode

    def get_strategy(self) -> ModeStrategies:
        return self.strategies.get(self.mode, ModeStrategies)()
