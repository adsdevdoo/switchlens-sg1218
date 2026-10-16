#!/usr/bin/env python3
"""Read-only follow-up. Usage: python audit_http.py firmware.bin > http-evidence.txt"""
import sys,hashlib,base64,struct
from pathlib import Path
from capstone import Cs,CS_ARCH_MIPS,CS_MODE_MIPS32,CS_MODE_BIG_ENDIAN
b=Path(sys.argv[1]).read_bytes()
h=hashlib.sha256(b).hexdigest();print('SHA256',h)
if h!='c9ab17eda7af714f00692d41f440ce84ed0d6c7d678634c364ec1154bb7e3f32':raise SystemExit('Unexpected image')
k=base64.b64decode(b[0xcb400:0xcb4c8],validate=True)
print('KEY header',k[:20].hex(),'decoded_length',len(k),'bits/exponent',struct.unpack('<II',k[12:20]))
print('SIGN digest prefix at cb3f0',b[0xcb3f0:0xcb400].hex())
for o in [0xd5924,0xd6e80,0xd6e8c]:print(hex(o),repr(b[o:b.index(0,o)]))
m=Cs(CS_ARCH_MIPS,CS_MODE_MIPS32|CS_MODE_BIG_ENDIAN);m.skipdata=True
for name,s,e in [('http_raw',0x66f8,0x6894),('http_begin_end',0x33278,0x33314),('tcp_send',0x30a64,0x30ad0),('format_dispatch',0x2b9dc,0x2b9fc),('router_prefix',0x33740,0x33808),('statistics_route',0x34258,0x34288),('poe_class_status',0x3ad00,0x3adc8),('sign_input',0x45718,0x457f4),('sign_digest',0x46004,0x4619c),('uid_copy',0x844c,0x8480)]:
 print('\nBLOCK',name,hex(s),hex(e))
 v=s+0xbfc08000 if s>=0x8178 else s-0x3160+0xbf019528
 for i in m.disasm(b[s:e],v):print(f'{s+i.address-v:08x} {i.address:08x} {i.mnemonic:8} {i.op_str}')
