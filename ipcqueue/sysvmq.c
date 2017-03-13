
#include <errno.h>
#include <math.h>
#include <stdlib.h>
#include <string.h>
#include <sys/ipc.h>
#include <sys/msg.h>
#include <sys/types.h>

#include "sysvmq.h"

SysVMqResult sysvmq_open(const unsigned int key, int * const mq) {
    int mqdes = msgget(key == 0 ? IPC_PRIVATE : key, 0644 | IPC_CREAT);

    if (mqdes < 0) {
        switch (errno) {
            case EACCES:
                return SYSVMQ_E_PERMISSIONS;
                break;
            case ENOMEM:
            case ENOSPC:
                return SYSVMQ_E_RESOURCES;
                break;
            default:
                return SYSVMQ_E;
        }
    }
    else {
        *mq = mqdes;
        return SYSVMQ_OK;
    }
}

SysVMqResult sysvmq_close(const int mq) {
    if (msgctl(mq, IPC_RMID, NULL) < 0) {
        switch (errno) {
            case EIDRM:
            case EINVAL:
                return SYSVMQ_E_DESCRIPTOR;
                break;
            case EPERM:
                return SYSVMQ_E_PERMISSIONS;
                break;
            default:
                return SYSVMQ_E;
        }
    }
    else {
        return SYSVMQ_OK;
    }
}

SysVMqResult sysvmq_put(const int mq, const char * const msg,
        const size_t msg_size, const long msg_type,
        const double timeout) {

    SysVMqBuffer buffer;
    int res;

    if (msg_size > MTEXT_BUFFER_SIZE) {
        return SYSVMQ_E_SIZE;
    }
    else {
        buffer.mtype = msg_type;
        memcpy(&buffer.mtext, msg, msg_size);
    }

    if (isinf(timeout)) {
        /* Block forever */
        res = msgsnd(mq, &buffer, msg_size, 0);
    }
    else if (timeout == 0.0) {
        /* Don't block */
        res = msgsnd(mq, &buffer, msg_size, IPC_NOWAIT);
    }
    else {
        return SYSVMQ_E_VALUE;
    }

    if (res < 0) {
        switch (errno) {
            case EACCES:
                return SYSVMQ_E_PERMISSIONS;
                break;
            case EAGAIN:
                return SYSVMQ_E_FULL;
                break;
            case EFAULT:
            case EINVAL:
                return SYSVMQ_E_VALUE;
                break;
            case EIDRM:
                return SYSVMQ_E_DESCRIPTOR;
                break;
            case EINTR:
                return SYSVMQ_E_SIGNAL;
                break;
            case ENOMEM:
                return SYSVMQ_E_RESOURCES;
                break;
            default:
                return SYSVMQ_E;
        }
    }
    else {
        return SYSVMQ_OK;
    }
}

SysVMqResult sysvmq_get(const int mq, char * const buffer,
        size_t * const size, const long msg_type,
        const double timeout) {

    SysVMqBuffer msg_buf;
    ssize_t res;

    if (isinf(timeout)) {
        /* Block forever */
        res = msgrcv(mq, &msg_buf, MTEXT_BUFFER_SIZE, msg_type, 0);
    }
    else if (timeout == 0.0) {
        /* Don't block */
        res = msgrcv(mq, &msg_buf, MTEXT_BUFFER_SIZE, msg_type, IPC_NOWAIT);
    }
    else {
        return SYSVMQ_E_VALUE;
    }

    if (res < 0) {
        switch (errno) {
            case E2BIG:
                return SYSVMQ_E_SIZE;
                break;
            case EACCES:
                return SYSVMQ_E_PERMISSIONS;
                break;
            case EFAULT:
            case EINVAL:
                return SYSVMQ_E_VALUE;
                break;
            case EIDRM:
                return SYSVMQ_E_DESCRIPTOR;
                break;
            case EINTR:
                return SYSVMQ_E_SIGNAL;
                break;
            case ENOMSG:
                return SYSVMQ_E_EMPTY;
                break;
            default:
                return SYSVMQ_E;
        }
    }
    else {
        if ((size_t)res > *size) {
            return SYSVMQ_E_SIZE;
        }
        else {
            memcpy(buffer, &msg_buf.mtext, res);
            *size = res;
            return SYSVMQ_OK;
        }
    }
}

SysVMqResult sysvmq_get_attr(const int mq, SysVMqAttr * const attr) {
    struct msqid_ds buf;

    if (msgctl(mq, IPC_STAT, &buf) < 0) {
        switch (errno) {
            case EACCES:
                return SYSVMQ_E_PERMISSIONS;
                break;
            case EINVAL:
                return SYSVMQ_E_DESCRIPTOR;
                break;
            default:
                return SYSVMQ_E;
        }
    }
    else {
        attr->size = buf.msg_qnum;
        attr->max_bytes = buf.msg_qbytes;
        return SYSVMQ_OK;
    }
}

SysVMqResult sysvmq_set_max_bytes(const int mq, const size_t max_bytes) {
    struct msqid_ds buf;

    if (msgctl(mq, IPC_STAT, &buf) < 0) {
        switch (errno) {
            case EACCES:
                return SYSVMQ_E_PERMISSIONS;
                break;
            case EIDRM:
            case EINVAL:
                return SYSVMQ_E_DESCRIPTOR;
                break;
            default:
                return SYSVMQ_E;
        }
    }
    else {
        buf.msg_qbytes = max_bytes;

        if (msgctl(mq, IPC_SET, &buf) < 0) {
            switch (errno) {
                case EACCES:
                case EPERM:
                    return SYSVMQ_E_PERMISSIONS;
                    break;
                case EIDRM:
                case EINVAL:
                    return SYSVMQ_E_DESCRIPTOR;
                    break;
                default:
                    return SYSVMQ_E;
            }
        }
        else {
            return SYSVMQ_OK;
        }
    }
}
