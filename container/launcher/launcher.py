# Copyright 2021 The Kubeflow Authors. All Rights Reserved.
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
"""Launcher client to launch jobs for various job types."""

import argparse
import json
import logging
import os
import sys
import time

#from . import jackhmmer 
#from . import hhblits
#from . import hhsearch 
#from . import hmmsearch
#from . import data_pipeline
from . import test_task

_TASK_TYPE_MAP = {
#    'Jackhmmer': jackhmmer.run_jackhmmer,
#    'HHblits': hhblits.run_hhblits,
#    'HHsearch': hhsearch.run_hhsearch,
#    'Hmmsearch': hmmsearch.run_hmmsearch,
#    'DataPipeline': data_pipeline.run_data_pipeline,
    'TestTask': test_task.run_task
}

def _make_parent_dirs_and_return_path(file_path: str):
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    return file_path


def _parse_args(args):
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        prog='AlphaFold components remote launcher', description='Launches AlphaFold components using remote Vertex Training jobs')
    parser.add_argument(
      '--task', dest='task', type=str, required=True, default=argparse.SUPPRESS)
    parser.add_argument(
        '--project',
        dest='project',
        type=str,
        required=True,
        default=argparse.SUPPRESS)
    parser.add_argument(
        '--location',
        dest='location',
        type=str,
        required=True,
        default=argparse.SUPPRESS)
    parser.add_argument(
        '--params',
        dest='params',
        type=str,
        required=True,
        default=argparse.SUPPRESS)
    parser.add_argument(
        '--gcp_resources',
        dest='gcp_resources',
        type=_make_parent_dirs_and_return_path,
        required=True,
        default=argparse.SUPPRESS)
    parser.add_argument(
        '--executor_input',
        dest='executor_input',
        type=str,
        default=argparse.SUPPRESS)
    parser.add_argument(
        '--runners_image',
        dest='runners_image',
        type=str,
        default=argparse.SUPPRESS)
    parsed_args, _ = parser.parse_known_args(args)
  
    return vars(parsed_args)


def main(argv):
    """Main entry.
    Expected input args are as follows:
        Project - Required. The project of which the resource will be launched.
        Region - Required. The region of which the resource will be launched.
        Task - Required. GCP launcher is a single container. This Enum will
            specify which resource to be launched.
        Request payload - Required. The full serialized json of the resource spec.
            Note this can contain the Pipeline Placeholders.
        gcp_resources - placeholder output for returning job_id.
    Args:
        argv: A list of system arguments.
    """
    parsed_args = _parse_args(argv)
    task_type = parsed_args.pop('task')

    if task_type not in _TASK_TYPE_MAP:
        raise ValueError(f'Unsupported task type: {task_type}')

    logging.info(f'Executing task: {task_type}')
    _TASK_TYPE_MAP[task_type](**parsed_args)


if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s - %(message)s',
                      level=logging.INFO, 
                      datefmt='%d-%m-%y %H:%M:%S',
                      stream=sys.stdout)

    main(sys.argv[1:])