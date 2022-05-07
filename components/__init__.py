import os

try:
  from kfp.v2.components import load_component_from_file
except ImportError:
  from kfp.components import load_component_from_file

__all__ = [
    'TestTaskOp',
],

TestTaskOp = load_component_from_file(
        os.path.join(os.path.dirname(__file__),  'test_task.yaml'))

TestTaskOp3 = load_component_from_file(
        os.path.join(os.path.dirname(__file__),  'test_task1.yaml'))


from .test_op1 import run_task1 as TestTaskOp1
