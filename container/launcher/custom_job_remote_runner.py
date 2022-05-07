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
import logging
import os
from os import path
import re
import sys
import time
from typing import Optional, Dict

from google.api_core import gapic_v1
import google.auth
import google.auth.transport.requests
from google.cloud import aiplatform
from google.cloud.aiplatform.utils import source_utils
from google.cloud.aiplatform.utils import worker_spec_utils
from google.cloud.aiplatform_v1.types import job_state as gca_job_state
from google_cloud_pipeline_components.proto.gcp_resources_pb2 import GcpResources
import requests
from . import execution_context

from google.protobuf import json_format

_POLLING_INTERVAL_IN_SECONDS = 60
_CONNECTION_ERROR_RETRY_LIMIT = 5

_JOB_COMPLETE_STATES = (
    gca_job_state.JobState.JOB_STATE_SUCCEEDED,
    gca_job_state.JobState.JOB_STATE_FAILED,
    gca_job_state.JobState.JOB_STATE_CANCELLED,
    gca_job_state.JobState.JOB_STATE_PAUSED,
)

_JOB_ERROR_STATES = (
    gca_job_state.JobState.JOB_STATE_FAILED,
    gca_job_state.JobState.JOB_STATE_CANCELLED,
    gca_job_state.JobState.JOB_STATE_PAUSED,
)

# Job error codes mapping can be found in:
# https://github.com/googleapis/googleapis/blob/master/google/rpc/code.proto
_JOB_USER_ERROR_CODES = (
    3,  # INVALID_ARGUMENT
    5,  # NOT_FOUND
    7, # PERMISSION_DENIED
    6,  # ALREADY_EXISTS
    9,  # FAILED_PRECONDITION
    11,  # OUT_OF_RANGE
    12,  # UNIMPLEMENTED
)


