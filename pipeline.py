# Copyright 2021 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import json
import time


from absl import flags
from absl import app
from typing import Any, Mapping, MutableMapping, Optional, Sequence, Union, List

from kfp.v2 import dsl
from kfp.v2 import compiler
from kfp import components

from components.jackhmmer import JackhmmerOp

PIPELINE_NAME = 'pipeline-2'
PIPELINE_DESCRIPTION = 'job control'
PROJECT_ID = 'jk-mlops-dev'
REGION = 'us-central1'


@dsl.pipeline(PIPELINE_NAME, description=PIPELINE_DESCRIPTION)
def pipeline():
    
    task = JackhmmerOp(
            project=PROJECT_ID,
            location=REGION,
        )
    

def _main(argv):
    compiler.Compiler().compile(
        pipeline_func=pipeline,
        package_path=f'{PIPELINE_NAME}.json')


if __name__ == "__main__":
    app.run(_main)
    

