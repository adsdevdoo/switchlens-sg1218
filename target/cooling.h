#ifndef SG_COOLING_H
#define SG_COOLING_H
#include <stdint.h>
#define SG_COOL_LIMIT 100u
struct sg_cooling { uint32_t control, direction, data, state, ticks, power; };
void sg_cool_snapshot(struct sg_cooling *);
int sg_cool_get(const struct sg_cooling *, enum sg_field, struct sg_value *);
#endif
