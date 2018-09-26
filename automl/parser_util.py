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

"""Parallel sentence parsers and exporters."""
import os

from absl import logging
from lxml import etree


def _skip_invalid_tmx_data():
  return False


def _parse_locale(lang_code):
  """Parses language string to babel locale.

  Args:
    lang_code: String - language code, for example 'en', 'en-US'.
    BCP 47 is expected: https://tools.ietf.org/html/bcp47

  Returns:
    parsed locale
  """
  return lang_code.lower().split('-')[0]


def _is_same_language(locale1, locale2):
  """Compares whether two locacle is the same language."""
  return locale1 == locale2


def _try_decode(text, encoding='utf-8'):
  if isinstance(text, unicode):
    return text
  try:
    return text.decode(encoding)
  except UnicodeError as e:
    raise ValueError('Invalide encoding, expect`{}`.'.format(encoding))


def _try_encode(text, encoding='utf-8'):
  if isinstance(text, unicode):
    return text.encode(encoding)
  return text


class InvalidFileFormatError(Exception):
  """Exception throws when there is syntactic error."""

  def __init__(self, file_type, line_index, message):
    super(InvalidFileFormatError, self).__init__()
    if line_index is not None:
      self.message = 'Invalid {} file at line {}: {}'.format(
        file_type, line_index, message)
    else:
      self.message = 'Invalid {} file: {}'.format(file_type, message)

  def __str__(self):
    return self.message


class ParseFinished(Exception):
  """An exception indicate the end of stream."""
  pass


class ParallelPhraseParser(object):
  """Parser base class to parse parallel phrases.

  Subclasses should implement `next_parallel_phrase_pair` and FILE_FORMAT.
  """
  _SENTENCE_BUFFER_SIZE = 1024 * 1024

  # The max number of skipped phrases in parsing we tolerate, exceeding this
  # number fails the parsing.
  _MAX_SKIPPED_PHRASES = 1024

  FILE_FORMAT = None

  def __init__(self):
    self._line_index = 0
    self._next_read_line_index = 0
    # The list stores all skipped phrases which are considered to be invalid by
    # the parser.
    # Each item contains (line number, src_text, dst_text, error_message) so
    # that the clients can show more concrete error messages to end users.
    # Note: the src_text and dst_text can be None.
    self._skipped_phrases = []

  @property
  def current_line_number(self):
    return self._line_index + 1

  @property
  def current_skipped_phrases(self):
    return self._skipped_phrases

  def next_parallel_phrase_pair(self):
    """Parses the next parallel phrase pair.

    Returns:
      (src_text, target_text)  unicode tuple
    Raises:
      InvalidFileFormatError: If stream format is invalid.
      ParseFinished: If stream is finished.
    """
    raise NotImplementedError()

  def readline(self, stream, check_sentence_buffer=False, rstrip=True):
    """Reads one line.

    Args:
      stream: file stream.
      check_sentence_buffer: check sentence buffer if it is True.
      rstrip: strip line separator if it is True.
    Returns:
      One line or _SENTENCE_BUFFER_SIZE buffer.
    Raises:
      InvalidFileFormatError: if buffer limit exceeded.
    """
    self._line_index = self._next_read_line_index
    line = stream.readline(self._SENTENCE_BUFFER_SIZE)
    if not line:
      raise ParseFinished()
    if line.endswith('\n') or line.endswith('\n\r'):
      self._next_read_line_index += 1
      if check_sentence_buffer and len(line) == self._SENTENCE_BUFFER_SIZE:
        raise self.invalid_format_error(
          'Length of the line exceeds the {} characters limit.'.format(
            self._SENTENCE_BUFFER_SIZE))
    if rstrip:
      line = line.rstrip('\n').rstrip('\r').rstrip('\n')
    return _try_decode(line)

  def __iter__(self):
    return self

  def next(self):
    try:
      return self.next_parallel_phrase_pair()
    except ParseFinished:
      raise StopIteration()

  def invalid_format_error(self, message, show_line_index=True):
    line_index = self.current_line_number if show_line_index else None
    return InvalidFileFormatError(
      file_type=self.FILE_FORMAT, line_index=line_index, message=message)


class ParallelPhraseExporter(object):
  """Parser base class to export parallel phrases.

  Subclasses should implement `feed_parallel_phrase_pair`, `initialize` and
  `finalize` is optional.
  """

  def feed_parallel_phrase_pair(self, src, dst):
    raise NotImplementedError()

  def initialize(self):
    pass

  def finalize(self):
    pass

  def __enter__(self):
    self.initialize()
    return self

  def __exit__(self, exc_type, exc_val, exc_tb):
    self.finalize()


