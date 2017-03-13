
#ifndef _POSIX_C_SOURCE
#define _POSIX_C_SOURCE 200112L
#endif

#include <errno.h>
#include <fcntl.h>
#include <math.h>
#include <mqueue.h>
#include <stdlib.h>
#include <sys/stat.h>
#include <sys/time.h>

#include "posixmq.h"


void inline timeout_to_timespec(const double timeout,
        struct timespec * const abs_timeout) {

    struct timeval current_timeval;
    double integral;
    double fractional = modf(timeout, &integral);

    gettimeofday(&current_timeval, NULL);

    abs_timeout->tv_sec = current_timeval.tv_sec + integral;
    abs_timeout->tv_nsec = (
            current_timeval.tv_usec + (fractional * 1000 * 1000)) * 1000;
    if (abs_timeout->tv_nsec > 1000000000) {
        abs_timeout->tv_sec += 1;
        abs_timeout->tv_nsec -= 1000000000;
    }
}

PosixMqResult posixmq_open(const char * const name, int * const mq,
        const size_t maxmsgsize, const size_t maxsize) {

    struct mq_attr attrs = {.mq_maxmsg = maxsize, .mq_msgsize = maxmsgsize};

    mqd_t mqdes = mq_open(name, O_CREAT | O_RDWR, 0644, &attrs);

    if (mqdes < 0) {
        switch (errno) {
            case EACCES:
                return POSIXMQ_E_PERMISSIONS;
                break;
            case EINVAL:
            case ENAMETOOLONG:
            case ENOENT:
                return POSIXMQ_E_VALUE;
                break;
            case EMFILE:
            case ENFILE:
            case ENOMEM:
            case ENOSPC:
                return POSIXMQ_E_RESOURCES;
                break;
            default:
                return POSIXMQ_E;
        }
    }
    else {
        *mq = mqdes;
        return POSIXMQ_OK;
    }
}

PosixMqResult posixmq_close(const int mq) {
    if (mq_close(mq) < 0) {
        switch (errno) {
            case EBADF:
                return POSIXMQ_E_DESCRIPTOR;
                break;
            default:
                return POSIXMQ_E;
        }
    }
    else {
        return POSIXMQ_OK;
    }
}

PosixMqResult posixmq_unlink(const char * const name) {
    if (mq_unlink(name) < 0)     {
        switch (errno) {
            case EACCES:
                return POSIXMQ_E_PERMISSIONS;
                break;
            case ENAMETOOLONG:
                return POSIXMQ_E_VALUE;
                break;
            case ENOENT:
                return POSIXMQ_E_DOESNT_EXIST;
                break;
            default:
                return POSIXMQ_E;
        }
    }
    else {
        return POSIXMQ_OK;
    }
}

PosixMqResult posixmq_put(const int mq, const char * const msg,
        const size_t size, const unsigned int priority,
        const double timeout) {

    ssize_t res;

    if (isinf(timeout)) {
        /* Block forever */
        res = mq_send(mq, msg, size, priority);
    }
    else {
        /* Block with timeout */
        struct timespec abs_timeout;
        timeout_to_timespec(timeout, &abs_timeout);
        res = mq_timedsend(mq, msg, size, priority, &abs_timeout);
    }

    if (res < 0) {
        switch (errno) {
            case EBADF:
                return POSIXMQ_E_DESCRIPTOR;
                break;
            case EINTR:
                return POSIXMQ_E_SIGNAL;
                break;
            case EINVAL:
                return POSIXMQ_E_VALUE;
                break;
            case EMSGSIZE:
                return POSIXMQ_E_SIZE;
                break;
            case ETIMEDOUT:
                return POSIXMQ_E_TIMEOUT;
                break;
            default:
                return POSIXMQ_E;
        }
    }
    else {
        return POSIXMQ_OK;
    }
}

PosixMqResult posixmq_get(const int mq, char * const buffer,
        size_t * const size, unsigned int * const priority,
        const double timeout) {

    ssize_t res;

    if (isinf(timeout)) {
        /* Block forever */
        res = mq_receive(mq, buffer, *size, priority);
    }
    else {
        /* Block with timeout */
        struct timespec abs_timeout;
        timeout_to_timespec(timeout, &abs_timeout);
        res = mq_timedreceive(mq, buffer, *size, priority, &abs_timeout);
    }

    if (res < 0) {
        switch (errno) {
            case EBADF:
                return POSIXMQ_E_DESCRIPTOR;
                break;
            case EINTR:
                return POSIXMQ_E_SIGNAL;
                break;
            case EINVAL:
                return POSIXMQ_E_VALUE;
                break;
            case EMSGSIZE:
                return POSIXMQ_E_SIZE;
                break;
            case ETIMEDOUT:
                return POSIXMQ_E_TIMEOUT;
                break;
            default:
                return POSIXMQ_E;
        }
    }
    else {
        *size = res;
        return POSIXMQ_OK;
    }
}

PosixMqResult posixmq_get_attr(const int mq, struct mq_attr * const attr) {
    if (mq_getattr(mq, attr) < 0) {
        switch (errno) {
            case EBADF:
                return POSIXMQ_E_DESCRIPTOR;
                break;
            default:
                return POSIXMQ_E;
        }
    }
    else {
        return POSIXMQ_OK;
    }
}
