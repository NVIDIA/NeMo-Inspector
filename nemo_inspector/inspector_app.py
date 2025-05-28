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

import sys
from pathlib import Path
import signal
import argparse
import dataclasses

from nemo_skills.utils import setup_logging
from nemo_skills.prompt.utils import PromptConfig

from nemo_inspector.parse_agruments_helpers import (
    add_arguments_from_dataclass,
    args_postproccessing,
    convert_to_nested_dict,
    create_dataclass_from_args,
    args_preproccessing,
)

sys.path.append(str(Path(__file__).parents[1]))

from nemo_inspector.layouts import get_main_page_layout

from nemo_inspector.settings.inspector_config import InspectorConfig


def main():
    setup_logging(disable_hydra_logs=False)

    signal.signal(signal.SIGALRM, signal.SIG_IGN)

    parser = argparse.ArgumentParser(description="NeMo Inspector")

    add_arguments_from_dataclass(
        parser,
        InspectorConfig,
        enforce_required=False,
        use_type_defaults=True,
    )

    add_arguments_from_dataclass(
        parser,
        PromptConfig,
        prefix="prompt.",
        use_default=argparse.SUPPRESS,
        enforce_required=False,
        use_type_defaults=True,
    )

    args = parser.parse_args()
    args_dict = vars(args)
    args_dict = args_preproccessing(args_dict)

    cfg = dataclasses.asdict(create_dataclass_from_args(InspectorConfig, args_dict))
    cfg["prompt"] = convert_to_nested_dict(args_dict).get("prompt", {})
    cfg = args_postproccessing(cfg)

    from nemo_inspector.callbacks import app

    app.server.config.update({"nemo_inspector": cfg})
    app.title = "NeMo Inspector"
    app.layout = get_main_page_layout()
    app.run(
        host="localhost",
        port="8080",
    )


if __name__ == "__main__":
    main()
