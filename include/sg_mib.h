#ifndef SG_MIB_H
#define SG_MIB_H
#include <stdint.h>
/* Experimental reader with injected host-order register access.
   No direct MMIO, register writes or callable firmware addresses. */
struct sg_registers {
 void *context;
 /* offset is relative to ASIC register space, not a CPU address.
    Must return 0 ONLY if read succeeded, otherwise nonzero. */
 int (*read32)(void *,uint32_t offset,uint32_t *value);
};
/* ui_port: 1..18; selector: audited allowlist only.
   0=read, -1=argument/unsupported, -2=I/O, -3=unstable pair.
   Leaves *value unchanged on error. Pair is high-low-high, max 3 attempts.
   Hardware latching/clear-on-read behavior still requires bench verification. */
int sg_mib_read(const struct sg_registers *,unsigned ui_port,unsigned selector,uint64_t *value);
#endif
