#!/usr/bin/python
# -*- coding: utf-8 -*-

# Hive Appier Framework
# Copyright (C) 2008-2014 Hive Solutions Lda.
#
# This file is part of Hive Appier Framework.
#
# Hive Appier Framework is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Hive Appier Framework is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Hive Appier Framework. If not, see <http://www.gnu.org/licenses/>.

__author__ = "João Magalhães <joamag@hive.pt>"
""" The author(s) of the module """

__version__ = "1.0.0"
""" The version of the module """

__revision__ = "$LastChangedRevision$"
""" The revision number of the module """

__date__ = "$LastChangedDate$"
""" The last change date of the module """

__copyright__ = "Copyright (c) 2008-2014 Hive Solutions Lda."
""" The copyright for the module """

__license__ = "GNU General Public License (GPL), Version 3"
""" The license for the module """

import unittest

import netius.common

SIMPLE_REQUEST = b"GET http://localhost HTTP/1.0\r\n\
Date: Wed, 1 Jan 2014 00:00:00 GMT\r\n\
Server: Test Service/1.0.0\r\n\
Content-Length: 11\r\n\
\r\n\
Hello World"

class HTTPParserTest(unittest.TestCase):

    def test_simple(self):
        parser = netius.common.HTTPParser(
            self,
            type = netius.common.REQUEST,
            store = True
        )
        parser.parse(SIMPLE_REQUEST)
        message = parser.get_message()
        headers = parser.get_headers()
        self.assertEqual(parser.method, b"get")
        self.assertEqual(parser.content_l, 11)
        self.assertEqual(message, b"Hello World")
        self.assertEqual(headers["server"], b"Service/1.0.0")