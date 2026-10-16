#!/usr/bin/env python3
"""Offline branch tracer, NOT a device emulator. No device I/O or firmware writes.
Usage: python audit_mib.py firmware.bin [openwrt-dsa.c] > mib-map.json
Traces switch cases only; intercepts the register-read helper with synthetic words.
Argument validation/startup/MMIO hardware are NOT emulated. Requires capstone5.
"""
import sys,json,struct,hashlib,re
from pathlib import Path
from capstone import Cs,CS_ARCH_MIPS,CS_MODE_MIPS32,CS_MODE_BIG_ENDIAN
b=Path(sys.argv[1]).read_bytes();h=hashlib.sha256(b).hexdigest()
if h!='c9ab17eda7af714f00692d41f440ce84ed0d6c7d678634c364ec1154bb7e3f32':raise SystemExit('Unexpected image')
m=Cs(CS_ARCH_MIPS,CS_MODE_MIPS32|CS_MODE_BIG_ENDIAN)
code={i.address:i for i in m.disasm(b[0x159c8:0x15cd4],0xbfc1d9c8)}
ref={};refmeta=None
if len(sys.argv)>2:
 raw=Path(sys.argv[2]).read_bytes();src=raw.decode();table=src.split('const struct rtl83xx_mib_desc rtl83xx_mib[] = {',1)[1].split('};',1)[0]
 for size,off,name in re.findall(r'MIB_DESC\((\d+), (0x[0-9a-f]+), "([^"]+)"\)',table):
  ref[252-int(off,16)]={'name':name,'words':int(size)}
 refmeta={'url':'https://raw.githubusercontent.com/openwrt/openwrt/openwrt-24.10/target/linux/realtek/files-6.6/drivers/net/dsa/rtl83xx/dsa.c','sha256':hashlib.sha256(raw).hexdigest(),'mapping':'low offset = 252 - descriptor.offset; high = low - 4','status':'Names are external RTL838x comparison, not proof of hardware behavior in this switch.'}
def trace(entry):
 r={'$zero':0,'$s0':0x1200,'$s1':0,'$s2':0x100000,'$sp':0x200000,'$a0':0};mem={0x200000+x:0 for x in [0x10,0x14,0x18,0x1c,0x20]};reads=[];writes=[]
 def get(x):return r[x] if x.startswith('$') else int(x,0)
 def addr(s):
  mm=re.fullmatch(r'(-?(?:0x[0-9a-f]+|\d+))?\((\$\w+)\)',s);assert mm,s
  return r[mm[2]]+int(mm[1] or '0',0)
 def step(i):
  a=i.op_str.split(', ');op=i.mnemonic
  if op=='nop':return
  if op=='move':r[a[0]]=get(a[1])
  elif op=='addiu':r[a[0]]=(get(a[1])+get(a[2]))&0xffffffff
  elif op=='addu':r[a[0]]=(get(a[1])+get(a[2]))&0xffffffff
  elif op=='sw':
   loc=addr(a[1]);mem[loc]=get(a[0]);writes.append(loc)
  elif op=='lw':r[a[0]]=mem[addr(a[1])]
  else:raise ValueError((hex(i.address),op,i.op_str))
 pc=entry
 for count in range(100):
  if pc==0xbfc1dcd4:break
  i=code[pc]
  if i.mnemonic in ['j','jal']:
   target=int(i.op_str,0);step(code[pc+4])
   if i.mnemonic=='jal':
    assert target==0xbfc1d7f0
    offset=r['$a1']-0x1200;reads.append(offset);mem[r['$a2']]=0xa5000000+offset;r['$v0']=0;pc+=8
   else:pc=target
  else:step(i);pc+=4
 else:raise ValueError('trace limit')
 return reads,[x-0x100000 for x in writes if x in [0x100000,0x100004]],r['$v1']
rows=[]
for sel in range(126):
 entry=struct.unpack_from('>I',b,0x93250+4*sel)[0];reads,writes,status=trace(entry)
 row={'selector':sel,'entry_file':hex(entry-0xbfc08000),'register_offsets':[hex(x) for x in reads],'output_word_offsets_written':writes,'return_status':status}
 if not reads:row['classification']='no_read_no_output'
 elif set(writes)!={0,4}:row['classification']='incomplete_output_EXCLUDE'
 elif sel in [1,9]:row['classification']='two_word_counter'
 elif len(reads)>1 and sel not in [0,8]:row['classification']='sum_modulo_2_32'
 else:row['classification']='single_word_counter'
 if reads:row['rtl838x_external_names']=[ref[x]['name'] if x in ref else None for x in reads]
 rows.append(row)
assert rows[1]['register_offsets']==['0x4','0x0']
assert rows[9]['register_offsets']==['0xc','0x8']
assert rows[125]['register_offsets']==['0x10']
assert rows[58]['output_word_offsets_written']==[0]
assert rows[3]['classification']=='no_read_no_output'
print(json.dumps({'image_sha256':h,'method':'Constrained static branch tracing with synthetic register reads; not hardware execution','reference':refmeta,'selectors':rows},indent=2))
