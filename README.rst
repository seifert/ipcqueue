IpcQueue
========

This package provides SYS V and POSIX message queues to exchange data
among processes. Both queues have similar functionality with some
differences. Queues are persistent in the kernel unless either queue is
closed/unlinked or system is shut down. Unlike `multiprocessing.Queue`,
the same queue can be joined by different processes according to its
unique name/key, it's not necessary to fork main process. Be careful if
you use signals in your application, because signal interrupts sending
or receiving message.

Installation
------------

Requires Python CFFI, C compiler and Python header files.

::

    cd ipcqueue/
    python setup.py install

Usage
-----

::

    >>> from ipcqueue import posixmq
    >>> q = posixmq.Queue('/foo')
    >>> q.qsize()
    0
    >>> q.put([1, 'A'], priority=1)
    >>> q.put([2, 'B'], priority=2)
    >>> q.put([3, 'C'], priority=1)
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

    >>> from ipcqueue import sysvmq
    >>> q = sysvmq.Queue(1)
    >>> q.qsize()
    >>> q.put([1, 'A'], msg_type=1)
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

Documentation
-------------

http://pythonhosted.org/ipcqueue

License
-------

3-clause BSD
