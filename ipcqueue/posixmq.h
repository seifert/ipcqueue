
#ifndef __POSIXMQ_H__
#define __POSIXMQ_H__

#include <mqueue.h>

typedef enum {
    POSIXMQ_OK,
    POSIXMQ_E,
    POSIXMQ_E_VALUE,
    POSIXMQ_E_PERMISSIONS,
    POSIXMQ_E_RESOURCES,
    POSIXMQ_E_DESCRIPTOR,
    POSIXMQ_E_SIGNAL,
    POSIXMQ_E_SIZE,
    POSIXMQ_E_TIMEOUT,
    POSIXMQ_E_DOESNT_EXIST
} PosixMqResult;

PosixMqResult posixmq_open(const char * const name, int * const mq,
        const size_t maxmsgsize, const size_t maxsize);

PosixMqResult posixmq_close(const int mq);

PosixMqResult posixmq_unlink(const char * const name);

PosixMqResult posixmq_put(const int mq, const char * const msg,
        const size_t msg_size, const unsigned int priority,
        const double timeout);

PosixMqResult posixmq_get(const int mq, char * const buffer,
        size_t * const size, unsigned int * const priority,
        const double timeout);

PosixMqResult posixmq_get_attr(const int mq, struct mq_attr * const attr);

#endif
