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

load("@deps//:requirements.bzl", "requirement")

py_binary(
  name = "parser",
  srcs = [
    "parser.py",
  ],
  deps = [
    ":autosplit",
    ":parser_util",
    requirement("future"),
  ],
)

py_library(
  name = "parser_util",
  srcs = [
    "parser_util.py",
  ],
  deps = [
    requirement("absl-py"),
    requirement("lxml"),
  ],
)

py_test(
  name = "parser_util_test",
  srcs = [
    "parser_util_test.py",
  ],
  deps = [
    ":parser_util",
  ],
)

py_library(
  name = "autosplit",
  srcs = [
    "autosplit.py",
  ],
  deps = [
    ":parser_util",
    requirement("enum34"),
  ],
)

py_test(
  name = "autosplit_test",
  srcs = [
    "autosplit_test.py",
  ],
  deps = [
    ":autosplit",
    requirement("mock"),
  ],
)
