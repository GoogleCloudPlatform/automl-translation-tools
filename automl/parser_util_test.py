# -*- coding: utf-8 -*-
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

import StringIO
import unittest

from automl import parser_util

_VALID_TSV = u"""Hello World\t你好世界
How are you\t你好吗
""".encode('utf-8')

_VALID_TMX = u"""<?xml version="1.0" encoding="UTF-8" ?>
<tmx version="1.4">
<header srclang="en"
        adminlang="en-us"
        o-tmf="unknown"
        segtype="sentence"
        creationtool="Uplug"
        creationtoolversion="unknown"
        datatype="PlainText" />
  <body>
    <note>This is note</note>
    # anything outside tag is ignored.
    <tu>
      <tuv xml:lang="en"><seg>Hello World</seg></tuv>
      <tuv xml:lang="zh"><seg>你好</seg><prop>PPP</prop><seg>世界</seg></tuv>
    </tu>
  </body>
</tmx>
""".encode('utf-8')

_VALID_RKV = u"""sl=en\ttl=zh\tquery=Hello World\treferences=你好世界
sl=en\ttl=zh\tquery=How are you\treferences=你好吗
""".encode('utf-8')


_TMX_WITH_ERRORS = u"""<?xml version="1.0" encoding="UTF-8" ?>
<tmx version="1.4">
<header srclang="en"
        adminlang="en-us"
        segtype="sentence"
        datatype="PlainText" />
  <body>
    <note>This sentence pair is valid</note>
    <tu>
      <tuv xml:lang="zh"><seg>你好世界</seg></tuv>
      <tuv xml:lang="en"><seg>Hello World</seg></tuv>
    </tu>

    # error: a tu w/o content
    <tu></tu>

    # error: a tu w/o content
    <tu>
      <tuv xml:lang="en"></tuv>
    </tu>

    # error: unexpected sentence pair
    <tu>
      <tuv xml:lang="ja"><seg>so ni</seg></tuv>
      <tuv xml:lang="ko"><seg>o ba</seg></tuv>
    </tu>

    # error: no sentence in source language
    <tu>
      <tuv xml:lang="zh"><seg>你好</seg></tuv>
      <tuv xml:lang="ko"><seg>o ba</seg></tuv>
      <tuv xml:lang="ja"><seg>yo xi</seg></tuv>
    </tu>

    # error: no sentence in target language
    <tu>
      <tuv xml:lang="en"><seg>brother</seg></tuv>
      <tuv xml:lang="zh"><seg></seg></tuv>
    </tu>

    # error: no sentence in target language
    <tu>
      <tuv xml:lang="en"><seg>world</seg></tuv>
      <tuv><seg>世界</seg></tuv>
    </tu>

  </body>
</tmx>
""".encode('utf-8')


