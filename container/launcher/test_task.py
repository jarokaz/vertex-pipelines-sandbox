# Copyright 2022 Google LLC
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
"""A Python wrapper around dsub."""


import json
import time

from absl import flags
from absl import app
from absl import logging

from . import custom_job_remote_runner
from . import utils

FLAGS = flags.FLAGS
RUNNER_SCRIPT = '/app/task.py'

def _main(argv):
    logging.info('Starting Test runner')

    env_variables = {
        'SLEEP_TIME': FLAGS.sleep_time,
    }
    display_name = f'TEST_JOB_{time.strftime("%Y%m%d_%H%M%S")}'
    custom_job_spec = utils.create_custom_job_spec_for_runner(
        display_name=display_name,
        script_path=RUNNER_SCRIPT,
        machine_type=FLAGS.machine_type,
        container_uri=FLAGS.runners_image,
        env_variables=env_variables,
    )

    custom_job_remote_runner.create_custom_job(
        FLAGS.project,
        FLAGS.location,
        custom_job_spec,
        utils.make_parent_dirs_and_return_path(FLAGS.gcp_resources)
    )

flags.DEFINE_string('project', None, 'GCP Project')
flags.DEFINE_string('location', None, 'GCP Region')
flags.DEFINE_string('machine_type', None, 'Machine type')
flags.DEFINE_string('executor_input', None, 'Executor input')
flags.DEFINE_string('runners_image', None, 'Docker image to run AlphaFold runner')
flags.DEFINE_string('gcp_resources', None, 'GCP resources path')
flags.DEFINE_integer('sleep_time', None, 'Sleep time')

if __name__ == '__main__':
    app.run(_main)





    