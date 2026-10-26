# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Arm System Register Ref (ASRF)** is a static web page for searching and decoding AArch64 system registers. It provides:

- Case-insensitive autocomplete search for system register names
- A value input (hex or decimal) that decodes each bit field with labeled meanings
- Reference links to the Arm Architecture Reference Manual (ARM ARM) for each register

## Getting Register Data

The register data comes from ARM's official **AARCHMRS** (A-Profile Machine Readable Specification) open-source JSON package, available at:
> https://developer.arm.com/downloads/-/exploration-tools  
> (Look for "A-Profile Architecture" → open-source JSON package)

After downloading and extracting the package, generate `data/registers.json`:

```sh
python3 scripts/parse_aarchmrs.py AARCHMRS_OPENSOURCE_A_profile_FAT-2025-12/
# Writes data/registers.json  (~1761 registers: AArch64 + AArch32 + External)
```

Then add the EC-dependent ISS/ISS2 encodings (ESR_ELx, HSR, PMBSR_ELx, TRBSR_ELx) and refresh the ARM ARM links, and regenerate the R-profile data:

```sh
python3 scripts/add_iss_encodings.py AARCHMRS_OPENSOURCE_A_profile_FAT-2026-09/
python3 scripts/gen_r_profile.py
```

In the data, the controlling field (EC) has `links: {"<EC value>": {"ISS": "<id>", ...}}`, and the dynamic field (ISS) has `instances: {"<id>": {display, fields[]}}`. `app.js` renders the fields of the selected instance as sub-rows.

The older `scripts/parse_sysreg.py` (SysReg XML tarball → AArch64 only, with field descriptions) is kept for reference.

## Running Locally

The page requires an HTTP server (not `file://`) due to the `fetch()` call for `data/registers.json`:

```sh
python3 -m http.server 8080
# Then open http://localhost:8080
```

## Architecture

```
index.html          # Single-page UI (inputs, dropdown, bit-field table)
style.css           # Dark-theme styles
app.js              # All frontend logic
data/
  registers.json    # Generated — not committed; ~2–5 MB
scripts/
  parse_sysreg.py   # One-shot parser: ARM SysReg XML tar.gz → registers.json
```

### Data flow

1. `parse_sysreg.py` reads each `AArch64-*.xml` from the ARM tarball and outputs a JSON array. Each entry has `name`, `long_name`, `description`, `arm_url`, and `fields[]` (with `msb`, `lsb`, `name`, `description`, `values[]`, `reserved`).
2. `app.js` fetches `data/registers.json` on load, then:
   - Filters register names as the user types (prefix matches ranked first)
   - Parses the value input to `BigInt` for 64-bit correctness
   - Extracts each field's bits with `(value >> lsb) & mask` and looks up enum labels from `field.values[]`

### ARM ARM URL format

Register pages follow the pattern:
```
https://developer.arm.com/documentation/111107/latest/AArch64-Registers/{slug}
```
(document 111107 is the successor of DDI0601). `slug` is `"{short name}, {long name}"` with every non-alphanumeric character replaced by its own `-` (no collapsing or stripping), e.g. `ESR-EL1--Exception-Syndrome-Register--EL1-`. Constructed in `parse_sysreg.py:make_arm_url()`.
