**English** | [Русский](HTTP-JSON-FOLLOWUP.ru.md)

# HTTP, JSON and PoE analysis follow-up

Historical static investigation,16 October2026, SHA-256
`c9ab17eda7af714f00692d41f440ce84ed0d6c7d678634c364ec1154bb7e3f32`.
[Original record](HTTP-JSON-FOLLOWUP.txt). Current working implementation and
hardware results: [FIRMWARE](../docs/FIRMWARE.md), [test journal](../docs/evidence/2026-10-17-switchlens/README.md).
Offsets include the16-byte update header. Reproduce with `tools/audit_http.py`.

## Output path

Stock buffer `[BF010F8C,BF011540)` is0x5b4=1460 bytes. BFC3B278/file33278 resets
its pointer/globals. BF01CAC0/file66f8 copies body bytes and calls BFC38A64 with
1460 bytes when full, returning−1 on nonzero send status and0 on success.
This is body buffering, not proof of HTTP Transfer-Encoding: chunked.
BFC38A64/file30a64 checks socket/protocol6, calls BFC37258 and reduces status to0/−1.
ACK/wait/timeout/reentrancy semantics required later hardware checks.

BF01CBF8/file6830 formats into BF011550, stores length at BF011650 and calls
raw output, but always returns v0=0, losing raw errors. Formatter BFC339DC/file2b9dc
uses callback BF00ECCC without a capacity argument. The256-byte distance to the
next global is not an array declaration; a whole JSON printf is unsuitable.
Final flush BFC3B2D0/file332d0 also hides send status. Implementation therefore
uses bounded own serialization, raw output and separately checked final send.
Clients must reject incomplete documents.

## Router/session

BFC3B740/file33740 compares request+EC against BF001488, governed by BF011660,
with `/logon.cgi` exception at d5924; refusal goes to BFC3CDE8. This initial
finding was not a complete cookie analysis or evidence for unauthenticated JSON.
The implemented first version preserves stock sessions; no new TLS/SNMP server
or global authentication disable was introduced. Exact GET route handling and
session cases were later tested in the MIPS harness.

## PoE fields

Per-port stride0x30; record values:

| Address for first port | Type | Meaning |
| --- | --- | --- |
| BF01440A | s16 | Enable/state |
| BF01440C | s16 | Power limit |
| BF014410 | u32 | Priority |
| BF014416 | s16 | Current |
| BF014418 | s16 | Voltage |
| BF01441A | s16 | Power |
| BF01441C | u32 | PD class, file3ad10:3ad60 |
| BF014420 | u32 | Power status, file3ad74:3adc4 |

Loop count comes from BF0143E0. Strings pdclass at d6e80 and powerstatus at d6e8c
support identification. Units/encodings: [comparison](COMPARISON-AND-POE.md).
Read the existing cache without new controller commands. Cache freshness and
cross-field consistency are unconfirmed; enable differs from supply status,
class is encoded, and zero measurement is not automatically a valid zero.

## SignCheck input

BFC1044C copies UID to stack+18 (file45778), its length from BF002E80 is stored
at stack+500 (457b0:457c8). BF01E1C8 receives that buffer/length (46064:46088);
20 finalized bytes are compared with signature-operation output (46138:46198).
SHA-1 initial words67452301,EFCDAB89,98BADCFE,10325476,C3D2E1F0 appear46038:4607c.
Base64 cb400:cb4c8 decodes to148 bytes, magicRSA1, bit length1024, exponent65537.
Signature is read separately from B41FC006.

This strongly supports RSA/SHA-1 over flash UID, not the entire runtime image.
It is not a full mathematical audit of RSA or proof of no earlier boot checks.
[Platform follow-up](PLATFORM-FOLLOWUP.md) records the explicit data path.

## Status changes since the report

Initially missing dump, build and hardware results were obtained later. The
firmware now boots and serves UART/JSON. Uptime scale, exact MIB widths/latching,
peak IRQ stack, loaded PoE and recovery still require separate evidence.
Older builds were subsequently compared; initial “files unavailable” statements
are historical. The owner did not authorize inventing pinouts/voltages from BIN
analysis; actual wiring evidence is in [LAB](../docs/LAB.md).
