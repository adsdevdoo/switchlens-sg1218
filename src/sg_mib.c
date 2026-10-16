#include "sg_mib.h"
struct mapping { unsigned char selector,offset; };
/* Verified offsets: ../research/mib-map.json; image SHA256 in ../research/REPORT.txt.
   Deliberately excludes aliases, sums, no-ops and incomplete selector 58. */
static const struct mapping map[]={
 {2,0x14},{4,0x18},{6,0x1c},{10,0x20},{12,0x24},{14,0x28},
 {16,0x2c},{17,0x30},{18,0x34},{19,0x38},{20,0x3c},{21,0x40},
 {22,0x44},{23,0x48},{24,0x4c},{25,0x50},{26,0x54},
 {31,0x60},{35,0x68},{36,0x64},{38,0x74},{39,0x70},
 {40,0x78},{43,0x7c},{46,0x80},{48,0x88},{49,0x84},
 {51,0x90},{52,0x8c},{54,0x98},{55,0x94},{57,0xa0},
 {60,0xa8},{61,0xa4},{63,0xb0},{64,0xac},{65,0x6c},
 {66,0xb8},{67,0xb4},{84,0xbc},{125,0x10}
};
int sg_mib_read(const struct sg_registers *io,unsigned port,unsigned selector,uint64_t *value){
 if(!io||!io->read32||!value||port<1||port>18)return -1;
 unsigned physical=port<=16?port-1:port+7;
 uint32_t base=0x1200u+(physical<<8),lo,hi,again;
 if(selector==1||selector==9){
  uint32_t high_offset=base+(selector==1?0:8);
  for(unsigned attempt=0;attempt<3;attempt++){
   if(io->read32(io->context,high_offset,&hi)||io->read32(io->context,high_offset+4,&lo)||io->read32(io->context,high_offset,&again))return -2;
   if(hi==again){*value=((uint64_t)hi<<32)|lo;return 0;}
  }return -3;
 }
 for(unsigned i=0;i<sizeof map/sizeof map[0];i++)if(map[i].selector==selector){
  if(io->read32(io->context,base+map[i].offset,&lo))return -2;
  *value=lo;return 0;
 }
 return -1;
}
