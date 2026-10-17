**English** | [Русский](CONTRIBUTING.ru.md)

# Contributing and publishing evidence

SwitchLens is working firmware with boot, UART `help` and dynamic JSON verified
on the owner's unit. Distinguish code/emulator checks, observed hardware results
and hypotheses about unverified metric semantics. Always identify firmware facts
by SHA-256, file offset or VA and the method used to establish them.

Before changing the schema, regenerate field tables with `make generated`, then
run `make test` and `make sanitize`. Tests should exercise behavior and meaningful
boundaries. Label synthetic examples. An SDK register name from another board
does not establish the hardware semantics of this unit.

Keep the telemetry reader read-only: no configuration setters, counter resets,
PoE switching or flash writes. Experiments use the owner's bench, not production
network equipment. Changes between project phases follow the owner's instructions.

English is the default documentation language. Maintain the matching `.ru.md`
version and the **English | Русский** links on every reader document. Preserve
code, field names, hashes and observed outputs exactly. Original messages/logs,
JSON samples, PDFs and frozen release artifacts remain primary evidence; paired
reader guides explain them without rewriting the originals.

Without a specific owner request, do not publish dumps, credentials, cookies,
real IP/MAC data, complete UART logs or panel screenshots. Use anonymized examples.
The following explicit exceptions were authorized on 17 October 2026:

- Versioned firmware BINs in `releases/`, with SHA-256, manifests and accurate
  verification status; authorized board photographs.
- The unchanged original GD25Q16B/Xgpro export in `backups/original/2026-10-17/`.
- The complete supplied stock boot text, including the unit MAC, and supplied
  UART screenshots in `docs/evidence/2026-10-17/` and `docs/images/uart/`.
- All four official V5 ZIP/BIN packages and upgrade guides in `vendor/tp-link/`,
  plus original manufacturer datasheets. Preserve bytes, provenance and hashes.
- The successful v0.1.1 session in `docs/evidence/2026-10-17-switchlens/`: selected
  owner messages, supplied boot/help text, eight original screenshots and two full
  JSON replies including this bench's IP/MAC information.

These exceptions are session-specific; they do not authorize future logs or secrets.
Do not modify the original dump/vendor files or released firmware just to update
documentation. Additional hardware observations belong in a new evidence record.
The software license does not automatically cover manufacturers' materials.
