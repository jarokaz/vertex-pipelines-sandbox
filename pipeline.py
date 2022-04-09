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

from google_cloud_pipeline_components.experimental import custom_job

PIPELINE_NAME = 'job-control'
PIPELINE_DESCRIPTION = 'job control'
PROJECT_ID = 'jk-mlops-dev'
REGION = 'us-central1'
GCS_BASE_OUTPUT_DIR = 'gs://jk-vertex-us-central1/jobs'
IMAGE_URI = "gcr.io/jk-mlops-dev/job-control-test"
MACHINE_TYPE = 'n1-standard-4'
JOB_NAME = f'{PIPELINE_NAME}-{time.strftime("%Y%m%d_%H%M%S")}'


@dsl.pipeline(PIPELINE_NAME, description=PIPELINE_DESCRIPTION)
def pipeline():
    
    worker_pool_specs = {
        "machine_spec": {
            "machine_type": MACHINE_TYPE
        },
        "replica_count": 1,
        "container_spec": {
            "image_uri": IMAGE_URI,
            "args": ["--sleep_time", "120"],
        }
    }
    
    train_task = custom_job.CustomTrainingJobOp(
            project=PROJECT_ID,
            location=REGION,
            display_name=JOB_NAME,
            base_output_directory=GCS_BASE_OUTPUT_DIR,
            worker_pool_specs=worker_pool_specs,
        )
    



def _main(argv):
    compiler.Compiler().compile(
        pipeline_func=pipeline,
        package_path=f'{PIPELINE_NAME}.json')


if __name__ == "__main__":
    app.run(_main)
    

