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
import pickle
import time

from alphafold.data import parsers

from . import custom_job_remote_runner
from . import utils


RUNNER_SCRIPT = '/scripts/alphafold_runners/hhsearch_runner.py'

def run_hhsearch(
    project,
    location,
    params,
    gcp_resources,
    executor_input,
    runners_image,
):
    logging.info('Starting HHsearch runner')

    params = json.loads(params)
    ref_databases = utils.get_artifact(executor_input, 'ref_databases')
    msa = utils.get_artifact(executor_input, 'msa')

    if not ref_databases:
        raise ValueError('No metadata for ref_databases artifact')

    template_dbs_paths = []
    for database in params['template_dbs']:
        template_dbs_paths.append(ref_databases['metadata'][database])

    template_dbs_paths = ','.join(template_dbs_paths)
    nfs_server, nfs_root_path, mount_path, network = ref_databases['uri'].split(',')
    env_variables = {
        'SEQUENCE_PATH': params['sequence_path'],
        'MSA_PATH': params['msa_path'],
        'MSA_DATA_FORMAT': msa['metadata']['Data format'],
        'TEMPLATE_HITS_PATH': params['template_hits_path'],
        'TEMPLATE_FEATURES_PATH': params['template_features_path'],
        'MMCIF_PATH': ref_databases['metadata'][params['mmcif_db']],
        'OBSOLETE_PATH': ref_databases['metadata'][params['obsolete_db']],
        'DB_ROOT': mount_path,
        'TEMPLATE_DBS_PATHS': template_dbs_paths,
        'MAXSEQ': params['maxseq'],
        'MAX_TEMPLATE_HITS': params['max_template_hits'],
        'MAX_TEMPLATE_DATE': params['max_template_date'],
    }
    display_name = f'HHSEARCH_JOB_{time.strftime("%Y%m%d_%H%M%S")}'
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
    artifacts = []
    with  open(params["template_hits_path"], 'r') as f:
        hhr = f.read()
    hhr = parsers.parse_hhr(hhr)
    metadata = {}
    metadata['Number of hits'] = len(hhr)
    metadata['Data format'] = 'hhr'
    artifacts.append(dict(name='template_hits', metadata=metadata))
    metadata = {}
    metadata['Data format'] = 'pkl'
    artifacts.append(dict(name='template_features', metadata=metadata))
    utils.update_output_artifacts(
        executor_input=executor_input,
        artifacts_to_update=artifacts
    )
    






    