class ParserUtilTest(unittest.TestCase):

  def test_parse_and_export_valid_tsv_tmx(self):
    tsv_input_stream1 = StringIO.StringIO(_VALID_TSV)
    tmx_output_stream1 = StringIO.StringIO()
    tsv_parser1 = parser_util.TsvParser('en', 'zh', tsv_input_stream1)
    tmx_exporter1 = parser_util.TmxExporter('en', 'zh', tmx_output_stream1)
    self._convert(tsv_parser1, tmx_exporter1)
    tmx_output1 = tmx_output_stream1.getvalue()

    tmx_input_stream2 = StringIO.StringIO(tmx_output1)
    tsv_output_stream2 = StringIO.StringIO()
    tmx_parser2 = parser_util.TmxParser('en', 'zh', tmx_input_stream2)
    tsv_exporter2 = parser_util.TsvExporter('en', 'zh', tsv_output_stream2)
    self._convert(tmx_parser2, tsv_exporter2)

    tsv_output_stream2.seek(0)
    tmx_output_stream3 = StringIO.StringIO()
    tsv_parser3 = parser_util.TsvParser('en', 'zh', tsv_output_stream2)
    tmx_exporter3 = parser_util.TmxExporter('en', 'zh', tmx_output_stream3)
    self._convert(tsv_parser3, tmx_exporter3)
    tmx_output3 = tmx_output_stream1.getvalue()
    self.assertEqual(tmx_output1, tmx_output3)

  def test_parse_empty_tsv(self):
    tsv_input_stream1 = StringIO.StringIO('')
    tmx_output_stream1 = StringIO.StringIO()
    tsv_parser1 = parser_util.TsvParser('en', 'zh', tsv_input_stream1)
    tmx_exporter1 = parser_util.TmxExporter('en', 'zh', tmx_output_stream1)
    self._convert(tsv_parser1, tmx_exporter1)

    tmx_output_stream1.seek(0)
    tsv_output_stream2 = StringIO.StringIO()
    tmx_parser2 = parser_util.TmxParser('en', 'zh', tmx_output_stream1)
    tsv_exporter2 = parser_util.TsvExporter('en', 'zh', tsv_output_stream2)
    self._convert(tmx_parser2, tsv_exporter2)
    self.assertEqual(tsv_output_stream2.getvalue(), '')

  def test_parse_and_export_valid_tmx_tsv(self):
    tmx_input_stream1 = StringIO.StringIO(_VALID_TMX)
    tsv_output_stream1 = StringIO.StringIO()
    tmx_parser1 = parser_util.TmxParser('en', 'zh', tmx_input_stream1)
    tsv_exporter1 = parser_util.TsvExporter('en', 'zh', tsv_output_stream1)
    self._convert(tmx_parser1, tsv_exporter1)
    tsv_output1 = tsv_output_stream1.getvalue()

    tsv_input_stream2 = StringIO.StringIO(tsv_output1)
    tmx_output_stream2 = StringIO.StringIO()
    tsv_parser2 = parser_util.TsvParser('en', 'zh', tsv_input_stream2)
    tmx_exporter2 = parser_util.TmxExporter('en', 'zh', tmx_output_stream2)
    self._convert(tsv_parser2, tmx_exporter2)

    tmx_output_stream2.seek(0)
    tsv_output_stream3 = StringIO.StringIO()
    tmx_parser3 = parser_util.TmxParser('en', 'zh', tmx_output_stream2)
    tsv_exporter3 = parser_util.TsvExporter('en', 'zh', tsv_output_stream3)
    self._convert(tmx_parser3, tsv_exporter3)
    tsv_output3 = tsv_output_stream3.getvalue()
    self.assertEqual(tsv_output1, tsv_output3)

  def test_parse_valid_tsv(self):
    tsv_input_stream1 = StringIO.StringIO(_VALID_TSV)
    tsv_parser1 = parser_util.TsvParser('en', 'zh', tsv_input_stream1)
    pair1, pair2 = list(tsv_parser1)
    self.assertEqual(pair1, ('Hello World', u'你好世界'))
    self.assertEqual(pair2, ('How are you', u'你好吗'))

  def test_parse_valid_tmx(self):
    tmx_input_stream1 = StringIO.StringIO(_VALID_TMX)
    tmx_parser1 = parser_util.TmxParser('en', 'zh', tmx_input_stream1)
    pair, = list(tmx_parser1)
    self.assertEqual(pair, ('Hello World', u'你好 世界'))

  def _convert(self, parser, exporter):
    with exporter:
      for src, dst in parser:
        exporter.feed_parallel_phrase_pair(src, dst)

  def test_invalid_tmx(self):
    tmx_input_stream = StringIO.StringIO("""<tmx><tu></tu></tmx>""")
    tmx_parser = parser_util.TmxParser('en', 'zh', tmx_input_stream)

    with self.assertRaisesRegexp(
        parser_util.InvalidFileFormatError,
        r'Invalid TMX file at line 1: Invalid tag structure'):
      list(tmx_parser)

  def test_parse_tmx_with_error_no_skip(self):
    tmx_input = StringIO.StringIO(_TMX_WITH_ERRORS)
    tmx_parser = parser_util.TmxParser('en', 'zh', tmx_input)
    with self.assertRaisesRegexp(
        parser_util.InvalidFileFormatError,
        r'No sentence found in source and target languages'):
      list(tmx_parser)

if __name__ == '__main__':
  unittest.main()