class TsvParser(ParallelPhraseParser):
  r"""Parser to parse tsv stream.

  Tsv format for parallel phrase:
    - No header line
    - line format: '<source_text>\t<target_text>'
  """

  FILE_FORMAT = 'TSV'

  def __init__(self, src_lang_code, dst_lang_code, input_stream):
    """Initializes `TsvParser`.

    Args:
      src_lang_code: String - source language code in BCP 47 spec.
      dst_lang_code: String - target language code in BCP 47 spec.
      input_stream: io stream - tsv stream that implemented file interface.
    """
    super(TsvParser, self).__init__()
    self._src_lang = _parse_locale(src_lang_code)
    self._dst_lang = _parse_locale(dst_lang_code)
    self._tsv_stream = input_stream

  def next_parallel_phrase_pair(self):
    line = self.readline(self._tsv_stream, check_sentence_buffer=True)
    pair = line.split('\t')
    if len(pair) != 2:
      raise self.invalid_format_error('Each line can only contains 2 phrases.')
    return tuple(pair)


class TsvExporter(ParallelPhraseExporter):
  """Exporter to export parallel phrase pair to tsv stream."""

  def __init__(self, src_lang_code, dst_lang_code, output_stream):
    """Initializes `TsvExporter`.

    Args:
      src_lang_code: String - source language code in BCP 47 spec.
      dst_lang_code: String - target language code in BCP 47 spec.
      output_stream: io stream - tsv stream that implemented file interface.
    """
    self._src_lang = _parse_locale(src_lang_code)
    self._dst_lang = _parse_locale(dst_lang_code)
    self._tsv_stream = output_stream

  def feed_parallel_phrase_pair(self, src, dst):
    line = u''.join([src, '\t', dst, '\n'])
    self._tsv_stream.write(_try_encode(line))


