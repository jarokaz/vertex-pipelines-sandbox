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

from google_cloud_pipeline_components.container.v1.gcp_launcher import custom_job_remote_runner


def _make_parent_dirs_and_return_path(file_path: str):
  os.makedirs(os.path.dirname(file_path), exist_ok=True)
  return file_path


def _parse_args(args):
  """Parse command line arguments."""
  parser = argparse.ArgumentParser(
      prog='Vertex Pipelines service launcher', description='')
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
      '--gcp_resources',
      dest='gcp_resources',
      type=_make_parent_dirs_and_return_path,
      required=True,
      default=argparse.SUPPRESS)
  parsed_args, _ = parser.parse_known_args(args)
  
  return vars(parsed_args)


PIPELINE_NAME = 'job-control'
PIPELINE_DESCRIPTION = 'job control'
PROJECT_ID = 'jk-mlops-dev'
REGION = 'us-central1'
GCS_BASE_OUTPUT_DIR = 'gs://jk-vertex-us-central1/jobs'
IMAGE_URI = "gcr.io/jk-mlops-dev/test-runner"
MACHINE_TYPE = 'n1-standard-4'
JOB_NAME = f'{PIPELINE_NAME}-{time.strftime("%Y%m%d_%H%M%S")}'


def main(argv):
  """Main entry.
  Expected input args are as follows:
    Project - Required. The project of which the resource will be launched.
    Region - Required. The region of which the resource will be launched.
    Type - Required. GCP launcher is a single container. This Enum will
        specify which resource to be launched.
    Request payload - Required. The full serialized json of the resource spec.
        Note this can contain the Pipeline Placeholders.
    gcp_resources - placeholder output for returning job_id.
  Args:
    argv: A list of system arguments.
  """
  parsed_args = _parse_args(argv)
    
  display_name = f'RUNNER_TEST_JOB_{time.strftime("%Y%m%d_%H%M%S")}'

  worker_pool_specs = [
        {
            "machine_spec": {
                "machine_type": MACHINE_TYPE
            },
            "replica_count": 1,
            "container_spec": {
                "image_uri": IMAGE_URI,
                "command": ["python3", "-m", "app.task"],
                "args": ["--sleep_time", "120"],
            },
            #"nfs_mounts": [
            #    {
            #        'server': '10.6.0.2',
            #        'path': '/ref_datasets',
            #        'mount_point': '/mnt/nfs/alphafold',
            #    }
            #]
         }
  ]

  custom_job_spec = {
      'display_name': display_name,
      'job_spec': {
          'worker_pool_specs': worker_pool_specs,
       }
  }

  print(custom_job_spec)

    
  custom_job_remote_runner.create_custom_job(
      type="CustomJob",
      project=parsed_args['project'],
      location=parsed_args['location'],
      payload=json.dumps(custom_job_spec),
      gcp_resources=parsed_args['gcp_resources']
  )



if __name__ == '__main__':
  main(sys.argv[1:])
