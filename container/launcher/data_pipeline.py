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



RUNNER_SCRIPT = '/scripts/alphafold_runners/data_pipeline_runner.py'
METDATA_FILE_SUFFIX = '_metadata.json'

def run_data_pipeline(
    project,
    location,
    params,
    gcp_resources,
    executor_input,
    runners_image,
):
    logging.info('Starting data pipeline runner')
    params = json.loads(params)
    ref_databases = utils.get_artifact(executor_input, 'ref_databases')
    if not ref_databases:
        raise ValueError('No metadata for ref_databases artifact')

    nfs_server, nfs_root_path, mount_path, network = ref_databases['uri'].split(',')
    uniref90_database_path = os.path.join(mount_path, ref_databases['metadata']['uniref90'])
    mgnify_database_path = os.path.join(mount_path, ref_databases['metadata']['mgnify'])
    uniclust30_database_path = os.path.join(mount_path, ref_databases['metadata']['uniclust30'])
    bfd_database_path = os.path.join(mount_path, ref_databases['metadata']['bfd'])
    small_bfd_database_path = os.path.join(mount_path, ref_databases['metadata']['small_bfd'])
    uniprot_database_path = os.path.join(mount_path, ref_databases['metadata']['uniprot'])
    pdb70_database_path = os.path.join(mount_path, ref_databases['metadata']['pdb70'])
    obsolete_pdbs_path = os.path.join(mount_path, ref_databases['metadata']['pdb_obsolete'])
    seqres_database_path = os.path.join(mount_path, ref_databases['metadata']['pdb_seqres'])
    mmcif_path = os.path.join(mount_path, ref_databases['metadata']['pdb_mmcif'])
    os.makedirs(params['msas_path'])

    env_variables = {
        'FASTA_PATH': params['sequence_path'],
        'MSA_OUTPUT_PATH': params['msas_path'],
        'FEATURES_OUTPUT_PATH': params['features_path'],
        'UNIREF_DATABASE_PATH': uniref90_database_path,
        'MGNIFY_DATABASE_PATH': mgnify_database_path,
        'BFD_DATABASE_PATH': bfd_database_path,
        'SMALL_BFD_DATABASE_PATH': small_bfd_database_path,
        'UNICLUST_DATABASE_PATH':uniclust30_database_path,
        'UNIPROT_DATABASE_PATH': uniprot_database_path,
        'PDB70_DATABASE_PATH': pdb70_database_path,
        'OBSOLETE_PDBS_PATH':  obsolete_pdbs_path,
        'SEQRES_DATABASE_PATH': seqres_database_path,
        'MMCIF_PATH': mmcif_path,
        'MAX_TEMPLATE_DATE': params['max_template_date'], 
    }

    if params['run_multimer_system'] == 'True':
        env_variables['RUN_MULTIMER_SYSTEM'] = 'True'
    if params['use_small_bfd'] == 'True':
        env_variables['USE_SMALL_BFD'] = 'True'

    display_name = f'ALPHAFOLD_DATA_PIPELINE_JOB_{time.strftime("%Y%m%d_%H%M%S")}'
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
    metadata = {}
    for file in os.listdir(params['msas_path']):
        with open(os.path.join(params['msas_path'], file), 'r') as f:
            artifact = f.read()
        format = file.split('.')[-1]
        if format == 'sto':
            artifact =  parsers.parse_stockholm(artifact)
        elif format == 'a3m':
            artifact = parsers.parse_a3m(artifact)
        elif format == 'hhr':
            artifact = parsers.parse_hhr(artifact)
        else:
            raise ValueError('Unknow artifact type')
        metadata[file] = len(artifact)
    artifacts.append((dict(name='msas', metadata=metadata)))

    metadata = {}
    with open(params['features_path'], 'rb') as f:
        features = pickle.load(f)
    metadata['Final (deduplicated) MSA size'] = int(features['num_alignments'][0])
    metadata['Total number of templates'] = int(features['template_domain_names'].shape[0])
    artifacts.append(dict(name='features', metadata=metadata))

    utils.update_output_artifacts(
        executor_input=executor_input,
        artifacts_to_update=artifacts
    )






    