class TmxParser(ParallelPhraseParser):
  """TMX parser that skips invalid phrases and unsupported tmx formats.

  Currently, parser can parse the subset of tmx spec.
  <tmx> element is required and should wrap all the content.
  <header> is required. It should be the first element inside tmx element.
      But parser will not return any error when there is nothing in tmx.
      (eg, <tmx></tmx>). Attribute 'srclang' is required, but all other
      attributes is optional for now.
  <body> is required. It should be right after header element. But parser
      will not return any error when there is no body element.
  <tu> is element inside <body>. Each <tu> contains a (src_lang, dst_lang) pair,
      it is expected to have 2 <tuv> elements.
  <tuv> is element inside <tu>. Attribute 'xml:lang' is required. Each <tuv> is
      expected to have 1 <seg> containing the phrase.
  <seg> contains the parallel phrase in either source or target language.

  Other unsupported tags(e.g. <entry_metadata>) are skipped.
  For each <tu>, if we can not parse a (src_lang, dst_lang) pair from it, we
  skip this <tu> and append the info into _skipped_phrases list.

  Example TMX structure:
  <tmx>
  <header srclang="en" />
    <body>
      <tu>
        <tuv xml:lang="en">
          <seg>XXX</seg>
        </tuv>
        <tuv xml:lang="zh">
          <seg>???</seg>
        </tuv>
      </tu>
    </body>
  </tmx>
  """
  FILE_FORMAT = 'TMX'

  _TU_BUF_SIZE = 1024
  _PARENT_TAG_NAME = {
    'tmx': '',
    'header': 'tmx',
    'body': 'tmx',
    'tu': 'body',
    'tuv': 'tu',
    'seg': 'tuv',
  }

  def __init__(self, src_lang_code, dst_lang_code, input_stream):
    """Initializes `TmxParser`.

    Args:
      src_lang_code: String - source language code in BCP 47 spec.
      dst_lang_code: String - target language code in BCP 47 spec.
      input_stream: io stream - tmx stream that implemented file interface.
    """
    super(TmxParser, self).__init__()
    self._src_lang = _parse_locale(src_lang_code)
    self._dst_lang = _parse_locale(dst_lang_code)
    self._tmx_stream = input_stream
    self._parser = etree.XMLPullParser(events=('start', 'end'))
    self._events = self._parser.read_events()
    self._buffered_parsed_pairs = []
    self._buffered_pairs_index = 0
    # Current stack of tag names. It should start with empty string.
    self._tag_name_stack = ['']
    self._header_inited = False
    self._body_inited = False
    self._encoding = 'utf-8'

  def next_parallel_phrase_pair(self):
    if len(self._buffered_parsed_pairs) <= self._buffered_pairs_index:
      self._read_next()
    pair = self._buffered_parsed_pairs[self._buffered_pairs_index]
    self._buffered_pairs_index += 1
    return pair

  def _read_next(self):
    """Reads and parses parallel phrase pairs from stream.

    It will reset `_buffered_parsed_pairs` and `_buffered_pairs_index`
    and feeding them with new values.

    Raises:
      InvalidFileFormatError: If stream format is invalid.
      ParseFinished: If stream is finished
    """
    assert len(self._buffered_parsed_pairs) <= self._buffered_pairs_index
    buff_total_size = 0
    self._buffered_pairs_index = 0
    self._buffered_parsed_pairs = []
    while True:
      try:
        buff = self.readline(self._tmx_stream, rstrip=False)
      except ParseFinished:
        self._parser.close()
        raise
      try:
        self._parser.feed(buff)
      except etree.XMLSyntaxError as e:
        # e.message contains line number info.
        raise self.invalid_format_error(e.message, show_line_index=False)
      for action, element in self._events:
        self._verify_element(action, element.tag)
        if action == 'end':
          if element.tag == 'header':
            self._parse_header_element(element)
          if element.tag == 'tu':
            src, dst, error_message = self._parse_tu_element(element)
            if not error_message:
              self._buffered_parsed_pairs.append((src, dst))
            elif _skip_invalid_tmx_data():
              self._skip_phrase_or_fail_parsing(src, dst, error_message)
            else:
              raise self.invalid_format_error(error_message)

            if len(element.getparent()) >= self._TU_BUF_SIZE:
              # There seems a weird bug in lxml appengine, always keep 1
              # element at the end.
              while element.getprevious() is not None:
                del element.getparent()[0]

      if self._buffered_parsed_pairs:
        return
      buff_total_size += len(buff)
      if buff_total_size > self._SENTENCE_BUFFER_SIZE:
        raise self.invalid_format_error('Exceeded buffer limit {}.'.format(
          self._SENTENCE_BUFFER_SIZE))

  def _parse_tu_element(self, tu_element):
    """Parse a <tu> element or skip it on errors.

    Args:
      tu_element: `tu` element parsed by `lxml`
    Returns:
      (src_text, target_text, error_message) tuple; if there is no error, the
      error message is None
    """
    src, dst = None, None
    for child_element in tu_element.getchildren():
      if child_element.tag != 'tuv':
        continue
      text, lang = self._parse_tuv_element(child_element)
      if text and lang:
        if _is_same_language(lang, self._src_lang):
          src = text
        elif _is_same_language(lang, self._dst_lang):
          dst = text

    if not src and not dst:
      return (src, dst,
              'No sentence found in source and target languages in this <tu>')
    if not src:
      return (src, dst, 'No sentence found in source language in this <tu>')
    if not dst:
      return (src, dst, 'No sentence found in target language in this <tu>')
    return (src, dst, None)

  def _parse_tuv_element(self, tuv_element):
    """Parses tuv element.

    Args:
      tuv_element: `tuv` element parsed by `lxml`
    Returns:
      (text_in_seg, language_code_without_locale) tuple
    """
    lang = tuv_element.get('{http://www.w3.org/XML/1998/namespace}lang', None)
    if lang:
      lang = _parse_locale(lang)

    tuv_text = ' '.join(
      text.strip() for text in tuv_element.itertext() if text.strip())
    return tuv_text.strip(), lang

  def _skip_phrase_or_fail_parsing(self, src_text, dst_text, error_message):
    if len(self._skipped_phrases) < self._MAX_SKIPPED_PHRASES:
      self._skipped_phrases.append((self.current_line_number, src_text,
                                    dst_text, error_message))
      return
    # too many errors
    raise self.invalid_format_error(
      'Too many sentence pair errors(%d) so far. The TMX may be broken.' %
      len(self._skipped_phrases))

  def _parse_header_element(self, element):
    """Parses header element."""
    src_lang = element.get('srclang', None)
    if not src_lang:
      return
    src_locale = _parse_locale(src_lang)
    if not _is_same_language(src_locale, self._src_lang):
      raise self.invalid_format_error(
        'Language in header doesn\'t match language'
        ' declared. Expecting {}, found {}'.format(self._src_lang,
                                                   src_locale))

  def _verify_element(self, action, tag):
    """Verifies whether elements' orgnization is valid."""
    if tag not in self._PARENT_TAG_NAME:
      return
    if action == 'start':
      if self._tag_name_stack[-1] != self._PARENT_TAG_NAME[tag]:
        raise self.invalid_format_error(
          'Invalid tag structure: <%s> should go inside <%s>, not <%s>.' %
          (tag, self._PARENT_TAG_NAME[tag], self._tag_name_stack[-1]))
      if tag == 'header':
        if self._header_inited:
          raise self.invalid_format_error('Duplicate header tag.')
        self._header_inited = True
      if tag == 'body':
        if self._body_inited:
          raise self.invalid_format_error('Duplicate body tag.')
        if not self._header_inited:
          raise self.invalid_format_error('header should before body.')
      self._tag_name_stack.append(tag)
    if action == 'end':
      if self._tag_name_stack[-1] != tag:
        raise self.invalid_format_error('Unclosed tag {}.'.format(
          self._tag_name_stack[-1]))
      self._tag_name_stack.pop()


