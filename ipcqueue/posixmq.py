"""
Interprocess POSIX message queue implementation.
"""

try:
    import cPickle as pickle
except ImportError:
    import pickle
try:
    import Queue as queue
except ImportError:
    import queue

from ipcqueue._posixmq import ffi, lib

__all__ = ['QueueError', 'unlink', 'Queue']


class QueueError(Exception):
    """
    Indicates Queue error. Contains additional attributes *errno* and *msg*.
    Value of the *errno* is system dependent, do don't use numeric codes
    directly, use constants **QueueError.ERROR**, **QueueError.INVALID_VALUE**,
    **QueueError.NO_PERMISSIONS**, **QueueError.NO_SYSTEM_RESOURCES**,
    **QueueError.INVALID_DESCRIPTOR**, **QueueError.INTERRUPTED**,
    **QueueError.TOO_BIG_MESSAGE**, **QueueError.TIMEOUT** and
    **QueueError.DOES_NOT_EXIST**.
    """

    ERROR = lib.POSIXMQ_E
    INVALID_VALUE = lib.POSIXMQ_E_VALUE
    NO_PERMISSIONS = lib.POSIXMQ_E_PERMISSIONS
    NO_SYSTEM_RESOURCES = lib.POSIXMQ_E_RESOURCES
    INVALID_DESCRIPTOR = lib.POSIXMQ_E_DESCRIPTOR
    INTERRUPTED = lib.POSIXMQ_E_SIGNAL
    TOO_BIG_MESSAGE = lib.POSIXMQ_E_SIZE
    TIMEOUT = lib.POSIXMQ_E_TIMEOUT
    DOES_NOT_EXIST = lib.POSIXMQ_E_DOESNT_EXIST

    _errno_to_str_map = {
        ERROR: 'Error',
        INVALID_VALUE: 'Invalid value',
        NO_PERMISSIONS: 'No permissions',
        NO_SYSTEM_RESOURCES: 'No system resources',
        INVALID_DESCRIPTOR: 'Invalid queue descriptor',
        INTERRUPTED: 'Interrupted by signal',
        TOO_BIG_MESSAGE: 'Data is too big',
        TIMEOUT: 'Timeout',
        DOES_NOT_EXIST: 'Queue does not exist',
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


def unlink(name):
    """
    Remove a message queue *name*.
    """
    q_name = ffi.new('char[]', name.encode('utf-8'))
    res = lib.posixmq_unlink(q_name)
    if res != lib.POSIXMQ_OK:
        raise QueueError(res)


class Queue(object):
    """
    POSIX message queue.
    """

    def __init__(self, name, maxsize=10, maxmsgsize=1024):
        """
        Constructor for message queue. *name* is an unique identifier of the
        queue, must starts with ``/``. *maxsize* is an integer that sets
        the upperbound limit on the number of items that can be placed in
        the queue (maximum value depends on system limit). *maxmsgsize*
        is a maximum size of the message in bytes (maximum value depends
        on hard system limit).
        """
        queue_name = ffi.new('char[]', name.encode('utf-8'))
        queue_id = ffi.new('int *')
        res = lib.posixmq_open(queue_name, queue_id, maxmsgsize, maxsize)
        if res != lib.POSIXMQ_OK:
            raise QueueError(res)
        self._queue_id = queue_id[0]
        self._name = name
        self._maxsize = maxsize
        self._max_msg_size = maxmsgsize

    def close(self):
        """
        Close a message queue.
        """
        res = lib.posixmq_close(self._queue_id)
        if res != lib.POSIXMQ_OK:
            raise QueueError(res)

    def unlink(self):
        """
        Remove a message queue. POSIX message queues have kernel persistence,
        so if it's not removed by this method, a message queue will exist
        until the system is shut down.
        """
        unlink(self._name)

    def put(self, item, block=True, timeout=None, priority=0,
            pickle_protocol=1):
        """
        Put *item* into the queue. If *block* is ``True`` and *timeout* is
        ``None`` (the default), block if necessary until a free slot is
        available. If *timeout* is a positive number, it blocks at most
        *timeout* seconds and raises the :class:`queue.Full` exception if
        no free slot was available within that time. Otherwise (*block* is
        ``False``), put an *item* on the queue if a free slot is immediately
        available, else raise the :class:`queue.Full` exception (*timeout*
        is ignored in that case). *priority* is a priority of the message,
        the highest valued items are retrieved first. Items is serialized by
        Python's :mod:`pickle` module, *pickle_protocol* is a protocol's
        version.
        """
        if not block:
            timeout = 0.0
        elif timeout is None:
            timeout = float('inf')
        data = pickle.dumps(item, pickle_protocol)

        res = lib.posixmq_put(
            self._queue_id, data, len(data), priority, timeout)

        if res == lib.POSIXMQ_E_TIMEOUT:
            raise queue.Full
        elif res != lib.POSIXMQ_OK:
            raise QueueError(res)

    def put_nowait(self, item, priority=0, pickle_protocol=1):
        """
        Put *item* into the queue, equivalent to ``put(item, block=False)``.
        *priority* is a priority of the message, the highest valued items
        are retrieved first. Items is serialized by Python's :mod:`pickle`
        module, *pickle_protocol* is a protocol's version.
        """
        return self.put(item, block=False, priority=priority,
                        pickle_protocol=pickle_protocol)

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
            timeout = float('inf')
        buffer = ffi.new('char[]', self._max_msg_size)
        size = ffi.new('size_t *', self._max_msg_size)
        priority = ffi.new('unsigned int *')

        res = lib.posixmq_get(self._queue_id, buffer, size, priority, timeout)

        if res == lib.POSIXMQ_E_TIMEOUT:
            raise queue.Empty
        elif res != lib.POSIXMQ_OK:
            raise QueueError(res)

        data_size = size[0]
        data = ffi.buffer(buffer[0:data_size])[:]
        return pickle.loads(data)

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
        attr = ffi.new('struct mq_attr *')
        res = lib.posixmq_get_attr(self._queue_id, attr)
        if res != lib.POSIXMQ_OK:
            raise QueueError(res)
        return {
            'size': attr.mq_curmsgs,
            'max_size': attr.mq_maxmsg,
            'max_msgbytes': attr.mq_msgsize,
        }

    def qsize(self):
        """
        Return the approximate size of the queue. Note, ``qsize() > 0``
        doesn't guarantee that a subsequent :meth:`get` will not block,
        nor will ``qsize() < maxsize`` guarantee that :meth:`put` will
        not block.
        """
        attr = self.qattr()
        return attr['size']
