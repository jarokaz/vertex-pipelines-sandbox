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
"""Common module for launching and managing the Vertex Job resources."""

import json
import os

from typing import Optional, Dict
from google.cloud.aiplatform.utils import worker_spec_utils

def make_parent_dirs_and_return_path(file_path: str):
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    return file_path

def update_output_artifacts(executor_input: str,
                            artifacts_to_update):
    """Updates the output artifacts with the new metadata."""
    executor_input_json = json.loads(executor_input)
    executor_output = {}
    executor_output['artifacts'] = {}
    for name, artifacts in executor_input_json.get('outputs',
                                                 {}).get('artifacts',
                                                         {}).items():
        artifacts_list = artifacts.get('artifacts')
        for artifact_to_update in artifacts_to_update:
            if name == artifact_to_update['name'] and artifacts_list:
                updated_runtime_artifact = artifacts_list[0]
                if 'metadata' in artifact_to_update:
                    updated_runtime_artifact['metadata'] = artifact_to_update['metadata']
                if 'uri' in artifact_to_update:
                    updated_runtime_artifact['uri'] = artifact_to_update['uri']
                artifacts = {'artifacts': [updated_runtime_artifact]}

            executor_output['artifacts'][name] = artifacts

    os.makedirs(
          os.path.dirname(executor_input_json['outputs']['outputFile']),
          exist_ok=True)
    with open(executor_input_json['outputs']['outputFile'], 'w') as f:
        f.write(json.dumps(executor_output))


def get_artifact(executor_input: str, artifact_name: str ):
    """Retrieves artifact's uri and metadata."""
    executor_input_json = json.loads(executor_input)

    result = {} 
    for name, artifacts in executor_input_json.get('inputs',
                                                 {}).get('artifacts',
                                                         {}).items():
        artifacts_list = artifacts.get('artifacts')
        if name == artifact_name and artifacts_list:
            result['uri'] = artifacts_list[0]['uri']
            result['metadata'] = artifacts_list[0]['metadata']

    return result 


def create_custom_job_spec_for_runner(
    display_name: str,
    script_path: str,
    container_uri: str,
    env_variables: Optional[Dict[str, str]] = None,
    machine_type: str = 'n1-standard-8',
    accelerator_type: str = 'ACCELERATOR_TYPE_UNSPECIFIED',
    accelerator_count: int = 0,
    boot_disk_type: str = 'pd-ssd',
    boot_disk_size_gb: int = 100,
    network: str = None,
    nfs_server: str = None,
    nfs_root_path: str = None,
    mount_path: str = None,   
) -> Dict: 
    """Creates a custom job specification for that starts an AlphaFold runner script
    as a Vertex Training job.
    """
    
    worker_pool_specs = worker_spec_utils._DistributedTrainingSpec.chief_worker_pool(
        replica_count=1,
        machine_type=machine_type,
        accelerator_count=accelerator_count,
        accelerator_type=accelerator_type,
        boot_disk_type=boot_disk_type,
        boot_disk_size_gb=boot_disk_size_gb,
    ).pool_specs

    if nfs_server and nfs_root_path and mount_path and network:
        worker_pool_specs[0]['nfs_mounts'] = [{
            'server': nfs_server,
            'path': nfs_root_path,
            'mount_point': mount_path,
        }]
        job_spec = {
            'worker_pool_specs': worker_pool_specs,
            'network': network,
        }
    else:
        job_spec = {
            'worker_pool_specs': worker_pool_specs,
        }

    container_spec = {
        'image_uri': container_uri,
        'command': ['python3'],
        'args': [script_path],
    }
        
    if env_variables:
        env = [{'name': name, 'value': str(value)} for name, value in env_variables.items()]
        container_spec['env'] = env
        worker_pool_specs[0]['container_spec'] = container_spec

    custom_job_spec = {
        'display_name': display_name,
        'job_spec': job_spec,
    }

    return custom_job_spec 


