
import signal

import pytest


def alarm(seconds):
    signal.alarm(seconds)


@pytest.fixture(scope='function')
def alarm_handler():
    def sig_alarm(signum, frame):
        pass
    signal.signal(signal.SIGALRM, sig_alarm)
    yield alarm
    signal.signal(signal.SIGALRM, signal.SIG_DFL)