class JobRemoteRunner():
  """Common module for creating and poll jobs on the Vertex Platform."""

  def __init__(self, job_type, project, location, gcp_resources):
    """Initializes a job client and other common attributes."""
    self.job_type = job_type
    self.project = project
    self.location = location
    self.gcp_resources = gcp_resources
    self.client_options = {
        'api_endpoint': location + '-aiplatform.googleapis.com'
    }
    self.client_info = gapic_v1.client_info.ClientInfo(
        user_agent='google-cloud-pipeline-components')
    self.job_client = aiplatform.gapic.JobServiceClient(
        client_options=self.client_options, client_info=self.client_info)
    self.job_uri_prefix = f"https://{self.client_options['api_endpoint']}/v1/"
    self.poll_job_name = ''

  def check_if_job_exists(self) -> Optional[str]:
    """Check if the job already exists."""
    if path.exists(
        self.gcp_resources) and os.stat(self.gcp_resources).st_size != 0:
      with open(self.gcp_resources) as f:
        serialized_gcp_resources = f.read()
        job_resources = json_format.Parse(serialized_gcp_resources,
                                          GcpResources())
        # Resources should only contain one item.
        if len(job_resources.resources) != 1:
          raise ValueError(
              f'gcp_resources should contain one resource, found {len(job_resources.resources)}'
          )

        job_name_group = re.findall(f'{self.job_uri_prefix}(.*)', job_resources.resources[0].resource_uri)
        if not job_name_group or not job_name_group[0]:
          raise ValueError(
              'Job Name in gcp_resource is not formatted correctly or is empty.'
          )
        job_name = job_name_group[0]

        logging.info('%s name already exists: %s. Continue polling the status',
                     self.job_type, job_name)
      return job_name
    else:
      return None

  def create_job(self, custom_job_spec) -> str:
    """Creates a  Vertex custom job."""

    #  Currently as a temporary mitigation we use a REST API directly
    # as the SDK does not support NFS clause.

    parent = f'projects/{self.project}/locations/{self.location}'
    #create_job_response = self.job_client.create_custom_job(
    #        parent=parent,
    #        custom_job=custom_job_spec
    #    )
    # job_name = create_job_respone.name

    credentials, _ = google.auth.default()
    authed_session = google.auth.transport.requests.AuthorizedSession(credentials)
    job_uri = f'{self.job_uri_prefix}{parent}/customJobs'
    create_job_response = authed_session.post(job_uri, data=json.dumps(custom_job_spec))
    if create_job_response.status_code != 200:
        raise RuntimeError(f'Request failed: {create_job_response.json()}')
    job_name = create_job_response.json()['name']

    # Write the job proto to output.
    job_resources = GcpResources()
    job_resource = job_resources.resources.add()
    job_resource.resource_type = self.job_type
    job_resource.resource_uri = f'{self.job_uri_prefix}{job_name}'

    with open(self.gcp_resources, 'w') as f:
      f.write(json_format.MessageToJson(job_resources))

    return job_name

  def poll_job(self,  job_name: str):
    """Poll the job status."""
    with execution_context.ExecutionContext(
        on_cancel=lambda: self.send_cancel_request(job_name)):
      retry_count = 0
      while True:
        try:
          get_job_response = self.job_client.get_custom_job(name=job_name)
          retry_count = 0
        # Handle transient connection error.
        except ConnectionError as err:
          retry_count += 1
          if retry_count < _CONNECTION_ERROR_RETRY_LIMIT:
            logging.warning(
                'ConnectionError (%s) encountered when polling job: %s. Trying to '
                'recreate the API client.', err, job_name)
            # Recreate the Python API client.
            self.job_client = aiplatform.gapic.JobServiceClient(
                self.client_options, self.client_info)
          else:
            # TODO(ruifang) propagate the error.
            """Exit with an internal error code."""
            exit_with_internal_error(
                'Request failed after %s retries.'.format(
                    _CONNECTION_ERROR_RETRY_LIMIT))

        if get_job_response.state == gca_job_state.JobState.JOB_STATE_SUCCEEDED:
          logging.info('Get%s response state =%s', self.job_type,
                       get_job_response.state)
          return get_job_response
        elif get_job_response.state in _JOB_ERROR_STATES:
          # TODO(ruifang) propagate the error.
          if get_job_response.error.code in _JOB_USER_ERROR_CODES:
            raise ValueError(
                'Job failed with value error in error state: {}.'.format(
                    get_job_response.state))
          else:
            raise RuntimeError('Job failed with error state: {}.'.format(
                get_job_response.state))
        else:
          logging.info(
              'Job %s is in a non-final state %s.'
              ' Waiting for %s seconds for next poll.', job_name,
              get_job_response.state, _POLLING_INTERVAL_IN_SECONDS)
          time.sleep(_POLLING_INTERVAL_IN_SECONDS)

  def send_cancel_request(self, job_name: str):
    if not job_name:
      return
    creds, _ = google.auth.default(
        scopes=['https://www.googleapis.com/auth/cloud-platform'])
    if not creds.valid:
      creds.refresh(google.auth.transport.requests.Request())
    headers = {
        'Content-type': 'application/json',
        'Authorization': 'Bearer ' + creds.token,
    }
    requests.post(
        url=f'{self.job_uri_prefix}{job_name}:cancel', data='', headers=headers)


def exit_with_internal_error(error_message: str):
  """Exit with internal error code and log error with the given error message.
  This function can be used when handling non-user errors.
  """
  logging.error(error_message)
  sys.exit(13)


def create_custom_job(
    project: str,
    location: str,
    custom_job_spec: dict,
    gcp_resources: str
):
    """Starts and monitors Vertex Training custom job."""
    job_type = 'CustomJob'
    remote_runner = JobRemoteRunner(job_type, project, location, gcp_resources)
    try:
        job_name = remote_runner.check_if_job_exists()
        if job_name is None:
            job_name = remote_runner.create_job(custom_job_spec)

        # Poll custom job status until "JobState.JOB_STATE_SUCCEEDED"
        remote_runner.poll_job(job_name)
    except (ConnectionError, RuntimeError) as err:
        exit_with_internal_error(err.args[0])




