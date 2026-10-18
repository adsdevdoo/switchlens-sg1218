#ifndef SG_BUILD_VERSION_H
#define SG_BUILD_VERSION_H
#ifdef SG_ANONYMOUS_STATS
#define SG_BUILD_ID "v0.1.6"
#elif defined(SG_COOLING)
#define SG_BUILD_ID "v0.1.5"
#else
#define SG_BUILD_ID "experimental-1"
#endif
#endif
