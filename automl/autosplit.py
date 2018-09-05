# Copyright 2018 Google LLC
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

import enum
import math
import random

from automl import parser_util


class MLUse(enum.IntEnum):
  """An enum for possible ML usecases."""

  UNASSIGNED = 0  # Not used for preprocessing. Should not occur.
  TRAIN = 1  # For training
  VALIDATION = 2  # For eval during training
  TEST = 3  # Holdout set


_ML_USES = (MLUse.TRAIN, MLUse.VALIDATION, MLUse.TEST)


def _autosplit_example_count(total_example_count):
  """Gets autosplit example counts group by ml_use.

  Args:
    total_example_count: int
  Returns:
    Dict[ml_use.MLUse, int]
  """
  train_example_count = int(math.ceil(total_example_count * 0.8))
  validation_example_count = int(
    math.ceil(total_example_count * 0.9 - train_example_count))
  test_example_count = (
      total_example_count - validation_example_count - train_example_count)
  return {
    MLUse.TRAIN: train_example_count,
    MLUse.VALIDATION: validation_example_count,
    MLUse.TEST: test_example_count,
  }


class AutoSplitUtil(object):
  """Util to do auto split."""

  def __init__(self, source_lang_code, target_lang_code,
               total_size, input_paths):
    """Initializes AutoSplitUtil.

    Args:
      source_lang_code: String - BCP 47 language code
      target_lang_code: String - BCP 47 language code.
      total_size: int
      input_paths: [String]
    """
    self._source_lang_code = source_lang_code
    self._target_lang_code = target_lang_code
    self._example_counts = _autosplit_example_count(total_size)
    self._input_paths = input_paths

  def _assign_ml_use(self):
    """Randomly assign a example type with current split ratio."""
    # Generate a random number between [0, total_size)
    example_index = random.randint(0, sum(self._example_counts.values()) - 1)
    int(random.random() * sum(self._example_counts.values()))

    for ml_use_value in _ML_USES:
      if example_index < self._example_counts[ml_use_value]:
        return ml_use_value
      example_index -= self._example_counts[ml_use_value]
    return MLUse.TRAIN

  def _select_ml_use(self, ml_use_value):
    """Update the ml_use count which will update the split ratio."""
    self._example_counts[ml_use_value] -= 1

  def _create_exporter(self, file_path, output_stream):
    return parser_util.create_exporter(
      file_path=file_path,
      src_lang_code=self._source_lang_code,
      dst_lang_code=self._target_lang_code,
      output_stream=output_stream)

  def autosplit(self, train_output_path, validation_output_path, test_output_path):
    """Autosplits dataset and save to 3 files.

    Args:
      train_output_path: String
      validation_output_path: String
      test_output_path: String
    """
    with open(train_output_path, 'w') as train_output_stream, open(validation_output_path,
                                                                   'w') as validation_output_stream, open(
      test_output_path, 'w') as test_output_stream:
      exporters = {
        MLUse.TRAIN:
          self._create_exporter(train_output_path, train_output_stream),
        MLUse.VALIDATION:
          self._create_exporter(validation_output_path, validation_output_stream),
        MLUse.TEST:
          self._create_exporter(test_output_path, test_output_stream),
      }
      for exporter in exporters.values():
        exporter.initialize()
      for input_path in self._input_paths:
        with open(input_path) as input_stream:
          parser = parser_util.create_parser(
            file_path=input_path,
            src_lang_code=self._source_lang_code,
            dst_lang_code=self._target_lang_code,
            input_stream=input_stream)
          for src_text, dst_text in parser:
            ml_use_value = self._assign_ml_use()
            exporters[ml_use_value].feed_parallel_phrase_pair(
              src_text, dst_text)
            self._select_ml_use(ml_use_value)
      for exporter in exporters.values():
        exporter.finalize()


def autosplit(input_file_paths,
              src_lang_code,
              dst_lang_code,
              train_output_path,
              validation_output_path,
              test_output_path):
  total_count = parser_util.iterate_parallel_phrases(input_file_paths=input_file_paths,
                                                     src_lang_code=src_lang_code,
                                                     dst_lang_code=dst_lang_code)
  autosplit_util = AutoSplitUtil(source_lang_code=src_lang_code,
                                 target_lang_code=dst_lang_code,
                                 total_size=total_count,
                                 input_paths=input_file_paths)
  autosplit_util.autosplit(train_output_path=train_output_path,
                           validation_output_path=validation_output_path,
                           test_output_path=test_output_path)
