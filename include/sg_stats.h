#ifndef SG_STATS_H
#define SG_STATS_H
#include <stddef.h>
#include <stdint.h>
/* Portable serializer interface; firmware integration lives in target/. */
#define SG_JSON_BUFFER_SIZE 128u
#define SG_PORTS 18u
#include "sg_fields.h"
enum sg_kind { SG_NULL, SG_UINT, SG_BOOL, SG_TEXT, SG_TENTHS };
struct sg_value { enum sg_kind kind; uint64_t number; const char *text; size_t length; };
enum sg_scope { SG_SYSTEM, SG_GLOBAL_POE, SG_PORT, SG_LOOP };
struct sg_source {
 void *context;
 /* Snapshot/cache scope before get calls. port is1..18 for SG_PORT, otherwise0. */
 int (*begin)(void *, enum sg_scope, unsigned port);
 /* Return0 with value or -1 for unavailable/read error. Strings remain valid until next call. */
 int (*get)(void *, enum sg_field, struct sg_value *);
 /* Called during port scope:1=PoE,0=no PoE,-1=unknown mapping (abort response). */
 int (*has_poe)(void *);
};
struct sg_sink {
 void *context;
 /* Return accepted byte count,0=no progress,negative=error. Must not block indefinitely. */
 int (*write)(void *, const char *, size_t);
 /* Commit/flush transport; return0 on success. No promise of receipt by client. */
 int (*finish)(void *);
};
struct sg_result { size_t bytes_accepted; unsigned unavailable_fields; unsigned invalid_fields; };
/*0=completed,-1=transport failure,-2=source/scope failure,-3=bad arguments.
 On failure stop immediately; client MUST discard the incomplete response.
 Lifetime: synchronous, source/sink must not recursively invoke the same transport. */
int sg_stats_emit(const struct sg_source *, const struct sg_sink *, struct sg_result *);
#endif
