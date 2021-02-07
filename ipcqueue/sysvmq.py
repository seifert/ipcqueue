"""
Interprocess SYS V message queue implementation.
"""

import errno
try:
    import Queue as queue
except ImportError:
    import queue

from ._sysvmq import (
    sysvmq_open, sysvmq_close, sysvmq_put, sysvmq_get,
    sysvmq_get_attr, sysvmq_set_max_bytes)
from .serializers import PickleSerializer

__all__ = ['Queue']


class Queue(object):
    """
    SYS V message queue.
    """

    def __init__(self, key=None, max_bytes=None, serializer=PickleSerializer):
        """
        Constructor for message queue. *key* is an unique identifier of
        the queue, must be positive number or ``0`` for private queue.
        *max_bytes* is a maximum number of bytes allowed in queue
        (maximum value depends on hard system limit).
        """
        self._queue_id = sysvmq_open(0 if key is None else key)
        self._key = key
        if max_bytes is None:
            max_bytes = self.qattr()['max_bytes']
        else:
            sysvmq_set_max_bytes(self._queue_id, max_bytes)
        self._max_bytes = max_bytes
        self._serializer = serializer

    def close(self):
        """
        Close a message queue.
        """
        sysvmq_close(self._queue_id)

    def put(self, item, block=True, msg_type=1):
        """
        Put *item* into the queue. If *block* is ``True``, block if
        necessary until a free slot is available. Otherwise, put an *item*
        on the queue if a free slot is immediately available, else raise
        the :class:`queue.Full` exception. *msg_type* must be positive
        integer value, this value can be used by the receiving process
        for message selection.
        """
        data = self._serializer.dumps(item)
        try:
            sysvmq_put(self._queue_id, data, msg_type, block)
        except OSError as exc:
            if exc.errno == errno.EAGAIN:
                raise queue.Full
            raise

    def put_nowait(self, item, msg_type=1):
        """
        Put *item* into the queue, equivalent to ``put(item, block=False)``.
        *msg_type* must be positive integer value, this value can be used
        by the receiving process for message selection. *pickle_protocol*
        is a format used by Python's :mod:`pickle`.
        """
        return self.put(item, block=False, msg_type=msg_type)

    def get(self, block=True, msg_type=0):
        """
        Remove and return an item from the queue. If *block* argument is
        ``True``, block if necessary until an item is available. Otherwise,
        return an item if one is immediately available, else raise the
        :class:`queue.Empty` exception. *msg_type* specifies the type of
        requested message. If it's ``0``, then the first message in the
        queue is read, if it's greater than ``0``, then the first message
        in the queue of requested type is read and if it's less than ``0``,
        then the first message in the queue with the lowest type less than
        or equal to the absolute value of *msg_type* will be read.
        """
        try:
            data = sysvmq_get(self._queue_id, msg_type, block)
        except OSError as exc:
            if exc.errno == errno.ENOMSG:
                raise queue.Empty
            raise
        return self._serializer.loads(data)

    def get_nowait(self, msg_type=0):
        """
        Get and return an item from queue, equivalent to ``get(block=False)``.
        *msg_type* specifies the type of requested message. If it's ``0``,
        then the first message in the queue is read, if it's greater than
        ``0``, then the first message in the queue of requested type is
        read and if it's less than ``0``, then the first message in the
        queue with the lowest type less than or equal to the absolute value
        of *msg_type* will be read.
        """
        return self.get(block=False, msg_type=msg_type)

    def qattr(self):
        """
        Return attributes of the message queue as a :class:`dict`:
        ``{'size': 3, 'max_bytes': 8192}``.
        """
        return sysvmq_get_attr(self._queue_id)

    def qsize(self):
        """
        Return the approximate size of the queue. Note, ``qsize() > 0``
        doesn't guarantee that a subsequent :meth:`get()` will not block.
        """
        return self.qattr()['size']
