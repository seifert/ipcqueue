
#define PY_SSIZE_T_CLEAN
#include <Python.h>

#include <errno.h>
#include <stdlib.h>
#include <string.h>
#include <sys/ipc.h>
#include <sys/msg.h>
#include <sys/types.h>

typedef struct {
    long mtype;
    char mtext[1];
} SysVMqMsgBuffer;

static PyObject* sysvmq_open(PyObject *self, PyObject *args) {
    const key_t key;
    key_t mqdescr;

    if (!PyArg_ParseTuple(args, "i", &key)) {
        return NULL;
    }
    if (key < 0) {
        errno = EINVAL;
        return PyErr_SetFromErrno(PyExc_OSError);
    }

    mqdescr = msgget(key == 0 ? IPC_PRIVATE : key, 0644 | IPC_CREAT);
    if (-1 == mqdescr) {
        return PyErr_SetFromErrno(PyExc_OSError);
    }
    return PyLong_FromLong(mqdescr);
}

static PyObject* sysvmq_close(PyObject *self, PyObject *args) {
    const int mqdescr;

    if (!PyArg_ParseTuple(args, "i", &mqdescr)) {
        return NULL;
    }

    if (msgctl(mqdescr, IPC_RMID, NULL) == -1) {
        return PyErr_SetFromErrno(PyExc_OSError);
    }
    Py_RETURN_NONE;
}

#if defined(PY_MAJOR_VERSION) && PY_MAJOR_VERSION == 2
#define ARGS_PUT_FMT "is*li"
#elif defined(PY_MAJOR_VERSION) && PY_MAJOR_VERSION == 3
#define ARGS_PUT_FMT "iy*lp"
#endif

static PyObject* sysvmq_put(PyObject *self, PyObject *args) {
    const int mqdescr;
    Py_buffer msg = {.obj=NULL};
    const long msg_type;
    const int block;
    SysVMqMsgBuffer * msg_buffer = NULL;
    PyObject * res = NULL;

    if (!PyArg_ParseTuple(args, ARGS_PUT_FMT,
            &mqdescr, &msg, &msg_type, &block)) {
        goto cleanup;
    }
    if (msg_type < 1) {
        errno = EINVAL;
        PyErr_SetFromErrno(PyExc_OSError);
        goto cleanup;
    }

    msg_buffer = (SysVMqMsgBuffer *) malloc(sizeof(SysVMqMsgBuffer) + msg.len);
    if (NULL == msg_buffer) {
        PyErr_NoMemory();
        goto cleanup;
    }
    msg_buffer->mtype = msg_type;
    memcpy(msg_buffer->mtext, msg.buf, msg.len);
    if (block) {
        if (msgsnd(mqdescr, msg_buffer, msg.len, 0) == -1) {
            PyErr_SetFromErrno(PyExc_OSError);
            goto cleanup;
        }
    }
    else {
        if (msgsnd(mqdescr, msg_buffer, msg.len, IPC_NOWAIT) == -1) {
            PyErr_SetFromErrno(PyExc_OSError);
            goto cleanup;
        }
    }
    res = Py_None;
    Py_INCREF(res);

cleanup:
    free(msg_buffer);
    if (NULL != msg.obj) {
        PyBuffer_Release(&msg);
    }

    return res;
}

#if defined(PY_MAJOR_VERSION) && PY_MAJOR_VERSION == 2
#define ARGS_GET_FMT "ili"
#elif defined(PY_MAJOR_VERSION) && PY_MAJOR_VERSION == 3
#define ARGS_GET_FMT "ilp"
#endif

