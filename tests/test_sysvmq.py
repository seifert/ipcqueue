
try:
    from Queue import Full, Empty
except ImportError:
    from queue import Full, Empty
import time

import pytest

from ipcqueue.sysvmq import Queue, QueueError


@pytest.fixture(scope='function')
def mq():
    mq = Queue(key=None, max_bytes=2048)
    yield mq
    mq.close()


@pytest.fixture(scope='function')
def mq_full(mq):
    mq.put_nowait([1, 'a' * 384])
    mq.put_nowait([2, 'a' * 384])
    mq.put_nowait([3, 'a' * 384])
    mq.put_nowait([4, 'a' * 384])
    mq.put_nowait([5, 'a' * 384])
    yield mq


def test_create_fail_when_invalid_key():
    with pytest.raises(OverflowError):
        mq = Queue(-1)
        mq.close()


def test_close_fail_when_invalid_descriptor():
    mq = Queue(0)
    mq.close()
    with pytest.raises(QueueError) as excinfo:
        mq.close()
    assert excinfo.value.errno == QueueError.INVALID_DESCRIPTOR


def test_put_get_nowait(mq):
    mq.put_nowait([123, 'test message'])
    mq.put_nowait([456, 'test message'])
    mq.put_nowait([789, 'test message'])
    assert mq.get_nowait() == [123, 'test message']
    assert mq.get_nowait() == [456, 'test message']
    assert mq.get_nowait() == [789, 'test message']


def test_put_get_nowait_msgtype(mq):
    mq.put_nowait([123, 'test message'], msg_type=1)
    mq.put_nowait([456, 'test message'], msg_type=2)
    mq.put_nowait([789, 'test message'], msg_type=1)
    assert mq.get_nowait(msg_type=2) == [456, 'test message']
    assert mq.get_nowait(msg_type=0) == [123, 'test message']
    assert mq.get_nowait(msg_type=1) == [789, 'test message']


def test_put_get_nowait_pickle_protocol(mq):
    mq.put_nowait([123, 'test message'])
    mq.put_nowait([456, 'test message'])
    assert mq.get_nowait() == [123, 'test message']
    assert mq.get_nowait() == [456, 'test message']


def test_put_nowait_fail_when_full_queue(mq_full):
    with pytest.raises(Full):
        mq_full.put_nowait([6, 'a' * 384])


def test_get_nowait_fail_when_empty_queue(mq):
    with pytest.raises(Empty):
        mq.get_nowait()


def test_put_block_forever(mq_full, alarm_handler):
    alarm_handler(1)
    start_time = time.time()
    with pytest.raises(QueueError) as excinfo:
        mq_full.put([6, 'a' * 384])
    assert time.time() - start_time > 1
    assert excinfo.value.errno == QueueError.INTERRUPTED


def test_get_block_forever(mq, alarm_handler):
    alarm_handler(1)
    start_time = time.time()
    with pytest.raises(QueueError) as excinfo:
        mq.get()
    assert time.time() - start_time > 1
    assert excinfo.value.errno == QueueError.INTERRUPTED


def test_put_fail_when_big_message(mq):
    with pytest.raises(QueueError) as excinfo:
        mq.put_nowait(['a' * (2048 + 1)])
    assert excinfo.value.errno == QueueError.TOO_BIG_MESSAGE


def test_qattr_empty_queue(mq):
    attr = mq.qattr()
    assert attr['size'] == 0
    assert attr['max_bytes'] == 2048


def test_qattr_full_queue(mq_full):
    attr = mq_full.qattr()
    assert attr['size'] == 5
    assert attr['max_bytes'] == 2048


def test_qsize_empty_queue(mq):
    assert mq.qsize() == 0


def test_qsize_full_queue(mq_full):
    assert mq_full.qsize() == 5
