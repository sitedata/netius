#!/usr/bin/python
# -*- coding: utf-8 -*-

# Hive Netius System
# Copyright (C) 2008-2012 Hive Solutions Lda.
#
# This file is part of Hive Netius System.
#
# Hive Netius System is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Hive Netius System is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Hive Netius System. If not, see <http://www.gnu.org/licenses/>.

__author__ = "João Magalhães joamag@hive.pt>"
""" The author(s) of the module """

__version__ = "1.0.0"
""" The version of the module """

__revision__ = "$LastChangedRevision$"
""" The revision number of the module """

__date__ = "$LastChangedDate$"
""" The last change date of the module """

__copyright__ = "Copyright (c) 2008-2012 Hive Solutions Lda."
""" The copyright for the module """

__license__ = "GNU General Public License (GPL), Version 3"
""" The license for the module """

import sys

import http

class WSGIServer(http.HTTPServer):

    def __init__(self, app, mount = "", name = None, handler = None, *args, **kwargs):
        http.HTTPServer.__init__(
            self,
            name = name,
            handler = handler,
            *args,
            **kwargs
        )
        self.app = app
        self.mount = mount
        self.mount_l = len(mount)

    def on_data_http(self, connection, parser):
        http.HTTPServer.on_data_http(self, connection, parser)

        # clojure method to be used to close the current connection in
        # case that's required by the current connection headers
        def close(data):
            self.on_connection_d(connection)

        # method created as a clojure that handles the starting of
        # response as defined in the wsgi standards
        def start_response(status, headers):
            return self._start_response(connection, status, headers)

        # retrieves the path for the current request and then retrieves
        # the query string part for it also, after that computes the
        # path info value as the substring of the path without the mount
        path = parser.get_path()
        query = parser.get_query()
        path_info = path[self.mount_l:]

        # initializes the environment map (structure) with all the cgi based
        # variables that should enable the application to handle the request
        # and respond to it in accordance
        environ = dict(
            REQUEST_METHOD = parser.method.upper(),
            SCRIPT_NAME = self.mount,
            PATH_INFO = path_info,
            QUERY_STRING = query,
            CONTENT_TYPE = parser.headers.get("content-type", None),
            CONTENT_LENGTH = None if parser.content_l == -1 else parser.content_l,
            SERVER_NAME = http.SERVER_NAME,
            SERVER_PORT = self.port,
            SERVER_PROTOCOL = parser.version_s
        )

        # updates the environment map with all the structures referring
        # to the wsgi specifications note that the message is retrieved
        # as a buffer to be able to handle the file specific operations
        environ["wsgi.version"] = (1, 0)
        environ["wsgi.url_scheme"] = "https" if connection.ssl else "http"
        environ["wsgi.input"] = parser.get_message_b()
        environ["wsgi.errors"] = sys.stderr
        environ["wsgi.multithread"] = True
        environ["wsgi.multiprocess"] = True
        environ["wsgi.run_once"] = True

        # iterates over all the header values that have been received
        # to set them in the environment map to be used by the wsig
        # infra-structure, not that their name is capitalized as defined
        # in the standard specification
        for key, value in parser.headers.items():
            key = "HTTP_" + key.upper()
            environ[key] = value

        # runs the app logic with the provided environment map and start
        # response clojure and then iterates over the complete set of values
        # in the returned iterator to send the messages to the other end
        sequence = self.app(environ, start_response)
        for value in sequence: connection.send(value)

        # in case the connection is not meant to be kept alive must
        # send an empty string with the callback for the closing of
        # the connection (connection close handle)
        if not parser.keep_alive: connection.send("", callback = close)

    def _start_response(self, connection, status, headers):
        parser = connection.parser
        version_s = parser.version_s
        headers = dict(headers)

        self._apply_base(headers)
        self._apply_parser(parser, headers)

        buffer = []
        buffer.append("%s %s\r\n" % (version_s, status))
        for key, value in headers.items():
            buffer.append("%s: %s\r\n" % (key, value))
        buffer.append("\r\n")

        data = "".join(buffer)
        connection.send(data)

def application(environ, start_response):
    message = "Hello World"
    message_l = len(message)
    headers = [
        ("Content-Type", "text/plain"),
        ("Content-Length", str(message_l))
    ]
    start_response("200 OK", headers)
    yield message


from flask import Flask
app = Flask(__name__)

@app.route("/")
@app.route("/index")
def hello():
    return "Hello World!"

if __name__ == "__main__":
    server = WSGIServer(app, mount = "/hello")
    server.serve(host = "0.0.0.0")
