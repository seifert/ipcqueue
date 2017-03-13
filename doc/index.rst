
Welcome to ipcqueue's documentation!
====================================

.. automodule:: ipcqueue

POSIX message queue
-------------------

.. automodule:: ipcqueue.posixmq
    :members:

::

    >>> from ipcqueue import posixmq
    >>> q = posixmq.Queue('/foo')
    >>> q.qsize()
    0
    >>> q.put([1, 'A'])
    >>> q.put([2, 'B'], priority=2)
    >>> q.put([3, 'C'], priority=0)
    >>> q.qsize()
    3
    >>> q.get()
    [2, 'B']
    >>> q.get()
    [1, 'A']
    >>> q.get()
    [3, 'C']
    >>> q.close()
    >>> q.unlink()

SYS V message queue
-------------------

.. automodule:: ipcqueue.sysvmq
    :members:

::

    >>> from ipcqueue import sysvmq
    >>> q = sysvmq.Queue(1)
    >>> q.qsize()
    >>> q.put([1, 'A'])
    >>> q.put([2, 'B'], msg_type=2)
    >>> q.put([3, 'C'], msg_type=2)
    >>> q.put([4, 'D'], msg_type=1)
    >>> q.qsize()
    4
    >>> q.get(msg_type=2)
    [2, 'B']
    >>> q.get()
    [1, 'A']
    >>> q.get()
    [3, 'C']
    >>> q.get()
    [4, 'D']
    >>> q.close()
