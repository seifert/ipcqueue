"""
This package provides SYS V and POSIX message queues to exchange data
among processes. Both queues have similar functionality with some
differences. Queues are persistent in the kernel unless either queue is
closed/unlinked or system is shut down. Unlike :class:`multiprocessing.Queue`,
the same queue can be joined by different processes according to its unique
name/key, it's not necessary to fork main process. Be careful if you use
signals in your application, because signal interrupts sending or receiving
message.

SYS V queue provides receiving messages according to their message
type, but doesn't provide blocking with timeout. See
http://man7.org/linux/man-pages/man7/svipc.7.html.

POSIX queue provides receiving messages according their priority, blocking
with timeout is supported, but doesn't provide  message's type. See
http://man7.org/linux/man-pages/man7/mq_overview.7.html.
"""

__version__ = '0.9.5'
