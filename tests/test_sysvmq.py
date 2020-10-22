
import errno
try:
    from Queue import Full, Empty
except ImportError:
    from queue import Full, Empty
import time

import pytest

from ipcqueue.serializers import RawSerializer
from ipcqueue.sysvmq import Queue


@pytest.fixture(scope='function')
def mq():
    mq = Queue(key=None, max_bytes=2048, serializer=RawSerializer)
    yield mq
    mq.close()


@pytest.fixture(scope='function')
def mq_full(mq):
    mq.put_nowait(b'a'*384)
    mq.put_nowait(b'a'*384)
    mq.put_nowait(b'a'*384)
    mq.put_nowait(b'a'*384)
    mq.put_nowait(b'a'*384)
    yield mq


def test_create_fail_when_invalid_key():
    with pytest.raises(OSError) as excinfo:
        mq = Queue(-1)
        mq.close()
    assert excinfo.value.errno == errno.EINVAL


def test_close_fail_when_invalid_descriptor():
    mq = Queue(0)
    mq.close()
    with pytest.raises(OSError) as excinfo:
        mq.close()
    assert excinfo.value.errno == errno.EINVAL


def test_put_get_nowait(mq):
    mq.put_nowait(b'test-message1')
    mq.put_nowait(b'test-message2')
    mq.put_nowait(b'test-message3')
    assert mq.get_nowait() == b'test-message1'
    assert mq.get_nowait() == b'test-message2'
    assert mq.get_nowait() == b'test-message3'


def test_put_get_nowait_msgtype(mq):
    mq.put_nowait(b'test message1', msg_type=1)
    mq.put_nowait(b'test message2', msg_type=2)
    mq.put_nowait(b'test message3', msg_type=1)
    assert mq.get_nowait(msg_type=2) == b'test message2'
    assert mq.get_nowait(msg_type=0) == b'test message1'
    assert mq.get_nowait(msg_type=1) == b'test message3'


def test_put_nowait_fail_when_full_queue(mq_full):
    with pytest.raises(Full):
        mq_full.put_nowait(b'a'*384)


def test_get_nowait_fail_when_empty_queue(mq):
    with pytest.raises(Empty):
        mq.get_nowait()


def test_put_block_forever(mq_full, alarm_handler):
    alarm_handler(1)
    start_time = time.time()
    with pytest.raises(OSError) as excinfo:
        mq_full.put(b'a'*384)
    assert time.time() - start_time > 1
    assert excinfo.value.errno == errno.EINTR


def test_get_block_forever(mq, alarm_handler):
    alarm_handler(1)
    start_time = time.time()
    with pytest.raises(OSError) as excinfo:
        mq.get()
    assert time.time() - start_time > 1
    assert excinfo.value.errno == errno.EINTR


def test_put_fail_when_big_message(mq):
    with pytest.raises(Full):
        mq.put_nowait(b'a'*(2049))


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
