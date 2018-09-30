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

import mock
import os
import unittest

from automl import autosplit as autosplit_util

_VALID_TSV = '\n'.join(['source_{}\ttarget'.format(i) for i in range(100)])


def _tmp_file(filename):
  return os.path.join(os.environ['TEST_TMPDIR'], filename)


def _get_line_count(filename):
  with open(_tmp_file(filename), 'r') as f:
    return len([line for line in f if line.strip()])


def _write_tmp_file(filename, content):
  with open(_tmp_file(filename), 'w') as f:
    f.write(content)

class AutoSplitUtilTest(unittest.TestCase):

  def test_auto_split_util(self):
    _write_tmp_file('source.tsv', _VALID_TSV)
    autosplit = autosplit_util.AutoSplitUtil(
        source_lang_code='en',
        target_lang_code='zh',
        total_size=100,
        input_paths=[_tmp_file("source.tsv")])
    autosplit.autosplit(
      _tmp_file('target_train.tsv'),
      _tmp_file('target_validation.tsv'),
      _tmp_file('target_test.tsv'))
    self.assertEqual(_get_line_count('target_train.tsv'), 80)
    self.assertEqual(_get_line_count('target_validation.tsv'), 10)
    self.assertEqual(_get_line_count('target_test.tsv'), 10)


if __name__ == '__main__':
  unittest.main()