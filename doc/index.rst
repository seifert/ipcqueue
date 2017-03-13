
Welcome to ipcqueue's documentation!
====================================

.. toctree::

Interprocess POSIX message queue implementation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. autoclass:: ipcqueue.posixmq.QueueError
    :members:

.. autoclass:: ipcqueue.posixmq.Queue
    :special-members: __init__
    :members:

.. autofunction:: ipcqueue.posixmq.unlink

Interprocess SYS V message queue implementation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. autoclass:: ipcqueue.sysvmq.QueueError
    :members:

.. autoclass:: ipcqueue.sysvmq.Queue
    :special-members: __init__
    :members:
