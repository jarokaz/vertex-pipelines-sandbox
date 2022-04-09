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
import sys
import time

from absl import flags
from absl import app
from absl import logging

FLAGS = flags.FLAGS

flags.DEFINE_integer('sleep_time', 20, 'Sleep time in seconds')


def _main(argv):
    logging.info(f'Sleeping for {FLAGS.sleep_time} seconds')
    time.sleep(FLAGS.sleep_time)
    logging.info('Done sleeping. Going home')
    
if __name__ == "__main__":
    app.run(_main)
    
    
    