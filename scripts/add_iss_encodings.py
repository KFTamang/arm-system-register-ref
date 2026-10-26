#!/usr/bin/env python3
"""
Add EC-dependent ISS encodings (ESR_ELx, HSR, PMBSR_ELx, TRBSR_ELx, ...) to
registers.json, using the ARM AARCHMRS open-source JSON package.

In AARCHMRS, a field such as ESR_EL1.ISS is a "Fields.Dynamic" field with one
fieldset per exception class, and each value of the controlling field (EC) is
a "Values.Link" naming the fieldset to use for ISS / ISS2.  This script copies
that structure into the matching entries of registers.json:

  controlling field:  "links":     {"<EC value>": {"ISS": "<id>", "ISS2": "<id>"}}
  dynamic field:      "instances": {"<id>": {"display": "...", "fields": [...]}}

Instance fields use absolute bit positions within the register.  They have the
same shape as top-level fields plus an optional "condition" string.

It also regenerates every arm_url (see parse_sysreg.make_arm_url).

Usage:
    python3 scripts/add_iss_encodings.py <AARCHMRS dir or Registers.json>
                                         [--data data/registers.json]

The AARCHMRS package is available from:
    https://developer.arm.com/downloads/-/exploration-tools
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from parse_sysreg import make_arm_url  # noqa: E402


# AARCHMRS omits all descriptive text, so enum labels for the most commonly
# decoded ISS fields are provided here.  Labels are only attached to values
# that AARCHMRS lists for the field.

FSC_LABELS = {
    0b000000: "Address size fault, level 0 of translation or translation table base register.",
    0b000001: "Address size fault, level 1.",
    0b000010: "Address size fault, level 2.",
    0b000011: "Address size fault, level 3.",
    0b000100: "Translation fault, level 0.",
    0b000101: "Translation fault, level 1.",
    0b000110: "Translation fault, level 2.",
    0b000111: "Translation fault, level 3.",
    0b001000: "Access flag fault, level 0.",
    0b001001: "Access flag fault, level 1.",
    0b001010: "Access flag fault, level 2.",
    0b001011: "Access flag fault, level 3.",
    0b001100: "Permission fault, level 0.",
    0b001101: "Permission fault, level 1.",
    0b001110: "Permission fault, level 2.",
    0b001111: "Permission fault, level 3.",
    0b010000: "Synchronous External abort, not on translation table walk or hardware update of translation table.",
    0b010001: "Synchronous Tag Check Fault.",
    0b010010: "Synchronous External abort on translation table walk or hardware update of translation table, level -2.",
    0b010011: "Synchronous External abort on translation table walk or hardware update of translation table, level -1.",
    0b010100: "Synchronous External abort on translation table walk or hardware update of translation table, level 0.",
    0b010101: "Synchronous External abort on translation table walk or hardware update of translation table, level 1.",
    0b010110: "Synchronous External abort on translation table walk or hardware update of translation table, level 2.",
    0b010111: "Synchronous External abort on translation table walk or hardware update of translation table, level 3.",
    0b011000: "Synchronous parity or ECC error on memory access, not on translation table walk.",
    0b011011: "Synchronous parity or ECC error on memory access on translation table walk or hardware update of translation table, level -1.",
    0b011100: "Synchronous parity or ECC error on memory access on translation table walk or hardware update of translation table, level 0.",
    0b011101: "Synchronous parity or ECC error on memory access on translation table walk or hardware update of translation table, level 1.",
    0b011110: "Synchronous parity or ECC error on memory access on translation table walk or hardware update of translation table, level 2.",
    0b011111: "Synchronous parity or ECC error on memory access on translation table walk or hardware update of translation table, level 3.",
    0b100001: "Alignment fault.",
    0b100010: "Granule Protection Fault on translation table walk or hardware update of translation table, level -2.",
    0b100011: "Granule Protection Fault on translation table walk or hardware update of translation table, level -1.",
    0b100100: "Granule Protection Fault on translation table walk or hardware update of translation table, level 0.",
    0b100101: "Granule Protection Fault on translation table walk or hardware update of translation table, level 1.",
    0b100110: "Granule Protection Fault on translation table walk or hardware update of translation table, level 2.",
    0b100111: "Granule Protection Fault on translation table walk or hardware update of translation table, level 3.",
    0b101000: "Granule Protection Fault, not on translation table walk or hardware update of translation table.",
    0b101001: "Address size fault, level -1.",
    0b101010: "Translation fault, level -2.",
    0b101011: "Translation fault, level -1.",
    0b101100: "Address size fault, level -2.",
    0b110000: "TLB conflict abort.",
    0b110001: "Unsupported atomic hardware update fault.",
    0b110100: "IMPLEMENTATION DEFINED fault (Lockdown).",
    0b110101: "IMPLEMENTATION DEFINED fault (Unsupported Exclusive or Atomic access).",
}

DA = "an_exception_from_a_Data_Abort"
IA = "an_exception_from_an_Instruction_Abort"
WP = "an_exception_from_a_Watchpoint_exception"
BP = "an_exception_from_a_Breakpoint_or_Vector_Catch_debug_exception"
SS = "an_exception_from_a_Software_Step_exception"
SE = "an_SError_interrupt"

WNR_LABELS = {
    0: "Abort caused by an instruction reading from memory.",
    1: "Abort caused by an instruction writing to memory.",
}
FNV_LABELS = {
    0: "FAR is valid.",
    1: "FAR is not valid, and holds an UNKNOWN value.",
}
DEBUG_FSC_LABELS = {0b100010: "Debug exception."}

# (register state, ISS instance id, field name) -> {value: label}
FIELD_LABELS = {
    ("AArch64", DA, "DFSC"): FSC_LABELS,
    ("AArch64", IA, "IFSC"): FSC_LABELS,
    ("AArch64", DA, "WnR"): WNR_LABELS,
    ("AArch64", WP, "WnR"): WNR_LABELS,
    ("AArch64", DA, "ISV"): {
        0: "No valid instruction syndrome. ISS[23:14] are RES0.",
        1: "ISS[23:14] hold a valid instruction syndrome.",
    },
    ("AArch64", DA, "FnV"): FNV_LABELS,
    ("AArch64", IA, "FnV"): FNV_LABELS,
    ("AArch64", WP, "FnV"): FNV_LABELS,
    ("AArch64", WP, "DFSC"): DEBUG_FSC_LABELS,
    ("AArch64", BP, "IFSC"): DEBUG_FSC_LABELS,
    ("AArch64", SS, "IFSC"): DEBUG_FSC_LABELS,
    ("AArch64", SE, "DFSC"): {
        0b000000: "Uncategorized error.",
        0b010001: "Asynchronous SError exception.",
    },
}


# ── AST → text ────────────────────────────────────────────────────────────────

def ast_text(node):
    """Render an AARCHMRS condition AST as a short readable expression."""
    t = node.get("_type")
    if t == "AST.Bool":
        return "TRUE" if node["value"] else "FALSE"
    if t == "AST.Identifier":
        return node["value"]
    if t == "Values.Value":
        return node["value"]
    if t == "Types.Field":
        v = node["value"]
        return f"{v['name']}.{v['field']}" if v.get("name") else v["field"]
    if t == "AST.Set":
        return "{" + ", ".join(ast_text(v) for v in node["values"]) + "}"
    if t == "AST.UnaryOp":
        s = ast_text(node["expr"])
        return node["op"] + (f"({s})" if node["expr"].get("_type") == "AST.BinaryOp" else s)
    if t == "AST.Function":
        args = [ast_text(a) for a in node["arguments"]]
        if node["name"] == "IsFeatureImplemented" and len(args) == 1:
            return args[0]
        return f"{node['name']}({', '.join(args)})"
    if t == "AST.BinaryOp":
        def side(n):
            s = ast_text(n)
            if n.get("_type") == "AST.BinaryOp" and n["op"] != node["op"]:
                s = f"({s})"
            return s
        return f"{side(node['left'])} {node['op']} {side(node['right'])}"
    return t or "?"


def condition_text(cond):
    """Return condition text, or None when the condition is always true."""
    if cond is None or (cond.get("_type") == "AST.Bool" and cond["value"]):
        return None
    return ast_text(cond)


# ── Values ────────────────────────────────────────────────────────────────────

def bits_of(value_str):
    """"'0101'" -> "0101" (may contain 'x' wildcards)."""
    return value_str.strip("'")


def flatten_values(values):
    """Yield (bits, condition) for every Values.Value, descending into ConditionalValue."""
    for v in values:
        if v["_type"] == "Values.Value":
            yield bits_of(v["value"]), None
        elif v["_type"] == "Values.ConditionalValue":
            cond = condition_text(v.get("condition"))
            for bits, _ in flatten_values(v["values"]["values"]):
                yield bits, cond


def convert_values(field, state, inst, name):
    vs = field.get("values")
    if not isinstance(vs, dict):
        return []
    labels = FIELD_LABELS.get((state, inst, name), {})
    out = []
    for bits, cond in flatten_values(vs["values"]):
        if "x" in bits:
            out.append({"val": None, "pattern": bits, "label": ""})
            continue
        val = int(bits, 2)
        label = labels.get(val, "")
        if label and cond:
            label += f" (when {cond})"
        out.append({"val": val, "label": label})
    # Drop value lists that carry no information beyond the raw number
    if not any(v["label"] for v in out):
        return []
    return out


def collect_links(values, out):
    for v in values:
        if v["_type"] == "Values.Link":
            out[str(int(bits_of(v["value"]), 2))] = v["links"]
        elif v["_type"] == "Values.ConditionalValue":
            collect_links(v["values"]["values"], out)


# ── Fields ────────────────────────────────────────────────────────────────────

def convert_field(f, base, state, inst, condition=None):
    """Convert one AARCHMRS field into a list of registers.json-style fields."""
    t = f["_type"]
    out = []

    if t == "Fields.ConditionalField":
        for alt in f["fields"]:
            cond = condition_text(alt["condition"])
            cond = " && ".join(c for c in (condition, cond) if c) or None
            for r in f["rangeset"]:
                out += convert_field(alt["field"], base + r["start"], state, inst, cond)
        return out

    for r in f.get("rangeset", []):
        lsb = base + r["start"]
        msb = lsb + r["width"] - 1
        if t == "Fields.Reserved":
            name = rwtype = f["value"]
            reserved = True
        elif t == "Fields.ImplementationDefined":
            name, rwtype, reserved = f.get("name") or "IMPLEMENTATION DEFINED", "IMPLEMENTATION DEFINED", False
        else:
            name, rwtype, reserved = f.get("name") or "?", None, False
        entry = {
            "name": name,
            "msb": msb,
            "lsb": lsb,
            "description": "",
            "values": [] if reserved else convert_values(f, state, inst, name),
            "reserved": reserved,
            "rwtype": rwtype,
        }
        if condition:
            entry["condition"] = condition
        out.append(entry)
    return out


def convert_instance(inst, base, state):
    fields = []
    for f in inst["values"]:
        fields += convert_field(f, base, state, inst["name"])
    fields.sort(key=lambda x: (-x["msb"], x["lsb"]))
    return {"display": inst.get("display") or inst["name"], "fields": fields}


def extract_dynamic(mrs_reg):
    """Return (links_by_field, instances_by_field) for one AARCHMRS register."""
    links, instances = {}, {}
    for fs in mrs_reg.get("fieldsets") or []:
        for f in fs["values"]:
            if f["_type"] == "Fields.Dynamic":
                base = f["rangeset"][0]["start"]
                instances[f["name"]] = {
                    i["name"]: convert_instance(i, base, mrs_reg["state"]) for i in f["instances"]
                }
            vs = f.get("values")
            if isinstance(vs, dict):
                lk = {}
                collect_links(vs["values"], lk)
                if lk:
                    links[f["name"]] = lk
    return links, instances


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Add EC-dependent ISS encodings to registers.json")
    parser.add_argument("aarchmrs", help="AARCHMRS directory or its Registers.json")
    parser.add_argument("--data", default="data/registers.json", help="registers.json to update in place")
    args = parser.parse_args()

    src = Path(args.aarchmrs)
    if src.is_dir():
        src = src / "Registers.json"
    print(f"Loading {src} ...")
    with open(src, encoding="utf-8") as f:
        mrs = json.load(f)

    with open(args.data, encoding="utf-8") as f:
        registers = json.load(f)
    index = {(r["name"], r["state"]): r for r in registers}

    updated = 0
    for m in mrs:
        if m.get("_type") not in ("Register", "RegisterArray"):
            continue
        links, instances = extract_dynamic(m)
        if not links or not instances:
            continue
        reg = index.get((m["name"], m["state"]))
        if reg is None:
            print(f"  {m['name']} ({m['state']}) not in {args.data}, skipped", file=sys.stderr)
            continue
        for field in reg["fields"]:
            field.pop("links", None)
            field.pop("instances", None)
            if field["name"] in links:
                field["links"] = links[field["name"]]
            if field["name"] in instances:
                field["instances"] = instances[field["name"]]
        print(f"  {reg['name']} ({reg['state']}): " +
              ", ".join(f"{k}[{len(v)}]" for k, v in instances.items()))
        updated += 1

    for reg in registers:
        reg["arm_url"] = make_arm_url(reg["name"], reg["long_name"], reg["state"])

    with open(args.data, "w", encoding="utf-8") as f:
        json.dump(registers, f, ensure_ascii=False, separators=(",", ":"))
    print(f"Updated {updated} registers; written to {args.data}")


if __name__ == "__main__":
    main()
