/* Called at the original outer HTTP callback entry, before any session read or
 * refresh. Parser BF01D05C retains the raw request at +0x88, the target pointer
 * at +0x8c and a NUL-terminated path (without query) at +8. Checking only the
 * parsed path would incorrectly admit queries; checking only method==1 would
 * admit the stock parser's three-byte GET prefix matches. No mutable globals. */
#include <stdint.h>

int sg_is_anonymous_stats(const void *request)
{
    static const char line_prefix[] = "GET /stats.json ";
    static const char path[] = "/stats.json";
    const unsigned char *r = request;
    const unsigned char *raw;
    unsigned i;
    if (!r || *(const uint32_t *)(r + 4) != 1) return 0;
    raw = (const unsigned char *)(uintptr_t)*(const uint32_t *)(r + 0x88);
    if (!raw || *(const uint32_t *)(r + 0x8c) != (uintptr_t)(raw + 4)) return 0;
    for (i = 0; i < sizeof(line_prefix) - 1; i++)
        if (raw[i] != (unsigned char)line_prefix[i]) return 0;
    for (i = 0; i < sizeof(path); i++)
        if (r[8 + i] != (unsigned char)path[i]) return 0;
    return 1;
}
