
#define PY_SSIZE_T_CLEAN
#include <Python.h>

#include <errno.h>
#include <fcntl.h>
#include <math.h>
#include <mqueue.h>
#include <stdlib.h>
#include <sys/stat.h>
#include <sys/time.h>

static void inline timeout_to_timespec(const double timeout,
        struct timespec * const abs_timeout) {
    struct timeval current_timeval;
    double integral;
    double fractional = modf(timeout, &integral);

    gettimeofday(&current_timeval, NULL);

    abs_timeout->tv_sec = current_timeval.tv_sec + integral;
    abs_timeout->tv_nsec = (
            current_timeval.tv_usec + (fractional * 1000 * 1000)) * 1000;
    if (abs_timeout->tv_nsec > 999999999) {
        long sec = abs_timeout->tv_nsec / 1000000000;
        abs_timeout->tv_sec += sec;
        abs_timeout->tv_nsec -= sec * 1000000000;
    }
}

static PyObject* posixmq_open(PyObject *self, PyObject *args) {
    const char * name;
    struct mq_attr attrs;
    mqd_t mqdescr;

    if (!PyArg_ParseTuple(args, "snn",
            &name, &attrs.mq_msgsize, &attrs.mq_maxmsg)) {
        return NULL;
    }

    if ((mqdescr = mq_open(name, O_CREAT | O_RDWR, 0644, &attrs)) == -1) {
        return PyErr_SetFromErrno(PyExc_OSError);
    }
    return PyLong_FromLong(mqdescr);
}

static PyObject* posixmq_close(PyObject *self, PyObject *args) {
    const int mqdescr;

    if (!PyArg_ParseTuple(args, "i", &mqdescr)) {
        return NULL;
    }

    if (mq_close(mqdescr) == -1) {
        return PyErr_SetFromErrno(PyExc_OSError);
    }
    Py_RETURN_NONE;
}

static PyObject* posixmq_unlink(PyObject *self, PyObject *args) {
    const char * name;

    if (!PyArg_ParseTuple(args, "s", &name)) {
        return NULL;
    }

    if (mq_unlink(name) == -1) {
        return PyErr_SetFromErrno(PyExc_OSError);
    }
    Py_RETURN_NONE;
}

#if defined(PY_MAJOR_VERSION) && PY_MAJOR_VERSION == 2
#define ARGS_PUT_FMT "is*Id"
#elif defined(PY_MAJOR_VERSION) && PY_MAJOR_VERSION == 3
#define ARGS_PUT_FMT "iy*Id"
#endif

static PyObject* posixmq_put(PyObject *self, PyObject *args) {
    const int mqdescr;
    Py_buffer msg = {.obj=NULL};
    const unsigned int priority;
    const double timeout;
    struct timespec abs_timeout;
    PyObject * res = NULL;

    if (!PyArg_ParseTuple(args, ARGS_PUT_FMT,
            &mqdescr, &msg, &priority, &timeout)) {
        goto cleanup;
    }

    if (isinf(timeout)) {
        if (mq_send(mqdescr, msg.buf, msg.len, priority) == -1) {
            PyErr_SetFromErrno(PyExc_OSError);
            goto cleanup;
        }
    }
    else {
        timeout_to_timespec(timeout, &abs_timeout);
        if (mq_timedsend(mqdescr, msg.buf, msg.len, priority, &abs_timeout)
                == -1) {
            PyErr_SetFromErrno(PyExc_OSError);
            goto cleanup;
        }
    }
    res = Py_None;
    Py_INCREF(res);

cleanup:
    if (NULL != msg.obj) {
        PyBuffer_Release(&msg);
    }

    return res;
}

static PyObject* posixmq_get(PyObject *self, PyObject *args) {
    const int mqdescr;
    const double timeout;
    const size_t maxmsgsize;
    char * buf = NULL;
    struct timespec abs_timeout;
    ssize_t msgsize;
    PyObject * res = NULL;

    if (!PyArg_ParseTuple(args, "idn", &mqdescr, &timeout, &maxmsgsize)) {
        return NULL;
    }

    if (NULL == (buf = (char *) malloc(maxmsgsize))) {
        return PyErr_NoMemory();
    }
    if (isinf(timeout)) {
        msgsize = mq_receive(mqdescr, buf, maxmsgsize, NULL);
    }
    else {
        timeout_to_timespec(timeout, &abs_timeout);
        msgsize = mq_timedreceive(mqdescr, buf, maxmsgsize, NULL, &abs_timeout);
    }
    if (-1 == msgsize) {
        PyErr_SetFromErrno(PyExc_OSError);
        goto cleanup;
    }
    res = PyBytes_FromStringAndSize(buf, msgsize);

cleanup:
    free(buf);

    return res;
}

static PyObject* posixmq_get_attr(PyObject *self, PyObject *args) {
    const int mqdescr;
    struct mq_attr attr;
    PyObject * res = NULL;
    PyObject * size = NULL;
    PyObject * max_size = NULL;
    PyObject * max_msgbytes = NULL;

    if (!PyArg_ParseTuple(args, "i", &mqdescr)) {
        return NULL;
    }

    if (0 != mq_getattr(mqdescr, &attr)) {
        return PyErr_SetFromErrno(PyExc_OSError);
    }
    if ((NULL == (size = PyLong_FromLong(attr.mq_curmsgs)))
            || (NULL == (max_size = PyLong_FromLong(attr.mq_maxmsg)))
            || (NULL == (max_msgbytes = PyLong_FromLong(attr.mq_msgsize)))
            || (NULL == (res = PyDict_New()))) {
        goto error;
    }
    if ((0 != PyDict_SetItemString(res, "size", size))
            || (0 != PyDict_SetItemString(res, "max_size", max_size))
            || (0 != PyDict_SetItemString(res, "max_msgbytes", max_msgbytes))) {
        goto error;
    }
    goto cleanup;

error:
    Py_XDECREF(res);
cleanup:
    Py_XDECREF(size);
    Py_XDECREF(max_size);
    Py_XDECREF(max_msgbytes);

    return res;
}

static PyMethodDef PosixMqMethods[] = {
    {"posixmq_open",  posixmq_open, METH_VARARGS, NULL},
    {"posixmq_close",  posixmq_close, METH_VARARGS, NULL},
    {"posixmq_unlink",  posixmq_unlink, METH_VARARGS, NULL},
    {"posixmq_put",  posixmq_put, METH_VARARGS, NULL},
    {"posixmq_get",  posixmq_get, METH_VARARGS, NULL},
    {"posixmq_get_attr",  posixmq_get_attr, METH_VARARGS, NULL},
    {NULL, NULL, 0, NULL}
};

#if defined(PY_MAJOR_VERSION) && PY_MAJOR_VERSION == 2
    PyMODINIT_FUNC init_posixmq(void) {
        if (NULL == Py_InitModule("ipcqueue._posixmq", PosixMqMethods)) {
            return;
        }
    }
#elif defined(PY_MAJOR_VERSION) && PY_MAJOR_VERSION == 3
    static struct PyModuleDef posixmqmodule = {
        PyModuleDef_HEAD_INIT,
        "ipcqueue._posixmq",
        NULL,
        -1,
        PosixMqMethods
    };

    PyMODINIT_FUNC PyInit__posixmq(void) {
        PyObject *module;
        if (NULL == (module = PyModule_Create(&posixmqmodule))) {
            return NULL;
        }
        return module;
    }
#endif
