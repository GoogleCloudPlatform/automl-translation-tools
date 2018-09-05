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

import os

from absl import app
from absl import flags
from absl import logging
from builtins import input

from automl import autosplit
from automl import parser_util

FLAGS = flags.FLAGS
flags.DEFINE_enum('cmd', None, ['validate', 'autosplit', 'convert', 'count'], 'The command to run.')
flags.DEFINE_multi_string('input_files', None, 'The input files')
flags.DEFINE_string('src_lang_code', None, 'The source language.')
flags.DEFINE_string('dst_lang_code', None, 'The target language.')
flags.DEFINE_string('output_file', None, 'The output file.')
flags.DEFINE_string('train_dataset', None, 'The path of train dataset.')
flags.DEFINE_string('validation_dataset', None, 'The path of validation dataset.')
flags.DEFINE_string('test_dataset', None, 'The path of test dataset.')

# Required flag.
flags.mark_flag_as_required('cmd')
flags.mark_flag_as_required('input_files')
flags.mark_flag_as_required('src_lang_code')
flags.mark_flag_as_required('dst_lang_code')


def _get_input_files():
  return set([os.path.expanduser(path) for path in FLAGS.input_files])


def _get_output_file():
  if not FLAGS.output_file:
    return None
  return os.path.expanduser(FLAGS.output_file)


def _assert_flag_not_none(command, flag_name, flag_value):
  if not flag_value:
    logging.fatal('Flag `%s` is required in command `%s`.', flag_name, command)


def command_validate():
  """Validates whether the input file is correct or not."""
  parser_util.iterate_parallel_phrases(input_file_paths=_get_input_files(),
                                       src_lang_code=FLAGS.src_lang_code,
                                       dst_lang_code=FLAGS.dst_lang_code)
  logging.info('Input files are valid.')


def command_convert():
  """Converts the file between tsv/tmx."""
  _assert_flag_not_none('convert', 'output_file', FLAGS.output_file)
  parser_util.convert_input_files(input_file_paths=_get_input_files(),
                                  output_file_path=_get_output_file(),
                                  src_lang_code=FLAGS.src_lang_code,
                                  dst_lang_code=FLAGS.dst_lang_code)


def command_count():
  total_count = parser_util.iterate_parallel_phrases(input_file_paths=_get_input_files(),
                                                     src_lang_code=FLAGS.src_lang_code,
                                                     dst_lang_code=FLAGS.dst_lang_code)
  logging.info('Total parallel phrases count: %d.', total_count)


def command_autosplit():
  """Autosplit input file into `train`, `validate` and `test` dataset."""
  _assert_flag_not_none('autosplit', 'train_dataset', FLAGS.train_dataset)
  _assert_flag_not_none('autosplit', 'validation_dataset', FLAGS.validation_dataset)
  _assert_flag_not_none('autosplit', 'test_dataset', FLAGS.test_dataset)
  input('Warning: This autosplit feature will randomly split the dataset. It may produce unreliable training result. '
        'Press enter to acknowledge the risk.')
  autosplit.autosplit(input_file_paths=_get_input_files(),
                      src_lang_code=FLAGS.src_lang_code,
                      dst_lang_code=FLAGS.dst_lang_code,
                      train_output_path=os.path.expanduser(FLAGS.train_dataset),
                      validation_output_path=os.path.expanduser(FLAGS.validation_dataset),
                      test_output_path=os.path.expanduser(FLAGS.test_dataset))


def main(argv):
  del argv  # Unused.
  cmd_key = 'command_{}'.format(FLAGS.cmd)
  cmd_func = globals().get(cmd_key, None)
  if not cmd_func:
    logging.fatal('Command `%s` is not supported.', FLAGS.cmd)
  cmd_func()

if __name__ == '__main__':
  app.run(main)