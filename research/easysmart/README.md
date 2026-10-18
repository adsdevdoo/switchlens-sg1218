English | [Русский](README.ru.md)

# Easy Smart Configuration Utility: static protocol review

The owner's uploaded classes confirm a management protocol with username/password fields and a legacy encryption key identical to the key in the stock switch firmware. **This does not establish a new management-login bypass.** The earlier hardware-confirmed factory MAC write without credentials is a separate TDDP finding.

This review is dated 2026-10-18. It processed data offline: no application, Java class or network probe was executed.

## Evidence and reproduction

- Original upload: branch `adsdevdoo-patch-2`, commit [4d6e8fa403ca102da2cb8e77ebcd44abed259104](https://github.com/adsdevdoo/switchlens-sg1218/commit/4d6e8fa403ca102da2cb8e77ebcd44abed259104).
- [Preserved class export](classes-export.json): 100 selected classes, 227,726 decoded bytes, from an embedded archive containing 913 entries.
- [Machine-readable verification](static-analysis.json): all 100 class lengths and SHA-256 hashes match; 645 methods, 642 Code attributes and 22,029 instructions were parsed. Decoded branch targets point to instruction boundaries.
- EXE SHA-256: `aa6e67c6e9be38cca002b704bc2eb1bf2b8fc199631e307a781cc7680c8d8619`.
- [Analyzer](../../tools/Analyze-EasySmartClasses.mjs).
- [Step-by-step journal, including full analyzer source](https://github.com/adsdevdoo/switchlens-sg1218/issues/1#issuecomment-6251784938).

With Node.js already installed and the input/script saved under C:\tmp:

```powershell
node C:\tmp\Analyze-EasySmartClasses.mjs C:\tmp\classes-export.json C:\tmp\easysmart-static-review
```

An optional third argument is the original 20230616 **web-upgrade BIN**, not the SPI backup. The analyzer checks its SHA-256 before comparison. It produces a JSON report and selected bytecode listing, refuses to overwrite existing output files, and makes no network requests. Its exact computational core was executed during this review; the Node filesystem wrapper was not run because the shell environment was unavailable. This parser is not a full JVM verifier.

## Transport and header

Method names below are relative to `com/tplink/smb/easySmartUtility/`.

`transfer/i.<clinit>`, `transfer/The.bb` and `transfer/V.bd` establish:

| Client path | Destination UDP port | Local UDP port |
| --- | ---: | ---: |
| Normal | 29808 | 29809 |
| Alternative after bind failure | 62576 | 62577 |

The destination address is 255.255.255.255. These are capabilities in the client; availability of each alternative on this switch was not tested.

`transfer/PacketHead.toArray` emits a 32-byte header. `transfer/TLV.F(S)` and `i(I)` serialize integers in big-endian order.

| Byte offset | Length | Outgoing header value |
| --- | ---: | --- |
| 0 | 1 | Version, initialized to 1 |
| 1 | 1 | Opcode |
| 2 | 6 | Device MAC; zero for discovery |
| 8 | 6 | Client MAC |
| 14 | 2 | Sequence |
| 16 | 4 | Error field |
| 20 | 2 | Total header + payload length |
| 22 | 2 | Fragment field |
| 24 | 2 | Flag |
| 26 | 2 | Token |
| 28 | 4 | Additional integer field; semantics not established |

This is distinct from the previously examined **12-byte TDDP factory protocol on UDP 1040**.

## Requests, credentials and login

| Identifier | Verified behavior | Bytecode source |
| --- | --- | --- |
| Opcode 0 | DISCOVERY (enum field y) | DataBean$Request, PacketHead.Code |
| Opcode 1 | GET (enum field z), including token request | DataBean$Request, PacketHead.Code, From |
| Opcode 3 | SET (enum field A); credential-bearing management path | DataBean$Request, PacketHead.Code, The.ba |
| Replies 2 / 4 | Accepted for y/z and A respectively | PacketHead.I |
| TLV 0x000A | Reported number of switch ports | SwitchLoginBean.buildGetRequest/handleResponse |
| TLV 0x0200 | Username from DeviceInfo | The.ba |
| TLV 0x0202 | Password from DeviceInfo | The.ba |
| TLV 0x0210 | Generated key passed through transfer/I.I | RSAKeyBean.buildSetRequest |
| TLV 0x0901 | Token request | From.init |
| 0xFFFF + zero length | Payload terminator | From.init |

The login controller first sends an RSAKeyBean. A recognized result value 0x1002 selects NEW_RC4_8 for the device MAC. It then reads the actual UI username and password, builds a SwitchLoginBean request and sends it. This describes client behavior; no live exchange from the owner's switch was captured in this review.

The client adding credentials does not by itself prove the server checks them on every path. Conversely, a shared transport key does not prove those checks are bypassed.

## Encryption findings

The client explicitly names OLD_RC4 and NEW_RC4_8. OLD_RC4 uses a 256-element RC4 state initialized with a shared key. The newer branch uses an 8-element state; its eight-character key string is generated through a constructor that creates **SecureRandom**, despite a Random-typed field.

The 264-byte constant in `transfer/of.aM` was decoded with a transcription of `transfer/mine.V`: 32 rounds, signed Java right shifts and 32-bit overflow. After removing eight padding bytes, the recovered 256 bytes match stock firmware bytes **[0xCB2E8, 0xCB3E8)** exactly. Re-encryption reproduces the original constant.

- Recovered key SHA-256: `003d481f74298dfb9cd27e69c74405a1bb949af5c5591dedea18c284ea828b54`.
- Stock web-upgrade BIN SHA-256: `c9ab17eda7af714f00692d41f440ce84ed0d6c7d678634c364ec1154bb7e3f32`.

The legacy key is recoverable from distributed software; it is not a per-device secret. The new branch's small state warrants separate cryptographic assessment. Neither observation establishes which mode a live session selects or proves a new exploit against this device.

## False positives and unresolved questions

The top-level Tempest class contains admin/admin but announces “Switch Simulation is Running.” and processes simulated switch models. Its wrapper is present; its activation in the released application was not established. These constants are **not evidence of a hidden switch account**. The string password in transfer/mine.main is an encryption demonstration.

A scoped search of the 100 classes did not identify the meaning of factory field40, a link to its known value, or a SHA1/MessageDigest call. The getIsFactory UI flag and firmware-upgrade flash-error text do not establish that link. The later six-class metadata export below supplies names and selected references for DataBean, SwitchLoginBean and DeviceInfo. It still does not provide all application classes or full control flow, so this is not a complete utility audit or command catalogue.

Earlier owner tests established unauthenticated factory MAC change/readback and restoration on reported SwitchLens v0.1.4. They did not establish reboot persistence or remote code execution. Those results remain valid and separate from this client analysis.

## Follow-up: six-class request metadata received

The owner successfully ran [Export-EasySmartRequestMetadata.ps1](../../tools/Export-EasySmartRequestMetadata.ps1). [Preserved metadata](request-metadata.json) was uploaded in commit [f8ac74e5860463130841d6348b50ed64e5adbaa3](https://github.com/adsdevdoo/switchlens-sg1218/commit/f8ac74e5860463130841d6348b50ed64e5adbaa3), timestamp 2026-10-18T15:56:04.5211994Z. The six reported sizes match the archive inventory (18,554 bytes), and event offsets are in bounds. Their hashes are extractor-reported: this metadata file does not include raw bytes for an independent hash recomputation here.

Confirmed additions:

- Enum fields y/z/A mean DISCOVERY/GET/SET. SET's enum ordinal is 2, while its wire opcode is 3.
- The login builder clears its list, selects SET and sets a client page flag to false. The shared sender then injects username/password TLVs. The initially empty list is not a passwordless-login path.
- The subsequent GET adds TLV 0x000A. Its response is read as a byte into portNum: a count of switch ports, not TCP/UDP port 10.
- Discovery reads isFactory as a one-byte property. That name does not link it to the separate 40-byte flash field at 0x1FC096 or prove a transition into TDDP factory mode.
- The reduced metadata lists discovery cases 1–16 without their destinations. Exact mappings for the remaining tags must not be inferred from the order of fields.

[Follow-up journal, with the script and each verified step](https://github.com/adsdevdoo/switchlens-sg1218/issues/1#issuecomment-6251922477). No additional switch traffic or firmware change occurred. Factory field40 remains unidentified; its firmware consumers are the next relevant evidence.

The full generated bytecode listing was not published as a separate file: automatic approval review rejected that publication, citing proprietary code and embedded cryptographic material. The analyzer can reproduce it locally from the existing owner-provided export.
