
try:
    from Queue import Full, Empty
except ImportError:
    from queue import Full, Empty
import time

import pytest

from ipcqueue.posixmq import Queue, QueueError


@pytest.fixture(scope='function')
def mq():
    mq = Queue('/test_posixmq', maxsize=5, maxmsgsize=2048)
    yield mq
    mq.close()
    mq.unlink()


@pytest.fixture(scope='function')
def mq_full(mq):
    mq.put_nowait([1, 'test message'])
    mq.put_nowait([2, 'test message'])
    mq.put_nowait([3, 'test message'])
    mq.put_nowait([4, 'test message'])
    mq.put_nowait([5, 'test message'])
    yield mq


@pytest.mark.parametrize(
    'name', ['', 'test_posixmq', '/' + 'a' * 256],
    ids=['empty', 'no-initial-slash', 'too-long']
)
def test_create_fail_when_invalid_name(name):
    with pytest.raises(QueueError) as excinfo:
        mq = Queue(name)
        mq.close()
        mq.unlink()
    assert excinfo.value.errno == QueueError.INVALID_VALUE


@pytest.mark.parametrize(
    'maxsize', [0, (2 ** 31) - 1], ids=['zero', 'too-big']
)
def test_create_fail_when_invalid_maxsize(maxsize):
    with pytest.raises(QueueError) as excinfo:
        mq = Queue('/test_posixmq', maxsize=maxsize)
        mq.close()
        mq.unlink()
    assert excinfo.value.errno == QueueError.INVALID_VALUE


def test_close_fail_when_invalid_descriptor():
    mq = Queue('/test_posixmq')
    try:
        mq.close()
        with pytest.raises(QueueError) as excinfo:
            mq.close()
        assert excinfo.value.errno == QueueError.INVALID_DESCRIPTOR
    finally:
        mq.unlink()


def test_unlink_fail_when_does_not_exist():
    mq = Queue('/test_posixmq')
    mq.close()
    mq.unlink()
    with pytest.raises(QueueError) as excinfo:
        mq.unlink()
    assert excinfo.value.errno == QueueError.DOES_NOT_EXIST


def test_put_get_nowait(mq):
    mq.put_nowait([123, 'test message'])
    mq.put_nowait([456, 'test message'])
    assert mq.get_nowait() == [123, 'test message']
    assert mq.get_nowait() == [456, 'test message']


def test_put_get_nowait_priority(mq):
    mq.put_nowait([123, 'test message'], priority=0)
    mq.put_nowait([456, 'test message'], priority=1)
    assert mq.get_nowait() == [456, 'test message']
    assert mq.get_nowait() == [123, 'test message']


def test_put_get_nowait_pickle_protocol(mq):
    mq.put_nowait([123, 'test message'], pickle_protocol=0)
    mq.put_nowait([456, 'test message'], pickle_protocol=1)
    assert mq.get_nowait() == [123, 'test message']
    assert mq.get_nowait() == [456, 'test message']


def test_put_nowait_fail_when_full_queue(mq_full):
    with pytest.raises(Full):
        mq_full.put_nowait([6, 'test message'])


def test_get_nowait_fail_when_empty_queue(mq):
    with pytest.raises(Empty):
        mq.get_nowait()


def test_put_timeout(mq_full):
    start_time = time.time()
    with pytest.raises(Full):
        mq_full.put([6, 'test message'], timeout=0.25)
    time_pass = time.time() - start_time
    assert time_pass >= 0.25


def test_get_timeout(mq):
    start_time = time.time()
    with pytest.raises(Empty):
        mq.get(timeout=0.25)
    time_pass = time.time() - start_time
    assert time_pass >= 0.25


def test_put_block_forever(mq_full, alarm_handler):
    alarm_handler(1)
    start_time = time.time()
    with pytest.raises(QueueError) as excinfo:
        mq_full.put([6, 'test message'])
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
        mq.put_nowait(['a' * 4096])
    assert excinfo.value.errno == QueueError.TOO_BIG_MESSAGE


def test_qattr_empty_queue(mq):
    attr = mq.qattr()
    assert attr['max_size'] == 5
    assert attr['max_msgbytes'] == 2048
    assert attr['size'] == 0


def test_qattr_full_queue(mq_full):
    attr = mq_full.qattr()
    assert attr['max_size'] == 5
    assert attr['max_msgbytes'] == 2048
    assert attr['size'] == 5


def test_qsize_empty_queue(mq):
    assert mq.qsize() == 0


def test_qsize_full_queue(mq_full):
    assert mq_full.qsize() == 5
