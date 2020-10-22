"""
Interprocess POSIX message queue implementation.
"""

import errno
try:
    from math import inf
except ImportError:
    inf = float('inf')
try:
    import Queue as queue
except ImportError:
    import queue

from ._posixmq import (
    posixmq_open, posixmq_close, posixmq_unlink, posixmq_put,
    posixmq_get, posixmq_get_attr)
from .serializers import PickleSerializer

__all__ = ['unlink', 'Queue']


def unlink(name):
    """
    Remove a message queue *name*.
    """
    posixmq_unlink(name)


class Queue(object):
    """
    POSIX message queue.
    """

    def __init__(
            self, name, maxsize=10, maxmsgsize=1024,
            serializer=PickleSerializer):
        """
        Constructor for message queue. *name* is an unique identifier of
        the queue, must starts with ``/``. *maxsize* is an integer that
        sets the upperbound limit on the number of items that can be placed
        in the queue (maximum value depends on system limit). *maxmsgsize*
        is a maximum size of the message in bytes (maximum value depends
        on hard system limit).
        """
        self._queue_id = posixmq_open(name, maxmsgsize, maxsize)
        self._name = name
        self._maxsize = maxsize
        self._max_msg_size = maxmsgsize
        self._serializer = serializer

    def close(self):
        """
        Close a message queue.
        """
        posixmq_close(self._queue_id)

    def unlink(self):
        """
        Remove a message queue. POSIX message queues have kernel persistence,
        so if it's not removed by this method, a message queue will exist
        until the system is shut down.
        """
        unlink(self._name)

    def put(self, item, block=True, timeout=None, priority=0):
        """
        Put *item* into the queue. If *block* is ``True`` and *timeout* is
        ``None`` (the default), block if necessary until a free slot is
        available. If *timeout* is a positive number, it blocks at most
        *timeout* seconds and raises the :class:`queue.Full` exception if
        no free slot was available within that time. Otherwise (*block* is
        ``False``), put an *item* on the queue if a free slot is immediately
        available, else raise the :class:`queue.Full` exception (*timeout*
        is ignored in that case). *priority* is a priority of the message,
        the highest valued items are retrieved first.
        """
        if not block:
            timeout = 0.0
        elif timeout is None:
            timeout = inf
        data = self._serializer.dumps(item)
        try:
            posixmq_put(self._queue_id, data, priority, timeout)
        except OSError as exc:
            if exc.errno == errno.ETIMEDOUT:
                raise queue.Full
            raise

    def put_nowait(self, item, priority=0):
        """
        Put *item* into the queue, equivalent to ``put(item, block=False)``.
        *priority* is a priority of the message, the highest valued items
        are retrieved first. Items is serialized by Python's :mod:`pickle`
        module, *pickle_protocol* is a protocol's version.
        """
        return self.put(item, block=False, priority=priority)

    def get(self, block=True, timeout=None):
        """
        Remove and return an item from the queue. If *block* is ``True`` and
        *timeout* is ``None`` (the default), block if necessary until an item
        is available. If *timeout* is a positive number, it blocks at most
        *timeout* seconds and raises the :class:`queue.Empty` exception if no
        item was available within that time. Otherwise (block is ``False``),
        return an item if one is immediately available, else raise the
        :class:`queue.Empty` exception (*timeout* is ignored in that case).
        """
        if not block:
            timeout = 0.0
        elif timeout is None:
            timeout = inf
        try:
            data = posixmq_get(self._queue_id, timeout, self._max_msg_size)
        except OSError as exc:
            if exc.errno == errno.ETIMEDOUT:
                raise queue.Empty
            raise
        return self._serializer.loads(data)

    def get_nowait(self):
        """
        Get and return an item from queue, equivalent to ``get(block=False)``.
        """
        return self.get(block=False)

    def qattr(self):
        """
        Return attributes of the message queue as a :class:`dict`:
        ``{'size': 5, 'max_size': 10, 'max_msgbytes': 1024}``.
        """
        return  posixmq_get_attr(self._queue_id)

    def qsize(self):
        """
        Return the approximate size of the queue. Note, ``qsize() > 0``
        doesn't guarantee that a subsequent :meth:`get` will not block,
        nor will ``qsize() < maxsize`` guarantee that :meth:`put` will
        not block.
        """
        return self.qattr()['size']
