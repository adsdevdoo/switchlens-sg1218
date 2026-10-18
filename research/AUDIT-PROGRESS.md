**English** | [Русский](AUDIT-PROGRESS.ru.md)

# Audit checkpoint — 18 October 2026

## Scope and current status
Owner-authorized security review of TL-SG1218MPE(UN) V5 / SwitchLens v0.1.4.
This file records evidence, conclusions, limitations and next steps for resuming work.
Local execution environment is disconnected. This checkpoint is saved through GitHub;
no new local file or hardware execution is claimed.

## Confirmed on the owner's device
Owner supplied a successful run of Confirm-TddpHandshake.ps1 at
2026-10-18T07:55:18.0610129Z: direct MAC query had no matching reply;
control request opcode 12 received opcode 4/type 1; subsequent opcode 15
returned the expected MAC, without credentials. No configuration writes were sent.
This establishes live handshake/read access, not physical flash-write success.
The owner reports having sent an earlier report to TP-Link. The assistant has not sent mail.

## Binary acquired again in this session
Repository: adsdevdoo/switchlens-sg1218.
Ref: e72ffeedce0884811b95a13d4956372454fb3e77.
Path: vendor/tp-link/tl-sg1218mpe-v5/20230616/TL-SG1218MPE-UN-V5-1.0.0-Build-20230616-up.bin.
Size: 1013324 bytes.
Git blob SHA: 4adcdc9ba049085cde19d422f55914e8f8a79430.
Retrieved through GitHub fetch_file with base64 encoding, decoded in JavaScript.
Instruction words reviewed with a small MIPS decoder; no fresh Unicorn execution.

## New review: actual function previously stubbed
Entry 0xbfc52edc (file 0x4aedc):
1. Rejects a null source pointer.
2. Copies 0xc2 bytes from memory-mapped factory flash at 0xb41fc000 into stack RAM.
3. Copies supplied bytes into that buffer at the requested offset.
4. Calls 0xbf0199b0, which returns the flash descriptor at 0xbf016078.
5. Calls 0xbf019ef4 with start/end sector 0x1fc.
6. Calls 0xbf019b9c with destination 0xb41fc000 and length 0xc2.
No password/HTTP-session comparison occurs in this function.
Erase failure causes a diagnostic print; execution still reaches the programming call.
Selected wrappers call it for offsets/lengths (0,6), (0x96,40), (6,128).
The wrappers return zero after the call, so an acknowledgement alone cannot establish persistence.

The real program routine 0xbf019b9c checks length, address ranges and a per-sector
protection byte, then writes SPI controller registers 0xb8001208/0xb800120c.
The real erase routine 0xbf019ef4 checks sector bounds and also writes those
controller registers. No credential comparison was seen in the reviewed bodies.
Observed command words include 0x06000000 and program address combined with
0x02000000; erase uses address combined with 0x20000000. Hardware success still
depends on protection/controller/flash state.

MAC getter 0xbfc54018 reads the six bytes directly from 0xb41fc000, with a special
fallback for one constant value. It is not merely a cached HTTP MAC getter.

## Meaning of this evidence
The code behind the old stub is a real erase/program path, not a second login
gate or a harmless placeholder. Calling it is evidence of an unauthenticated
attempt to change factory flash in the previously traced TDDP path.
Successful physical persistence has NOT yet been observed. Do not describe
this as proven remote takeover, arbitrary flash access, deliberate backdoor,
or ongoing/mass exploitation.

## Next steps
- Finish tracing flash protection initialization and remaining driver callees.
- Record exact instruction excerpts and a reproducible decoding method.
- Determine the smallest controlled write/read-back verification on owner hardware.
- Only claim physical write success after reading back the changed factory value.
- Update vendor draft with separate live, emulated and static evidence.
- v0.1.5 disables TDDP/TSDP; owner hardware installation is not confirmed.

## Existing reproducible evidence
- [Audit](SECURITY-AUDIT.md)
- [Offline MIPS results](management-auth-results.json)
- [Offline harness](../tools/audit_management_auth.py)
- [Live read-only probe](../tools/Confirm-TddpHandshake.ps1)
- [Vendor draft](TP-LINK-REPORT.md)

This checkpoint contains a technical evidence summary, not private internal reasoning.
