#include "sg_mib.h"
#include <assert.h>
#include <stdio.h>
struct fake {unsigned calls,fail_at,n;uint32_t offsets[9],values[9];};
static int read32(void *p,uint32_t offset,uint32_t *out){struct fake *f=p;assert(f->calls<f->n);unsigned i=f->calls++;assert(offset==f->offsets[i]);if(f->calls==f->fail_at)return -1;*out=f->values[i];return 0;}
int main(void){
 uint64_t value=99;struct fake f={0};struct sg_registers io={&f,read32};
 assert(sg_mib_read(&io,0,1,&value)==-1&&value==99);
 assert(sg_mib_read(&io,19,1,&value)==-1&&value==99);
 assert(sg_mib_read(&io,1,58,&value)==-1&&f.calls==0);
 assert(sg_mib_read(&io,1,3,&value)==-1&&f.calls==0);
 f=(struct fake){.n=3,.offsets={0x1200,0x1204,0x1200},.values={0xffffffff,0xffffffff,0xffffffff}};
 assert(sg_mib_read(&io,1,1,&value)==0&&value==UINT64_MAX&&f.calls==3);
 f=(struct fake){.n=6,.offsets={0x2a08,0x2a0c,0x2a08,0x2a08,0x2a0c,0x2a08},.values={1,0,2,2,1,2}};
 assert(sg_mib_read(&io,17,9,&value)==0&&value==UINT64_C(0x200000001)&&f.calls==6);
 f=(struct fake){.n=1,.offsets={0x2b10},.values={123}};
 assert(sg_mib_read(&io,18,125,&value)==0&&value==123);
 for(unsigned fail=1;fail<=3;fail++){
  f=(struct fake){.n=3,.fail_at=fail,.offsets={0x1200,0x1204,0x1200},.values={1,2,1}};
  value=99;assert(sg_mib_read(&io,1,1,&value)==-2&&value==99&&f.calls==fail);
 }
 f=(struct fake){.n=9,.offsets={0x1200,0x1204,0x1200,0x1200,0x1204,0x1200,0x1200,0x1204,0x1200},.values={0,1,1,1,2,2,2,3,3}};
 value=99;assert(sg_mib_read(&io,1,1,&value)==-3&&value==99&&f.calls==9);
 puts("MIB: mapping, 64-bit rollover, read errors, bounded retries, unsupported selectors: PASS");return 0;
}
