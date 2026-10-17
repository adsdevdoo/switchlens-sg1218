**English** | [Русский](COMPARISON-AND-POE.ru.md)

# Vendor-build comparison and PoE sources

Historical static analysis,16 October2026. [Original record](COMPARISON-AND-POE.txt).
Current working firmware and test results are separate:
[API](../docs/JSON-API.md), [hardware evidence](../docs/evidence/2026-10-17-switchlens/README.md).
Offsets include each image's header. No device was queried by this analysis.

## Compared images

| Build | SHA-256 |
| --- | --- |
| 20221012 Rel.42630 | 4b5f2348480fcb8a908a2ef7a76d1a4d82e754375cece9a24a3e3038120d9cf3 |
| 20230220 Rel.33194 | 0bcbe30cb88a0987967cb1b30eac01060a48eec2cbdcbd94091ea6e0dfd3a6b9 |
| 20230616 Rel.57668 | c9ab17eda7af714f00692d41f440ce84ed0d6c7d678634c364ec1154bb7e3f32 |

ZIP hashes:20221012 `063ebd47fbbcfbd8a333cc79cbcb8d6551053d95721ff4f60d19818d6484f888`,
20230220 `fddab01e344812033717324ebdc5c0bfd62f32198b2d545e2b6a6007275ca43f`.
Each ZIP contained one BIN and upgrade PDF; those PDFs were not analyzed at this stage.
All three BINs are1013324 bytes, bytes4:16=`000f763c0dffffff184d5005`.
CRC32 over10:f7000 matches first big-endian word: f0f47733 /278ed387 /d31a20a5.
Web CRC call sites35fe4/36614/36014 use length f6ff0 and CRC functions
BF01B420/BF01B8C0/BF01B480 respectively.

SignCheck start exists in all three at d7504/d7eac/d757c, with flash UID/signature,
RSA1 and Pass/Fail messages. It was not introduced only in February. Runtime
strings alone cannot rule out separate bootloader checks. February additionally
contains RSA_private_decrypt error at d7cf8 and success at d7d14, referenced by
4339c/433b0; absence in other builds does not prove removal of cryptography.
A management-protocol change was a hypothesis, not a complete protocol analysis.

## Statistics existed in earlier builds

CLI table locations940c0/94a60/94170 have the same rx bytes0, tx bytes8, tx drop16
and six other name/selectors. General MIB entry file158d0/15e90/15930,
VA BFC1D8D0/BFC1DE90/BFC1D930, matched first56 bytes/dispatch.
Stock statistics handlers BFC415BC/BFC41C3C/BFC4163C are routed in each image.
This does not establish whole-function semantic equivalence.

## PoE RAM and UI

June router34920:34948 sends `/PoeConfigRpm.htm` to BFC42910/file3a910.
Handler3a9f4:3aa84 reads base BF0143E0: port_count+0,
limit+14, min+18, max+1c, consumption+20. Stock web clamps displayed consumption
at the limit and remaining at zero; JSON preserves original consumption/raw.

Records stride0x30. First port: state BF01440A(s16), limit BF01440C(s16),
priority BF014410(u32), current BF014416(s16), voltage BF014418(s16),
power BF01441A(s16), traced at3aab8:3ace8. Later analysis established
class BF01441C and status BF014420; initial string evidence d6e80/d6e8c.

JS printSpanStr at b6938 divides power/voltage by10; current is unscaled mA
(header in b43f8:b8034). Global power quantities also divide by10.
Limit330 means Auto, not fixed33W;40/70/154/300 correspond to class limit choices,
other values display raw/10W. PD class separately maps330/40/70/154/300→0/1/2/3/4.
Priority0/1/2→High/Middle/Low. Status0–9 maps OFF, TURNING-ON, ON, OVERLOAD,
SHORT, NOSTANDARD-PD, VOLTAGE-HIGH, VOLTAGE-LOW, HARDWARE-FAULT, OVERTEMPERATURE.
Unknown codes display unavailable; JSON retains raw numeric code with null text.
Zero measurements display `---`, so per-port nonpositive readings are null.

## Implemented interpretation and limits

One read-only JSON includes network counters and PoE, reading existing cache
without issuing controller commands. Keep configuration enable separate from
actual status, class/limit codes separate, and raw values where implemented.
Ports1–16 have PoE objects;17/18 have null. Do not claim cache freshness or
measurement validity. The early proposal's field names were refined in the
[current schema/reference](../docs/JSON-API.md).

At the original analysis stage no patch existed and the planning gate was open.
That is historical: a build and successful hardware boot/UART/JSON now exist.
Loaded PoE, recovery and full metric semantics remain outstanding.
