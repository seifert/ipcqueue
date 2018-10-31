"""
Interprocess SYS V message queue implementation.
"""

from .serializers import PickleSerializer

try:
    import Queue as queue
except ImportError:
    import queue

from ipcqueue._sysvmq import ffi, lib

__all__ = ['QueueError', 'Queue']


class QueueError(Exception):
    """
    Indicates Queue error. Contains additional attributes *errno* and *msg*.
    Value of the *errno* is system dependent, do don't use numeric codes
    directly, use constants **QueueError.ERROR**, **QueueError.INVALID_VALUE**,
    **QueueError.NO_PERMISSIONS**, **QueueError.NO_SYSTEM_RESOURCES**,
    **QueueError.INVALID_DESCRIPTOR**, **QueueError.INTERRUPTED** and
    **QueueError.TOO_BIG_MESSAGE**.
    """

    ERROR = lib.SYSVMQ_E
    INVALID_VALUE = lib.SYSVMQ_E_VALUE
    NO_PERMISSIONS = lib.SYSVMQ_E_PERMISSIONS
    NO_SYSTEM_RESOURCES = lib.SYSVMQ_E_RESOURCES
    INVALID_DESCRIPTOR = lib.SYSVMQ_E_DESCRIPTOR
    INTERRUPTED = lib.SYSVMQ_E_SIGNAL
    TOO_BIG_MESSAGE = lib.SYSVMQ_E_SIZE

    _errno_to_str_map = {
        ERROR: 'Error',
        INVALID_VALUE: 'Invalid value',
        NO_PERMISSIONS: 'No permissions',
        NO_SYSTEM_RESOURCES: 'No system resources',
        INVALID_DESCRIPTOR: 'Invalid queue descriptor',
        INTERRUPTED: 'Interrupted by signal',
        TOO_BIG_MESSAGE: 'Data is too big',
    }

    def __init__(self, errno, msg=None):
        if not msg:
            try:
                msg = self._errno_to_str_map[errno]
            except KeyError:
                msg = self._errno_to_str_map[-1]
        self.errno = errno
        self.msg = msg
        super(QueueError, self).__init__('{}, {}'.format(errno, msg))


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
        queue_id = ffi.new('int *')
        res = lib.sysvmq_open(0 if key is None else key, queue_id)
        if res != lib.SYSVMQ_OK:
            raise QueueError(res)
        self._queue_id = queue_id[0]
        self._key = key

        if max_bytes is None:
            max_bytes = self.qattr()['max_bytes']
        else:
            res = lib.sysvmq_set_max_bytes(self._queue_id, max_bytes)
            if res != lib.SYSVMQ_OK:
                raise QueueError(res)
        self._max_bytes = max_bytes
        self._serializer = serializer

    def close(self):
        """
        Close a message queue.
        """
        res = lib.sysvmq_close(self._queue_id)
        if res != lib.SYSVMQ_OK:
            raise QueueError(res)

    def put(self, item, block=True, msg_type=1):
        """
        Put *item* into the queue. If *block* is ``True``, block if
        necessary until a free slot is available. Otherwise, put an *item*
        on the queue if a free slot is immediately available, else raise
        the :class:`queue.Full` exception. *msg_type* must be positive
        integer value, this value can be used by the receiving process
        for message selection.
        """
        if block:
            timeout = float('inf')
        else:
            timeout = 0.0
        data = self._serializer.dumps(item)
        data_len = len(data)

        if data_len > self._max_bytes:
            raise QueueError(lib.SYSVMQ_E_SIZE)

        res = lib.sysvmq_put(
                self._queue_id, data, data_len, msg_type, timeout)

        if res == lib.SYSVMQ_E_FULL:
            raise queue.Full
        elif res != lib.SYSVMQ_OK:
            raise QueueError(res)

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
        if block:
            timeout = float('inf')
        else:
            timeout = 0.0
        buf = ffi.new('char[]', self._max_bytes)
        size = ffi.new('size_t *', self._max_bytes)

        res = lib.sysvmq_get(self._queue_id, buf, size, msg_type, timeout)

        if res == lib.SYSVMQ_E_EMPTY:
            raise queue.Empty
        elif res != lib.SYSVMQ_OK:
            raise QueueError(res)

        data_size = size[0]
        data = ffi.buffer(buf[0:data_size])[:]
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
        attr = ffi.new('SysVMqAttr *')
        res = lib.sysvmq_get_attr(self._queue_id, attr)
        if res != lib.SYSVMQ_OK:
            raise QueueError(res)
        return {
            'size': attr.size,
            'max_bytes': attr.max_bytes,
        }

    def qsize(self):
        """
        Return the approximate size of the queue. Note, ``qsize() > 0``
        doesn't guarantee that a subsequent :meth:`get()` will not block.
        """
        return self.qattr()['size']
