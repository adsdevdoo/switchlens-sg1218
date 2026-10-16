#!/usr/bin/env python3
"""Read-only audit of the supplied image. No network, device I/O or image writes.
Usage: python audit.py /path/to/firmware.bin > evidence.txt
Optional dependency for disassembly: capstone==5.0.9
All offsets include the 16-byte update header. Range ends are exclusive.
"""
import hashlib, pathlib, re, struct, sys, zlib
p=pathlib.Path(sys.argv[1]); b=p.read_bytes()
expected='c9ab17eda7af714f00692d41f440ce84ed0d6c7d678634c364ec1154bb7e3f32'
h=hashlib.sha256(b).hexdigest()
print('SHA256',h)
if h!=expected: raise SystemExit('STOP: unexpected image SHA256')
print('SIZE',len(b),hex(len(b)))
print('HEADER',b[:16].hex(' '))
print('HEADER_WORDS_BE',*[hex(x) for x in struct.unpack('>4I',b[:16])])
c=zlib.crc32(b[0x10:0xf7000]); print('CRC32[0x10:0xf7000]',hex(c),'MATCH',c==int.from_bytes(b[:4],'big'))
print('PADDING_FF[0xd8640:0xf7000]',all(x==255 for x in b[0xd8640:0xf7000]),'SIZE',0xf7000-0xd8640)
for key in [b'snmp',b'community',b'1.3.6.1.2.1',b'Linux',b'eCos',b'FreeRTOS']:
 print('ASCII_CASE_INSENSITIVE',repr(key),[hex(m.start()) for m in re.finditer(re.escape(key),b,re.I)])
print('CLI_MIB_TABLE: names belong to 32-bit selector variants; adjacent 64-bit variants identified separately')
for o in range(0x94170,0x94290,32):
 print(hex(o),b[o:o+28].split(b'\0')[0].decode(),int.from_bytes(b[o+28:o+32],'big'))
print('MIB_JUMP_TABLE at 0x93250')
for k in [0,1,2,4,6,8,9,10,12,14,16,21,31,34,37,40,43]:
 print(k,hex(int.from_bytes(b[0x93250+4*k:0x93254+4*k],'big')))
print('SELECTED_STRINGS')
for o in [0xd3094,0xd5d54,0xd6c60,0xd757c,0xd7590,0xd75a8,0xd75c8,0xd75dc,0xd82f4,0xd6344]:
 print(hex(o),b[o:b.index(0,o)].decode(errors='replace'))
try:
 from capstone import Cs,CS_ARCH_MIPS,CS_MODE_MIPS32,CS_MODE_BIG_ENDIAN
except ImportError:
 print('Disassembly skipped: install capstone==5.0.9'); sys.exit(0)
md=Cs(CS_ARCH_MIPS,CS_MODE_MIPS32|CS_MODE_BIG_ENDIAN);md.skipdata=True
# RAM-mapped code ranges use explicit startup-derived VAs.
ranges=[('startup',0x410,0x720,None),('register_read',0x8768,0x87a0,None),
 ('main_loop',0x26a44,0x26b74,None),('timer_ISR',0x3ccc,0x3dec,0xbf01a094),
 ('route',0x34258,0x34288,None),('statistics_page',0x3963c,0x39960,None),
 ('stat_wrappers',0x51390,0x51a18,None),('logical_physical_port_map',0x4dc3c,0x4dc74,None),
 ('MIB_read',0x157f0,0x15cf0,None),('CLI_MIB',0x2a7a0,0x2a848,None),
 ('upgrade',0x35d20,0x36164,None),('crc32',0x50b8,0x5228,0xbf01b480),
 ('sign_start',0x45718,0x457f4,None),('flash_signature_read',0x4941c,0x49450,None),
 ('sign_end',0x46170,0x46238,None),('sign_init_call',0x26614,0x26680,None),
 ('UDP_init',0x3fcf0,0x3fdd0,None),('UDP_send_call',0x40818,0x40854,None),
 ('UDP_send_wrapper',0x6684,0x66f8,0xbf01ca4c),('HTTP_printf',0x6830,0x6894,0xbf01cbf8)]
for name,start,end,va in ranges:
 print('\nBLOCK',name,hex(start),hex(end))
 va=va if va is not None else 0xbfc08000+start
 for i in md.disasm(b[start:end],va):
  print(f'{start+i.address-va:08x} {i.address:08x} {i.bytes.hex():8s} {i.mnemonic:8s} {i.op_str}')
