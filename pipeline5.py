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
import google.cloud.aiplatform as aip

from components import TestTaskOp3

FLAGS = flags.FLAGS

PIPELINE_NAME = 'pipeline-2'
RUNNERS_IMAGE = 'gcr.io/jk-mlops-dev/app'

@dsl.pipeline(name=PIPELINE_NAME, description='test')
def pipeline():

    test_task = TestTaskOp3()
    
def _main(argv):
    compiler.Compiler().compile(
        pipeline_func=pipeline,
        package_path=f'{PIPELINE_NAME}.json')

    params = {
    }

    job_name = f'{PIPELINE_NAME}-{time.strftime("%Y%m%d_%H%M%S")}'
    pipeline_job = aip.PipelineJob(
        display_name=job_name,
        template_path=f'{PIPELINE_NAME}.json',
        pipeline_root=f'{FLAGS.pipeline_staging_location}/{PIPELINE_NAME}',
        parameter_values=params,
        enable_caching=FLAGS.enable_caching,

    )

    pipeline_job.run(
        service_account=FLAGS.pipelines_sa
        
    )

flags.DEFINE_string('pipeline_staging_location', 'gs://jk-vertex-us-central1/pipelines', 'Vertex AI staging bucket')
flags.DEFINE_string('project', 'jk-mlops-dev', 'GCP Project')
flags.DEFINE_string('region', 'us-central1', 'GCP Region')
flags.DEFINE_string('machine_type', 'n1-standard-8', 'Machine type')
flags.DEFINE_string('vertex_sa', 'training-sa@jk-mlops-dev.iam.gserviceaccount.com', 'Vertex SA')
flags.DEFINE_string('pipelines_sa', 'pipelines-sa@jk-mlops-dev.iam.gserviceaccount.com', 'Pipelines SA')
flags.DEFINE_bool('enable_caching', False, 'Caching control')



if __name__ == "__main__":
    app.run(_main)
    