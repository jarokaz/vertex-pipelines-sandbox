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
import logging
import os
import time

from alphafold.data import parsers

from . import custom_job_remote_runner
from . import utils


RUNNER_SCRIPT = '/scripts/alphafold_runners/hhblits_runner.py'
SUPPORTED_DATABASES = ['bfd', 'uniclust30']

def run_hhblits(
    project,
    location,
    params,
    gcp_resources,
    executor_input,
    runners_image,
):
    logging.info('Starting HHBlits runner')

    params = json.loads(params)
    ref_databases = utils.get_artifact(executor_input, 'ref_databases')
    if not ref_databases:
        raise ValueError('No metadata for ref_databases artifact')

    db_paths = []
    for database in params['databases']:
        if not (database in SUPPORTED_DATABASES):
            raise RuntimeError(f'HHBlits cannot be used with {database} database.')
        db_paths.append(ref_databases['metadata'][database])

    db_paths = ','.join(db_paths)

    nfs_server, nfs_root_path, mount_path, network = ref_databases['uri'].split(',')
    env_variables = {
        'INPUT_PATH': params['sequence_path'],
        'MSA_PATH': params['msa_path'],
        'DB_ROOT': mount_path,
        'DB_PATHS': db_paths,
        'N_CPU': params['n_cpu'],
        'MAXSEQ': params['maxseq']
    }
    display_name = f'HHBLITS_JOB_{time.strftime("%Y%m%d_%H%M%S")}'
    custom_job_spec = utils.create_custom_job_spec_for_runner(
        display_name=display_name,
        script_path=RUNNER_SCRIPT,
        machine_type=params['machine_type'],
        container_uri=runners_image,
        env_variables=env_variables,
        network=network,
        nfs_server=nfs_server,
        nfs_root_path=nfs_root_path,
        mount_path=mount_path
    )

    custom_job_remote_runner.create_custom_job(
        project,
        location,
        custom_job_spec,
        gcp_resources
    )

   # Update output artifacts
    with  open(params["msa_path"], 'r') as f:
        msa = f.read()
    msa = parsers.parse_a3m(msa)
    metadata = {}
    metadata['Number of sequences'] = len(msa)
    metadata['Data format'] = 'a3m'
    utils.update_output_artifacts(
        executor_input=executor_input,
        artifacts_to_update=[dict(name='msa', metadata=metadata)]
    )





    