class TmxExporter(ParallelPhraseExporter):
  """Exporter to export parallel phrase pair to tmx stream."""

  _TMX_INIT_TMPL = u"""<?xml version="1.0" encoding="UTF-8" ?>
<tmx version="1.4">
<header srclang="{}"
        adminlang="en-us"
        o-tmf="unknown"
        segtype="sentence"
        creationtool="Uplug"
        creationtoolversion="unknown"
        datatype="PlainText" />
  <body>
"""

  _TMX_PAIR_TMPL = u"""    <tu>
      <tuv xml:lang="{}"><seg>{}</seg></tuv>
      <tuv xml:lang="{}"><seg>{}</seg></tuv>
    </tu>
"""

  def __init__(self, src_lang_code, dst_lang_code, output_stream):
    """Initializes `TmxParser`.

    Args:
      src_lang_code: String - source language code in BCP 47 spec.
      dst_lang_code: String - target language code in BCP 47 spec.
      output_stream: io stream - tmx stream that implemented file interface.
    """
    self._src_lang = _parse_locale(src_lang_code)
    self._dst_lang = _parse_locale(dst_lang_code)
    self._src_lang_code = src_lang_code
    self._dst_lang_code = dst_lang_code
    self._tmx_stream = output_stream

  def feed_parallel_phrase_pair(self, src, dst):
    self._write(
      self._TMX_PAIR_TMPL.format(self._src_lang_code, src,
                                 self._dst_lang_code, dst))

  def initialize(self):
    self._write(self._TMX_INIT_TMPL.format(self._src_lang_code))

  def finalize(self):
    self._write('  </body>\n</tmx>')

  def _write(self, data):
    self._tmx_stream.write(_try_encode(data))


_PARSERS = {
  'tsv': TsvParser,
  'tmx': TmxParser,
}

_EXPORTERS = {
  'tsv': TsvExporter,
  'tmx': TmxExporter,
}


def _get_file_type(path):
  _, file_type = os.path.splitext(path)
  file_type = file_type[1:]
  if file_type not in ('tsv', 'tmx'):
    raise NotImplementedError('`{}` is not supported'.format(file_type))
  return file_type


def create_parser(file_path, *args, **kwargs):
  return _PARSERS[_get_file_type(file_path)](*args, **kwargs)


def create_exporter(file_path, *args, **kwargs):
  return _EXPORTERS[_get_file_type(file_path)](*args, **kwargs)


def iterate_parallel_phrases(input_file_paths, src_lang_code, dst_lang_code, exporter=None):
  total_counts = 0
  for input_file_path in input_file_paths:
    with open(input_file_path) as input_file:
      parser = create_parser(file_path=input_file_path,
                             src_lang_code=src_lang_code,
                             dst_lang_code=dst_lang_code,
                             input_stream=input_file)
      for src, dst in parser:
        total_counts += 1
        if exporter:
          exporter.feed_parallel_phrase_pair(src, dst)
  return total_counts



def convert_input_files(input_file_paths, output_file_path, src_lang_code, dst_lang_code):
  """Converts the file between tsv/tmx."""
  with open(output_file_path, 'w') as output_file:
    with create_exporter(file_path=output_file_path,
                         src_lang_code=src_lang_code,
                         dst_lang_code=dst_lang_code,
                         output_stream=output_file) as exporter:
      iterate_parallel_phrases(input_file_paths=input_file_paths,
                               src_lang_code=src_lang_code,
                               dst_lang_code=dst_lang_code,
                               exporter=exporter)
