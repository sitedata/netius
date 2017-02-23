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

import time
import socket

from . import async
from . import errors

class AbstractLoop(object):
    """
    Top level abstract class that adds compatibility support for
    the asyncio event loop strategy.
    """

    def time(self):
        return time.time()

    def call_at(self, when, callback, *args):
        delay = when - self.time()
        return self.call_later(delay, callback, *args)

    def call_later(self, delay, callback, *args):
        """
        Calls the provided callback with the provided parameters after the defined
        delay (in seconds), should ensure proper sleep operation.

        :type delay: float
        :param delay: The delay in seconds after which the callback is going to be
        called with the provided arguments.
        :type callback: Function
        :param callback: The function to be called after the provided delay.
        :rtype: Handle
        :return: The handle object to the operation, that may be used to cancel it.
        """

        # creates the callable to be called after the timeout, note the
        # clojure around the "normal" arguments (allows proper propagation)
        callable = lambda: callback(*args)

        # schedules the delay call of the created callable according to
        # the provided (amount of) sleep time
        self.delay(callable, timeout = delay)

        # creates the handle to control the operation and then returns the
        # object to the caller method, allowing operation
        handle = async.Handle()
        return handle

    def create_future(self):
        """
        Creates a future object that is bound to the current event loop context,
        this allows for latter access to the owning loop.

        This behaviour is required to ensure compatibility with the "legacy"
        asyncio support, ensuring seamless compatibility.

        :rtype: Future
        :return: The generated future that should be bound to the current context.
        """

        # creates a normal future object, setting the current instance as
        # the loop, then returns the future to the caller method
        future = async.Future()
        future._loop = self
        return future

    def create_task(self, coroutine):
        future = self.ensure(coroutine)
        task = async.Task(future)
        return task

    def create_connection(self, *args, **kwargs):
        coroutine = self._create_connection(*args, **kwargs)
        return async.coroutine_return(coroutine)

    def getaddrinfo(self, *args, **kwargs):
        coroutine = self._getaddrinfo(*args, **kwargs)
        return async.coroutine_return(coroutine)

    def getnameinfo(self, *args, **kwargs):
        coroutine = self._getnameinfo(*args, **kwargs)
        return async.coroutine_return(coroutine)

    def run_until_complete(
        self,
        coroutine,
        args = [],
        kwargs = {},
        thread = None
    ):
        # creates the callback function that is going to be called when
        # the future associated with the provided ensure context gets
        # finished (on done callback)
        def cleanup(future):
            exception = future.exception()
            if exception:
                self.warning(exception)
                self.log_stack()
            self.stop()

        # tries to determine if the provided object is in fact a coroutine
        # or if instead it is a "simple" future object ready to be used
        is_coroutine = async.is_coroutine(coroutine)

        # ensures that the provided coroutine get executed under a new
        # context and retrieves the resulting future
        future = self.ensure(
            coroutine,
            args = args,
            kwargs = kwargs,
            thread = thread
        ) if is_coroutine else coroutine

        # defines the cleanup operation (loop stop) as the target for the
        # done operation on the future (allows cleanup)
        future.add_done_callback(cleanup)

        # updates the current task associated with the event loop, note that
        # this operation required proper asyncio patching, causing possible
        # issues with other event loop
        self._set_current_task(future)

        # starts the current event loop, this is a blocking operation until
        # the done callback is called to stop the loop
        self.start()

    def get_debug(self):
        return self.is_debug()

    def is_closed(self):
        return self.is_stopped()

    def _getaddrinfo(
        self,
        host,
        port,
        family = 0,
        type = 0,
        proto = 0,
        flags = 0
    ):
        future = self.create_future()
        result = socket.getaddrinfo(
            host,
            port,
            family,
            type,
            proto,
            flags = flags
        )
        self.delay(lambda: future.set_result(result), immediately = True)
        yield future

    def _getnameinfo(self, sockaddr, flags = 0):
        raise errors.NotImplemented()

    def _create_connection(
        self,
        protocol_factory,
        host = None,
        port = None,
        ssl = None,
        family = 0,
        proto = 0,
        flags = 0,
        sock = None,
        local_addr = None,
        server_hostname = None,
        *args,
        **kwargs
    ):
        future = self.create_future()

        def connect(connection):
            protocol = protocol_factory()
            connection._set_compat(protocol)
            future.set_result((connection, protocol))

        connection = self.connect(
            host,
            port,
            ssl = ssl,
            ensure_loop = False
        )
        connection.bind("connect", connect)

        yield future

    def _set_current_task(self, task):
        import asyncio
        asyncio.Task._current_tasks[self] = task

class AbstractTransport(object):

    def write(self, data):
        self.send(data)

    def _on_data(self, connection, data):
        self._protocol.data_received(data)

    def _on_close(self, connection):
        self._protocol.eof_received()

    def _set_compat(self, protocol):
        self._set_binds()
        self._set_protocol(protocol)

    def _set_binds(self):
        self.bind("data", self._on_data)
        self.bind("close", self._on_close)

    def _set_protocol(self, protocol):
        self._protocol = protocol