static PyObject* sysvmq_get(PyObject *self, PyObject *args) {
    const int mqdescr;
    const long msg_type;
    const int block;
    struct msqid_ds msq_info_buffer;
    size_t buf_size;
    SysVMqMsgBuffer * msg_buffer = NULL;
    int msgsize;
    PyObject * res = NULL;

    if (!PyArg_ParseTuple(args, ARGS_GET_FMT, &mqdescr, &msg_type, &block)) {
        goto cleanup;
    }

    if (msgctl(mqdescr, IPC_STAT, &msq_info_buffer) == -1) {
        PyErr_SetFromErrno(PyExc_OSError);
        goto cleanup;
    }
    buf_size = msq_info_buffer.msg_qbytes;
    msg_buffer = (SysVMqMsgBuffer *) malloc(sizeof(SysVMqMsgBuffer) + buf_size);
    if (NULL == msg_buffer) {
        PyErr_NoMemory();
        goto cleanup;
    }
    if (block) {
        msgsize = msgrcv(mqdescr, msg_buffer, buf_size, msg_type, 0);
        if (msgsize == -1) {
            PyErr_SetFromErrno(PyExc_OSError);
            goto cleanup;
        }
    }
    else {
        msgsize = msgrcv(mqdescr, msg_buffer, buf_size, msg_type, IPC_NOWAIT);
        if (msgsize == -1) {
            PyErr_SetFromErrno(PyExc_OSError);
            goto cleanup;
        }
    }
    res = PyBytes_FromStringAndSize(msg_buffer->mtext, msgsize);

cleanup:
    free(msg_buffer);

    return res;
}

static PyObject* sysvmq_get_attr(PyObject *self, PyObject *args) {
    const int mqdescr;
    struct msqid_ds buf;
    PyObject * res = NULL;
    PyObject * size = NULL;
    PyObject * max_bytes = NULL;

    if (!PyArg_ParseTuple(args, "i", &mqdescr)) {
        return NULL;
    }

    if (msgctl(mqdescr, IPC_STAT, &buf) == -1) {
        return PyErr_SetFromErrno(PyExc_OSError);
    }
    if ((NULL == (size = PyLong_FromLong(buf.msg_qnum)))
            || (NULL == (max_bytes = PyLong_FromLong(buf.msg_qbytes)))
            || (NULL == (res = PyDict_New()))) {
        goto error;
    }
    if ((0 != PyDict_SetItemString(res, "size", size))
            || (0 != PyDict_SetItemString(res, "max_bytes", max_bytes))) {
        goto error;
    }
    goto cleanup;

error:
    Py_XDECREF(res);
cleanup:
    Py_XDECREF(size);
    Py_XDECREF(max_bytes);

    return res;
}

static PyObject* sysvmq_set_max_bytes(PyObject *self, PyObject *args) {
    const int mqdescr;
    const size_t max_bytes;
    struct msqid_ds buf;

    if (!PyArg_ParseTuple(args, "in", &mqdescr, &max_bytes)) {
        return NULL;
    }

    if (msgctl(mqdescr, IPC_STAT, &buf) == -1) {
        return PyErr_SetFromErrno(PyExc_OSError);
    }
    buf.msg_qbytes = max_bytes;
    if (msgctl(mqdescr, IPC_SET, &buf) == -1) {
        return PyErr_SetFromErrno(PyExc_OSError);
    }
    Py_RETURN_NONE;
}

static PyMethodDef SysVMqMethods[] = {
    {"sysvmq_open",  sysvmq_open, METH_VARARGS, NULL},
    {"sysvmq_close",  sysvmq_close, METH_VARARGS, NULL},
    {"sysvmq_put",  sysvmq_put, METH_VARARGS, NULL},
    {"sysvmq_get",  sysvmq_get, METH_VARARGS, NULL},
    {"sysvmq_get_attr",  sysvmq_get_attr, METH_VARARGS, NULL},
    {"sysvmq_set_max_bytes",  sysvmq_set_max_bytes, METH_VARARGS, NULL},
    {NULL, NULL, 0, NULL}
};

#if defined(PY_MAJOR_VERSION) && PY_MAJOR_VERSION == 2
    PyMODINIT_FUNC init_sysvmq(void) {
        if (NULL == Py_InitModule("ipcqueue._sysvmq", SysVMqMethods)) {
            return;
        }
    }
#elif defined(PY_MAJOR_VERSION) && PY_MAJOR_VERSION == 3
    static struct PyModuleDef sysvmqqmodule = {
        PyModuleDef_HEAD_INIT,
        "ipcqueue._sysvmq",
        NULL,
        -1,
        SysVMqMethods
    };

    PyMODINIT_FUNC PyInit__sysvmq(void) {
        PyObject *module;
        if (NULL == (module = PyModule_Create(&sysvmqqmodule))) {
            return NULL;
        }
        return module;
    }
#endif
