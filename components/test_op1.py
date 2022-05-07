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
"""A component encapsulating AlphaFold model predict"""

import os

from typing import Any, Mapping, MutableMapping, Optional, Sequence, Union
from kfp.v2 import dsl
from kfp.v2.dsl import Output, Input, Artifact, Dataset, OutputPath
from typing import List, Dict 


COMPONENT_IMAGE = 'gcr.io/jk-mlops-dev/app'
@dsl.component(
    base_image=COMPONENT_IMAGE,
    output_component_file='test_opt1.json'
)
def run_task1(
    project: str,
    location: str,
    sleep_time: int,
    runners_image: str,
    gcp_resources: OutputPath(Dict), 
    machine_type: str='n1-standard-8',
):
    
    import logging
    import time

    from launcher import custom_job_remote_runner
    from launcher import utils


    logging.info('Starting Test runner')

    RUNNER_SCRIPT = '/app/task.py'
    
    env_variables = {
        'SLEEP_TIME': sleep_time,
    }
    display_name = f'TEST_JOB_{time.strftime("%Y%m%d_%H%M%S")}'
    custom_job_spec = utils.create_custom_job_spec_for_runner(
        display_name=display_name,
        script_path=RUNNER_SCRIPT,
        machine_type=machine_type,
        container_uri=runners_image,
        env_variables=env_variables,
    )

    custom_job_remote_runner.create_custom_job(
        project,
        location,
        custom_job_spec,
        gcp_resources
    )








