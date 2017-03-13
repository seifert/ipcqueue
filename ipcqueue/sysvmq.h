
#ifndef __SYSVMQ_H__
#define __SYSVMQ_H__

#include <sys/msg.h>

typedef enum {
    SYSVMQ_OK,
    SYSVMQ_E,
    SYSVMQ_E_VALUE,
    SYSVMQ_E_PERMISSIONS,
    SYSVMQ_E_RESOURCES,
    SYSVMQ_E_DESCRIPTOR,
    SYSVMQ_E_SIGNAL,
    SYSVMQ_E_SIZE,
    SYSVMQ_E_FULL,
    SYSVMQ_E_EMPTY,
} SysVMqResult;

typedef struct {
    size_t size;
    size_t max_bytes;
} SysVMqAttr;

#define MTEXT_BUFFER_SIZE 8192

typedef struct {
    long mtype;
    char mtext[MTEXT_BUFFER_SIZE];
} SysVMqBuffer;

SysVMqResult sysvmq_open(const unsigned int key, int * const mq);

SysVMqResult sysvmq_close(const int mq);

SysVMqResult sysvmq_put(const int mq, const char * const msg,
        const size_t msg_size, const long msg_type,
        const double timeout);

SysVMqResult sysvmq_get(const int mq, char * const buffer,
        size_t * const size, const long msg_type,
        const double timeout);

SysVMqResult sysvmq_get_attr(const int mq, SysVMqAttr * const attr);

SysVMqResult sysvmq_set_max_bytes(const int mq, const size_t max_bytes);

#endif
