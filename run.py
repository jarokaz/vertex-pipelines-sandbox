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
import random
from re import I
import sys

from absl import flags
from absl import app

import google.cloud.aiplatform as aip


_PIPELINE_JOB_NAME = 'job-control'

FLAGS = flags.FLAGS

flags.DEFINE_string('pipeline_spec', 'job-control.json', 'Path to pipeline spec')
flags.DEFINE_string('pipeline_staging_location', 'gs://jk-vertex-us-central1/pipelines', 'Vertex AI staging bucket')
flags.DEFINE_string('project', 'jk-mlops-dev', 'GCP Project')
flags.DEFINE_string('region', 'us-central1', 'GCP Region')
flags.DEFINE_string('vertex_sa', 'training-sa@jk-mlops-dev.iam.gserviceaccount.com', 'Vertex SA')
flags.DEFINE_string('pipelines_sa', 'pipelines-sa@jk-mlops-dev.iam.gserviceaccount.com', 'Pipelines SA')
flags.DEFINE_bool('enable_caching', False, 'Caching control')

def _main(argv):

    params = {
    }

    pipeline_job = aip.PipelineJob(
        display_name=_PIPELINE_JOB_NAME,
        template_path=FLAGS.pipeline_spec,
        pipeline_root=f'{FLAGS.pipeline_staging_location}/{_PIPELINE_JOB_NAME}',
        parameter_values=params,
        enable_caching=FLAGS.enable_caching,

    )

    pipeline_job.run(
        service_account=FLAGS.pipelines_sa
        
    )


if __name__ == "__main__":
    app.run(_main)
