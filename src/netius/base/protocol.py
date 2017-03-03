#!/usr/bin/python
# -*- coding: utf-8 -*-

# Hive Netius System
# Copyright (c) 2008-2017 Hive Solutions Lda.
#
# This file is part of Hive Netius System.
#
# Hive Netius System is free software: you can redistribute it and/or modify
# it under the terms of the Apache License as published by the Apache
# Foundation, either version 2.0 of the License, or (at your option) any
# later version.
#
# Hive Netius System is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# Apache License for more details.
#
# You should have received a copy of the Apache License along with
# Hive Netius System. If not, see <http://www.apache.org/licenses/>.

__author__ = "João Magalhães <joamag@hive.pt>"
""" The author(s) of the module """

__version__ = "1.0.0"
""" The version of the module """

__revision__ = "$LastChangedRevision$"
""" The revision number of the module """

__date__ = "$LastChangedDate$"
""" The last change date of the module """

__copyright__ = "Copyright (c) 2008-2017 Hive Solutions Lda."
""" The copyright for the module """

__license__ = "Apache License, Version 2.0"
""" The license for the module """

from . import legacy
from . import request
from . import observer

class Protocol(observer.Observable):

    def __init__(self, owner = None):
        observer.Observable.__init__(self)
        self.owner = owner
        self._transport = None
        self._loop = None
        self._writing = True
        self._closed = True
        self._delayed = []

    def open(self):
        self._closed = False

        self.trigger("open", self)

    def close(self):
        self._close_transport()

        del self._delayed[:]

        self._transport = None
        self._loop = None
        self._writing = True
        self._closed = True

        self.trigger("close", self)

    def info_dict(self, full = False):
        if not self._transport: return dict()
        info = self._transport.info_dict(full = full)
        return info

    def connection_made(self, transport):
        self._transport = transport
        self.open()

    def connection_lost(self, exception):
        self.close()

    def pause_writing(self):
        self._writing = False

    def resume_writing(self):
        self._writing = True
        self._flush_send()

    def delay(self, callable, timeout = None):
        if hasattr(self._loop, "delay"):
            immediately = timeout == None
            return self._loop.delay(
                callable,
                timeout = timeout,
                immediately = immediately
            )

        if timeout: return self._loop.call_later(timeout, callable)
        else: return self._loop.call_soon(callable)

    def debug(self, object):
        if not self._loop: return
        if not hasattr(self._loop, "debug"): return
        self._loop.debug(object)

    def info(self, object):
        if not self._loop: return
        if not hasattr(self._loop, "info"): return
        self._loop.info(object)

    def warning(self, object):
        if not self._loop: return
        if not hasattr(self._loop, "warning"): return
        self._loop.warning(object)

    def error(self, object):
        if not self._loop: return
        if not hasattr(self._loop, "error"): return
        self._loop.error(object)

    def critical(self, object):
        if not self._loop: return
        if not hasattr(self._loop, "critical"): return
        self._loop.critical(object)

    def is_open(self):
        return not self._closed

    def is_closed(self):
        return self._closed

    def _close_transport(self):
        if not self._transport: return
        self._transport.abort()

    def _delay_send(self, data, address = None, callback = None):
        item = (data, address, callback)
        self._delays.append(item)

    def _flush_send(self):
        while True:
            if not self._delays: break
            if not self._writing: break
            data, address, callback = self._delays.pop(0)
            if address: self.send(data, address, callback = callback)
            else: self.send(data, callback = callback)

class DatagramProtocol(Protocol):

    def __init__(self):
        Protocol.__init__(self)
        self.requests = []
        self.requests_m = {}

    def datagram_received(self, data, address):
        self.on_data(address, data)

    def error_received(self, exception):
        pass

    def on_data(self, address, data):
        pass

    def send(
        self,
        data,
        address,
        delay = True,
        force = False,
        callback = None
    ):
        return self.send_to(data, address)

    def send_to(
        self,
        data,
        address,
        delay = True,
        force = False,
        callback = None
    ):
        if not self._writing:
            return self._delay_send(
                data,
                address = address,
                callback = callback
            )

        data = legacy.bytes(data)
        result = self._transport.sendto(data, address)

        if callback: self.delay(lambda: callback(self._transport))

        return result

    def add_request(self, request):
        # adds the current request object to the list of requests
        # that are pending a valid response, a garbage collector
        # system should be able to erase this request from the
        # pending list in case a timeout value has passed
        self.requests.append(request)
        self.requests_m[request.id] = request

    def remove_request(self, request):
        self.requests.remove(request)
        del self.requests_m[request.id]

    def get_request(self, id):
        is_response = isinstance(id, request.Response)
        if is_response: id = id.get_id()
        return self.requests_m.get(id, None)

class StreamProtocol(Protocol):

    def data_received(self, data):
        self.on_data(data)

    def eof_received(self):
        pass

    def on_data(self, data):
        pass

    def send(self, data, delay = True, force = False, callback = None):
        if not self._writing:
            return self._delay_send(data, callback = callback)

        data = legacy.bytes(data)
        result = self._transport.write(data)

        if callback: self.delay(lambda: callback(self._transport))

        return result
