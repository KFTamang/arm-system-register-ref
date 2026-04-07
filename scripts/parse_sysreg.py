#!/usr/bin/env python3
"""
Parse the ARM AArch64 SysReg XML tarball into registers.json.

Usage:
    python3 scripts/parse_sysreg.py <SysReg_xml_*.tar.gz> [--out data/registers.json]

Download the tarball from:
    https://developer.arm.com/downloads/-/exploration-tools
    (Look for "AArch64 System Register XML" or "A-Profile Architecture")
"""

import argparse
import json
import re
import sys
import tarfile
import xml.etree.ElementTree as ET
from pathlib import Path


def text(el):
    """Return stripped text content of an element, or empty string."""
    if el is None:
        return ""
    parts = []
    if el.text:
        parts.append(el.text.strip())
    for child in el:
        t = text(child)
        if t:
            parts.append(t)
        if child.tail:
            parts.append(child.tail.strip())
    return " ".join(p for p in parts if p)


def first_text(parent, *tags):
    """Return the first non-empty text found among all elements matching any of the given tags."""
    for tag in tags:
        for el in parent.findall(tag):   # iterate ALL siblings, not just the first
            t = text(el)
            if t:
                return t
    return ""


def make_arm_url(short_name, long_name):
    """
    Construct the ARM Architecture Reference URL for a register.

    Example:
      short_name="SCTLR_EL1", long_name="System Control Register (EL1)"
      -> https://developer.arm.com/documentation/ddi0601/latest/AArch64-Registers/SCTLR-EL1--System-Control-Register--EL1-
    """
    base = "https://developer.arm.com/documentation/ddi0601/latest/AArch64-Registers"
    short_slug = short_name.replace("_", "-")
    if long_name:
        # Replace non-alphanumeric characters with '-', collapse runs of '-'
        long_slug = re.sub(r"[^A-Za-z0-9]+", "-", long_name)
        long_slug = long_slug.strip("-") + "-"
        slug = f"{short_slug}--{long_slug}"
    else:
        slug = short_slug
    return f"{base}/{slug}"


def parse_field_values(field_el):
    """Extract named enum values from a <field> element.

    Actual XML structure:
      <field_values>
        <field_value_instance>
          <field_value>0b0</field_value>
          <field_value_description><para>...</para></field_value_description>
        </field_value_instance>
      </field_values>
    """
    values = []
    fvs = field_el.find("field_values")
    if fvs is None:
        return values
    for fvi in fvs.findall("field_value_instance"):
        raw = first_text(fvi, "field_value")        # e.g. "0b0" or "0b1"
        label = first_text(fvi, "field_value_description")
        if not raw:
            continue
        try:
            # strip "0b" prefix and parse as binary
            val = int(raw.replace("0b", "").replace(" ", ""), 2)
        except ValueError:
            val = None
        values.append({"val": val, "label": label})
    return values


def parse_register(xml_bytes, filename):
    """Parse a single AArch64 register XML file. Returns a dict or None."""
    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError as e:
        print(f"  XML parse error in {filename}: {e}", file=sys.stderr)
        return None

    # Support both flat and nested structures
    reg_el = root.find(".//register")
    if reg_el is None:
        return None

    # Only AArch64 registers
    exec_state = reg_el.get("execution_state", "")
    if exec_state and exec_state != "AArch64":
        return None

    short_name = first_text(reg_el, "reg_short_name")
    if not short_name:
        # Fall back to filename: AArch64-SCTLR_EL1.xml -> SCTLR_EL1
        stem = Path(filename).stem  # e.g. AArch64-SCTLR_EL1
        short_name = stem.replace("AArch64-", "").replace("-", "_")

    long_name = first_text(reg_el, "reg_long_name")
    description = first_text(reg_el, "reg_purpose", "reg_description", "purpose")

    # Parse bit fields
    # Actual path: <reg_fieldsets><fields id="fieldset_0"><field>...
    # Use ".//fields" to find regardless of nesting depth; take first fieldset.
    fields = []
    fields_el = reg_el.find(".//fields")
    if fields_el is not None:
        for field_el in fields_el.findall("field"):
            fname = first_text(field_el, "field_name")
            # Reserved fields without a name — use the rwtype/reserved_type as name
            if not fname:
                fname = field_el.get("rwtype") or field_el.get("reserved_type") or "RES"

            try:
                msb = int(first_text(field_el, "field_msb") or "0")
                lsb = int(first_text(field_el, "field_lsb") or "0")
            except ValueError:
                continue

            # Description is in <field_description><para>...</para>
            description_text = first_text(field_el, "field_description")

            field_values = parse_field_values(field_el)

            # Determine if reserved
            rwtype = field_el.get("rwtype", "")
            reserved_type = field_el.get("reserved_type", "")
            is_reserved = bool(reserved_type) or rwtype in ("RES0", "RES1", "RAZ", "RAO", "UNKNOWN")

            fields.append({
                "name": fname,
                "msb": msb,
                "lsb": lsb,
                "description": description_text,
                "values": field_values,
                "reserved": is_reserved,
                "rwtype": rwtype or reserved_type or None,
            })

    # Sort fields MSB → LSB
    fields.sort(key=lambda f: -f["msb"])

    return {
        "name": short_name,
        "long_name": long_name,
        "description": description,
        "arm_url": make_arm_url(short_name, long_name),
        "fields": fields,
    }


def main():
    parser = argparse.ArgumentParser(description="Parse ARM SysReg XML tarball → registers.json")
    parser.add_argument("tarball", help="Path to SysReg_xml_*.tar.gz")
    parser.add_argument("--out", default="data/registers.json", help="Output JSON file")
    args = parser.parse_args()

    registers = []
    skipped = 0

    print(f"Opening {args.tarball} ...")
    with tarfile.open(args.tarball, "r:gz") as tf:
        members = [m for m in tf.getmembers() if m.name.endswith(".xml")]
        # Only AArch64 register files
        aarch64_members = [m for m in members if "/AArch64-" in m.name or m.name.startswith("AArch64-")]
        print(f"Found {len(aarch64_members)} AArch64 XML files (of {len(members)} total)")

        for member in aarch64_members:
            f = tf.extractfile(member)
            if f is None:
                continue
            xml_bytes = f.read()
            reg = parse_register(xml_bytes, Path(member.name).name)
            if reg is not None:
                registers.append(reg)
            else:
                skipped += 1

    # Sort alphabetically
    registers.sort(key=lambda r: r["name"].upper())

    print(f"Parsed {len(registers)} registers, skipped {skipped}")

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as fout:
        json.dump(registers, fout, ensure_ascii=False, separators=(",", ":"))

    print(f"Written to {out_path}  ({out_path.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
