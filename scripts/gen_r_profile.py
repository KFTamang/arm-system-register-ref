#!/usr/bin/env python3
"""
Generate data/registers_r_profile.json for Armv8-R AArch32 profile.

Based on ARM DDI 0568A.c (Armv8 for Armv8-R AArch32 Architecture Profile):
- Unchanged: keep A-profile AArch32 entry as-is
- Redefined: keep A-profile entry, mark as redefined (fields may differ)
- New:       inject new entry with fields extracted from DDI0568
- Unused:    excluded entirely

Usage:
    python3 scripts/gen_r_profile.py [--input data/registers.json]
                                     [--out data/registers_r_profile.json]
"""

import argparse
import json
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# R-profile register status table (from DDI0568 Table E1-1)
# Keys are canonical register names; values are status strings.
# ---------------------------------------------------------------------------
R_PROFILE_STATUS = {
    # Unchanged
    "ACTLR":         "Unchanged",
    "ACTLR2":        "Unchanged",
    "ADFSR":         "Unchanged",
    "AIDR":          "Unchanged",
    "AIFSR":         "Unchanged",
    "AMAIR0":        "Unchanged",
    "AMAIR1":        "Unchanged",
    "CCSIDR":        "Unchanged",
    "CLIDR":         "Unchanged",
    "CNTFRQ":        "Unchanged",
    "CNTHCTL":       "Unchanged",
    "CNTHP_CTL":     "Unchanged",
    "CNTHP_CVAL":    "Unchanged",
    "CNTHP_TVAL":    "Unchanged",
    "CNTKCTL":       "Unchanged",
    "CNTPCT":        "Unchanged",
    "CNTP_CTL":      "Unchanged",
    "CNTP_CVAL":     "Unchanged",
    "CNTP_TVAL":     "Unchanged",
    "CNTVCT":        "Unchanged",
    "CNTVOFF":       "Unchanged",
    "CNTV_CTL":      "Unchanged",
    "CNTV_CVAL":     "Unchanged",
    "CNTV_TVAL":     "Unchanged",
    "CONTEXTIDR":    "Unchanged",
    "CPACR":         "Unchanged",
    "CSSELR":        "Unchanged",
    "CTR":           "Unchanged",
    "DBGBCR<n>":     "Unchanged",
    "DBGBVR<n>":     "Unchanged",
    "DBGBXVR<n>":    "Unchanged",
    "DBGCLAIMCLR":   "Unchanged",
    "DBGCLAIMSET":   "Unchanged",
    "DBGDCCINT":     "Unchanged",
    "DBGDEVID":      "Unchanged",
    "DBGDEVID1":     "Unchanged",
    "DBGDEVID2":     "Unchanged",
    "DBGDIDR":       "Unchanged",
    "DBGDRAR":       "Unchanged",
    "DBGDSAR":       "Unchanged",
    "DBGDSCRint":    "Unchanged",
    "DBGDTRRXext":   "Unchanged",
    "DBGDTRRXint":   "Unchanged",
    "DBGDTRTXext":   "Unchanged",
    "DBGDTRTXint":   "Unchanged",
    "DBGOSDLR":      "Unchanged",
    "DBGOSECCR":     "Unchanged",
    "DBGOSLAR":      "Unchanged",
    "DBGOSLSR":      "Unchanged",
    "DBGPRCR":       "Unchanged",
    "DBGVCR":        "Unchanged",
    "DBGWCR<n>":     "Unchanged",
    "DBGWFAR":       "Unchanged",
    "DBGWVR<n>":     "Unchanged",
    "DFAR":          "Unchanged",
    "DLR":           "Unchanged",
    "DSPSR":         "Unchanged",
    "FCSEIDR":       "Unchanged",
    "FPEXC":         "Unchanged",
    "FPSID":         "Unchanged",
    "HACR":          "Unchanged",
    "HACTLR":        "Unchanged",
    "HACTLR2":       "Unchanged",
    "HADFSR":        "Unchanged",
    "HAIFSR":        "Unchanged",
    "HAMAIR0":       "Unchanged",
    "HAMAIR1":       "Unchanged",
    "HDFAR":         "Unchanged",
    "HIFAR":         "Unchanged",
    "HMAIR0":        "Unchanged",
    "HMAIR1":        "Unchanged",
    "HPFAR":         "Unchanged",
    "HRMR":          "Unchanged",
    "HSTR":          "Unchanged",
    "HTPIDR":        "Unchanged",
    "HVBAR":         "Unchanged",
    "ID_AFR0":       "Unchanged",
    "ID_DFR0":       "Unchanged",
    "ID_ISAR0":      "Unchanged",
    "ID_ISAR1":      "Unchanged",
    "ID_ISAR2":      "Unchanged",
    "ID_ISAR3":      "Unchanged",
    "ID_ISAR4":      "Unchanged",
    "ID_ISAR5":      "Unchanged",
    "ID_MMFR1":      "Unchanged",
    "ID_MMFR3":      "Unchanged",
    "ID_MMFR4":      "Unchanged",
    "ID_PFR0":       "Unchanged",
    "ID_PFR1":       "Unchanged",
    "IFAR":          "Unchanged",
    "ISR":           "Unchanged",
    "JIDR":          "Unchanged",
    "JMCR":          "Unchanged",
    "JOSCR":         "Unchanged",
    "MAIR0":         "Unchanged",
    "MAIR1":         "Unchanged",
    "MIDR":          "Unchanged",
    "MPIDR":         "Unchanged",
    "MVBAR":         "Unchanged",
    "MVFR0":         "Unchanged",
    "MVFR1":         "Unchanged",
    "MVFR2":         "Unchanged",
    "NSACR":         "Unchanged",
    "PAR":           "Unchanged",
    "PMCCFILTR":     "Unchanged",
    "PMCCNTR":       "Unchanged",
    "PMCEID0":       "Unchanged",
    "PMCEID1":       "Unchanged",
    "PMCNTENCLR":    "Unchanged",
    "PMCNTENSET":    "Unchanged",
    "PMEVCNTR<n>":   "Unchanged",
    "PMEVTYPER<n>":  "Unchanged",
    "PMINTENCLR":    "Unchanged",
    "PMINTENSET":    "Unchanged",
    "PMOVSR":        "Unchanged",
    "PMOVSSET":      "Unchanged",
    "PMSELR":        "Unchanged",
    "PMSWINC":       "Unchanged",
    "PMUSERENR":     "Unchanged",
    "PMXEVCNTR":     "Unchanged",
    "PMXEVTYPER":    "Unchanged",
    "REVIDR":        "Unchanged",
    "RVBAR":         "Unchanged",
    "SPSR":          "Unchanged",
    "TCMTR":         "Unchanged",
    "TPIDRPRW":      "Unchanged",
    "TPIDRURO":      "Unchanged",
    "TPIDRURW":      "Unchanged",
    "VBAR":          "Unchanged",
    "VMPIDR":        "Unchanged",
    "VPIDR":         "Unchanged",
    # Redefined (PAR is in Table E1-1 as "Unchanged" but has its own E2.1 section)
    "PAR":           "Redefined",
    "DBGAUTHSTATUS": "Redefined",
    "DBGDSCRext":    "Redefined",
    "DFSR":          "Redefined",
    "FPSCR":         "Redefined",
    "HCPTR":         "Redefined",
    "HCR":           "Redefined",
    "HCR2":          "Redefined",
    "HDCR":          "Redefined",
    "HSCTLR":        "Redefined",
    "HSR":           "Redefined",
    "ID_MMFR0":      "Redefined",
    "ID_MMFR2":      "Redefined",
    "IFSR":          "Redefined",
    "PMCR":          "Redefined",
    "SCTLR":         "Redefined",
    # New (R-profile only)
    "HMPUIR":        "New",
    "HPRBAR":        "New",
    "HPRBAR<n>":     "New",
    "HPRENR":        "New",
    "HPRLAR":        "New",
    "HPRLAR<n>":     "New",
    "HPRSELR":       "New",
    "MPUIR":         "New",
    "PRBAR":         "New",
    "PRBAR<n>":      "New",
    "PRLAR":         "New",
    "PRLAR<n>":      "New",
    "PRSELR":        "New",
    "VSCTLR":        "New",
    # Unused (NMRR, PRRR, RMR) are deliberately omitted
}

# ---------------------------------------------------------------------------
# New register definitions extracted from DDI0568 Chapter E2.2
# ---------------------------------------------------------------------------

DDI0568_URL = "https://developer.arm.com/documentation/ddi0568/latest"


def _res0(msb, lsb):
    return {"name": "RES0", "msb": msb, "lsb": lsb,
            "description": "Reserved, RES0.", "values": [], "reserved": True, "rwtype": "RES0"}


def _f(name, msb, lsb, desc, vals=None):
    """Shorthand for a normal (non-reserved) field."""
    return {"name": name, "msb": msb, "lsb": lsb, "description": desc,
            "values": vals or [], "reserved": False, "rwtype": None}


# ---------------------------------------------------------------------------
# Redefined register field definitions extracted from DDI0568 Chapter E2.1
# These replace the A-profile field data for "Redefined" registers.
# ---------------------------------------------------------------------------

REDEFINED_REGISTERS = [
    {
        "name": "DBGAUTHSTATUS",
        "description": "Provides information about the state of the IMPLEMENTATION DEFINED authentication interface for debug.",
        "fields": [
            _res0(31, 12),
            _f("HNID", 11, 10, "Hyp non-invasive debug.", [
                {"val": 0, "label": "Separate Hyp enable not implemented, or EL2 not implemented."},
                {"val": 2, "label": "Implemented and disabled. ExternalHypNoninvasiveDebugEnabled() == FALSE."},
                {"val": 3, "label": "Implemented and enabled. ExternalHypNoninvasiveDebugEnabled() == TRUE."},
            ]),
            _f("HID", 9, 8, "Hyp invasive debug.", [
                {"val": 0, "label": "Separate Hyp enable not implemented, or EL2 not implemented."},
                {"val": 2, "label": "Implemented and disabled. ExternalHypInvasiveDebugEnabled() == FALSE."},
                {"val": 3, "label": "Implemented and enabled. ExternalHypInvasiveDebugEnabled() == TRUE."},
            ]),
            _f("SNID", 7, 6, "Secure non-invasive debug.", [
                {"val": 0, "label": "Not implemented."},
            ]),
            _f("SID", 5, 4, "Secure invasive debug.", [
                {"val": 0, "label": "Not implemented."},
            ]),
            _f("NSNID", 3, 2, "Non-secure non-invasive debug.", [
                {"val": 2, "label": "Implemented and disabled. ExternalNoninvasiveDebugEnabled() == FALSE."},
                {"val": 3, "label": "Implemented and enabled. ExternalNoninvasiveDebugEnabled() == TRUE."},
            ]),
            _f("NSID", 1, 0, "Non-secure invasive debug.", [
                {"val": 2, "label": "Implemented and disabled. ExternalInvasiveDebugEnabled() == FALSE."},
                {"val": 3, "label": "Implemented and enabled. ExternalInvasiveDebugEnabled() == TRUE."},
            ]),
        ],
    },
    {
        "name": "DBGDSCRext",
        "description": "Main control register for the debug implementation.",
        "fields": [
            _res0(31, 31),
            _f("RXfull", 30, 30, "DTRRX full. Used for save/restore of EDSCR.RXfull."),
            _f("TXfull", 29, 29, "DTRTX full. Used for save/restore of EDSCR.TXfull."),
            _res0(28, 28),
            _f("RXO", 27, 27, "Used for save/restore of EDSCR.RXO."),
            _f("TXU", 26, 26, "Used for save/restore of EDSCR.TXU."),
            _res0(25, 24),
            _f("INTdis", 23, 22, "Used for save/restore of EDSCR.INTdis."),
            _f("TDA", 21, 21, "Used for save/restore of EDSCR.TDA."),
            _res0(20, 19),
            _f("NS", 18, 18, "Non-secure status. This bit is RES1. Arm deprecates use of this field."),
            _f("SPNIDdis", 17, 17, "Secure privileged profiling disabled status bit. This bit is RES0. Arm deprecates use of this field."),
            _f("SPIDdis", 16, 16, "Secure privileged AArch32 invasive self-hosted debug disabled status bit. This bit is RES0. Arm deprecates use of this field."),
            _f("MDBGen", 15, 15, "Monitor debug events enable. Enables Breakpoint, Watchpoint, and Vector Catch exceptions.", [
                {"val": 0, "label": "Breakpoint, Watchpoint, and Vector Catch exceptions disabled."},
                {"val": 1, "label": "Breakpoint, Watchpoint, and Vector Catch exceptions enabled."},
            ]),
            _f("HDE", 14, 14, "Used for save/restore of EDSCR.HDE."),
            _res0(13, 13),
            _f("UDCCdis", 12, 12, "Traps EL0 accesses to the DCC registers to Undefined mode.", [
                {"val": 0, "label": "EL0 accesses to the DCC registers are not trapped to Undefined mode."},
                {"val": 1, "label": "EL0 accesses to DBGDSCRint, DBGDTRRXint, DBGDTRTXint, DBGDIDR, DBGDSAR, and DBGDRAR are trapped to Undefined mode."},
            ]),
            _res0(11, 7),
            _f("ERR", 6, 6, "Used for save/restore of EDSCR.ERR."),
            _f("MOE", 5, 2, "Method of Entry for debug exception.", [
                {"val": 1,  "label": "Breakpoint."},
                {"val": 3,  "label": "Software breakpoint (BKPT) instruction."},
                {"val": 5,  "label": "Vector catch."},
                {"val": 10, "label": "Watchpoint."},
            ]),
            _res0(1, 0),
        ],
    },
    {
        "name": "DFSR",
        "description": "Holds status information about the last data fault.",
        "fields": [
            _res0(31, 17),
            _f("FnV", 16, 16, "FAR not Valid, for a Synchronous External abort. RES0 for all other Data Abort exceptions.", [
                {"val": 0, "label": "DFAR is valid."},
                {"val": 1, "label": "DFAR is not valid, and holds an UNKNOWN value."},
            ]),
            _res0(15, 14),
            _f("CM", 13, 13, "Cache maintenance fault. Indicates whether a cache maintenance instruction generated the fault.", [
                {"val": 0, "label": "Abort not caused by execution of a cache maintenance instruction."},
                {"val": 1, "label": "Abort caused by execution of a cache maintenance instruction."},
            ]),
            _f("ExT", 12, 12, "External abort type. IMPLEMENTATION DEFINED classification of External aborts."),
            _f("WnR", 11, 11, "Write not Read. Indicates whether the abort was caused by a write or a read instruction.", [
                {"val": 0, "label": "Abort caused by a read instruction."},
                {"val": 1, "label": "Abort caused by a write instruction."},
            ]),
            _res0(10, 10),
            _f("LPAE", 9, 9, "Reserved, RES1. Indicates long-descriptor translation table format."),
            _res0(8, 6),
            _f("STATUS", 5, 0, "Fault status bits.", [
                {"val": 0b000100, "label": "Translation fault"},
                {"val": 0b001100, "label": "Permission fault"},
                {"val": 0b010000, "label": "Synchronous External abort"},
                {"val": 0b010001, "label": "SError interrupt"},
                {"val": 0b011000, "label": "Synchronous parity or ECC error on memory access"},
                {"val": 0b011001, "label": "SError parity or ECC error on memory access"},
                {"val": 0b100001, "label": "Alignment fault"},
                {"val": 0b100010, "label": "Debug exception"},
                {"val": 0b110100, "label": "IMPLEMENTATION DEFINED fault (Cache lockdown fault)"},
                {"val": 0b110101, "label": "IMPLEMENTATION DEFINED fault (Unsupported Exclusive access fault)"},
            ]),
        ],
    },
    {
        "name": "HCPTR",
        "description": "Controls trapping to Hyp mode of access, at EL1 or EL0, to trace and to Advanced SIMD or floating-point functionality.",
        "fields": [
            _f("TCPAC", 31, 31, "Traps EL1 accesses to the CPACR to Hyp mode.", [
                {"val": 0, "label": "This control has no effect on EL1 accesses to the CPACR."},
                {"val": 1, "label": "EL1 accesses to the CPACR are trapped to Hyp mode."},
            ]),
            _res0(30, 21),
            _f("TTA", 20, 20, "Traps System register accesses to all implemented trace registers to Hyp mode.", [
                {"val": 0, "label": "This control has no effect on System register accesses to trace registers."},
                {"val": 1, "label": "Any System register access to an implemented trace register is trapped to Hyp mode."},
            ]),
            _res0(19, 16),
            _f("TASE", 15, 15, "Traps execution of Advanced SIMD instructions to Hyp mode when HCPTR.TCP10 is 0.", [
                {"val": 0, "label": "This control has no effect on execution of Advanced SIMD instructions."},
                {"val": 1, "label": "When TCP10 is 0, any attempt to execute an Advanced SIMD instruction is trapped to Hyp mode."},
            ]),
            _res0(14, 14),
            {"name": "RES1", "msb": 13, "lsb": 12, "description": "Reserved, RES1.", "values": [], "reserved": False, "rwtype": "RES1"},
            _f("TCP11", 11, 11, "The value of this field is ignored. Mirrors TCP10 for legacy compatibility."),
            _f("TCP10", 10, 10, "Trap accesses to Advanced SIMD and floating-point functionality to Hyp mode.", [
                {"val": 0, "label": "This control has no effect on accesses to Advanced SIMD and floating-point functionality."},
                {"val": 1, "label": "Any attempted access to Advanced SIMD and floating-point functionality is trapped to Hyp mode."},
            ]),
            {"name": "RES1", "msb": 9, "lsb": 0, "description": "Reserved, RES1.", "values": [], "reserved": False, "rwtype": "RES1"},
        ],
    },
    {
        "name": "HCR",
        "description": "Provides configuration controls for virtualization, including defining whether various Non-secure operations are trapped to Hyp mode.",
        "fields": [
            _res0(31, 31),
            _f("TRVM", 30, 30, "Trap Reads of Memory controls. Traps EL1 reads of the memory control registers to Hyp mode.", [
                {"val": 0, "label": "This control has no effect on EL1 read accesses to memory control registers."},
                {"val": 1, "label": "EL1 read accesses to the memory control registers are trapped to Hyp mode."},
            ]),
            _f("HCD", 29, 29, "HVC instruction disable.", [
                {"val": 0, "label": "HVC instruction execution is enabled at EL2 and EL1."},
                {"val": 1, "label": "HVC instructions are UNDEFINED at EL2 and EL1."},
            ]),
            _res0(28, 28),
            _f("TGE", 27, 27, "Trap General Exceptions from EL0. When set, all exceptions that would be routed to EL1 are routed to EL2.", [
                {"val": 0, "label": "This control has no effect on execution at EL0."},
                {"val": 1, "label": "All exceptions that would be routed to EL1 are routed to EL2."},
            ]),
            _f("TVM", 26, 26, "Trap Memory controls. Traps EL1 writes to the memory control registers to Hyp mode.", [
                {"val": 0, "label": "This control has no effect on EL1 write accesses to EL1 memory control registers."},
                {"val": 1, "label": "EL1 write accesses to EL1 memory control registers are trapped to Hyp mode."},
            ]),
            _res0(25, 25),
            _f("TPU", 24, 24, "Trap cache maintenance instructions that operate to the Point of Unification.", [
                {"val": 0, "label": "This control has no effect on the execution of cache maintenance instructions."},
                {"val": 1, "label": "EL1 execution of the specified instructions is trapped to Hyp mode."},
            ]),
            _f("TPC", 23, 23, "Trap data or unified cache maintenance instructions that operate to the Point of Coherency.", [
                {"val": 0, "label": "This control has no effect on the execution of cache maintenance instructions."},
                {"val": 1, "label": "EL1 execution of the specified instructions is trapped to Hyp mode."},
            ]),
            _f("TSW", 22, 22, "Trap data or unified cache maintenance instructions that operate by Set/Way.", [
                {"val": 0, "label": "This control has no effect on the execution of cache maintenance instructions."},
                {"val": 1, "label": "EL1 execution of the specified instructions is trapped to Hyp mode."},
            ]),
            _f("TAC", 21, 21, "Trap Auxiliary Control Registers. Traps EL1 accesses to ACTLR and ACTLR2 to Hyp mode.", [
                {"val": 0, "label": "This control has no effect on EL1 accesses to the Auxiliary Control Registers."},
                {"val": 1, "label": "EL1 accesses to the Auxiliary Control Registers are trapped to Hyp mode."},
            ]),
            _f("TIDCP", 20, 20, "Trap IMPLEMENTATION DEFINED functionality. Traps EL1 accesses to encodings for IMPLEMENTATION DEFINED System Registers to Hyp mode.", [
                {"val": 0, "label": "This control has no effect on EL1 and EL0 accesses to the System register encodings for IMPLEMENTATION DEFINED functionality."},
                {"val": 1, "label": "EL1 accesses to the IMPLEMENTATION DEFINED System register encodings are trapped to Hyp mode."},
            ]),
            _res0(19, 19),
            _f("TID3", 18, 18, "Trap ID group 3. Traps EL1 reads of ID_PFR0/1, ID_DFR0, ID_AFR0, ID_MMFR0-4, ID_ISAR0-5, MVFR0-2 to Hyp mode.", [
                {"val": 0, "label": "This control has no effect on EL1 reads of the ID group 3 registers."},
                {"val": 1, "label": "The specified EL1 read accesses to ID group 3 registers are trapped to Hyp mode."},
            ]),
            _f("TID2", 17, 17, "Trap ID group 2. Traps EL1/EL0 reads of CTR, CCSIDR, CLIDR, CSSELR, and EL1/EL0 writes to CSSELR.", [
                {"val": 0, "label": "This control has no effect on EL1 and EL0 accesses to the ID group 2 registers."},
                {"val": 1, "label": "The specified EL1 and EL0 accesses to ID group 2 registers are trapped to Hyp mode."},
            ]),
            _f("TID1", 16, 16, "Trap ID group 1. Traps EL1 reads of TCMTR, TLBTR, REVIDR, AIDR, MPUIR to Hyp mode.", [
                {"val": 0, "label": "This control has no effect on EL1 reads of the ID group 1 registers."},
                {"val": 1, "label": "The specified EL1 read accesses to ID group 1 registers are trapped to Hyp mode."},
            ]),
            _f("TID0", 15, 15, "Trap ID group 0. Traps EL1 reads of JIDR and FPSID to Hyp mode.", [
                {"val": 0, "label": "This control has no effect on EL1 reads of the ID group 0 registers."},
                {"val": 1, "label": "The specified EL1 read accesses to ID group 0 registers are trapped to Hyp mode."},
            ]),
            _f("TWE", 14, 14, "Traps EL0 and EL1 execution of WFE instructions to Hyp mode.", [
                {"val": 0, "label": "This control has no effect on the execution of WFE instructions at EL0 or EL1."},
                {"val": 1, "label": "Any attempt to execute a WFE instruction at EL0 or EL1 is trapped to Hyp mode if it would cause a low-power state."},
            ]),
            _f("TWI", 13, 13, "Traps EL0 and EL1 execution of WFI instructions to Hyp mode.", [
                {"val": 0, "label": "This control has no effect on the execution of WFI instructions at EL1 or EL0."},
                {"val": 1, "label": "Any attempt to execute a WFI instruction at EL0 or EL1 is trapped to Hyp mode if it would cause a low-power state."},
            ]),
            _f("DC", 12, 12, "Default Cacheability. When set, forces VM=1 and sets the EL1&0 default memory type to Normal Write-Back cacheable.", [
                {"val": 0, "label": "This control has no effect on the EL1&0 translation regime."},
                {"val": 1, "label": "HCR.VM behaves as 1; EL1&0 default memory map uses Normal WB cacheable memory type."},
            ]),
            _f("BSU", 11, 10, "Barrier Shareability upgrade. Determines the minimum Shareability domain applied to any barrier instruction from EL1 or EL0.", [
                {"val": 0, "label": "No effect."},
                {"val": 1, "label": "Inner Shareable."},
                {"val": 2, "label": "Outer Shareable."},
                {"val": 3, "label": "Full system."},
            ]),
            _f("FB", 9, 9, "Force broadcast. Causes BPIALL and ICIALLU to be broadcast within the Inner Shareable domain when executed from EL1.", [
                {"val": 0, "label": "This field has no effect on the operation of the specified instructions."},
                {"val": 1, "label": "When one of the specified instructions is executed at EL1, the instruction is broadcast within the Inner Shareable domain."},
            ]),
            _f("VA", 8, 8, "Virtual SError interrupt exception.", [
                {"val": 0, "label": "This mechanism is not making a virtual SError interrupt pending."},
                {"val": 1, "label": "A virtual SError interrupt is pending because of this mechanism."},
            ]),
            _f("VI", 7, 7, "Virtual IRQ exception.", [
                {"val": 0, "label": "This mechanism is not making a virtual IRQ pending."},
                {"val": 1, "label": "A virtual IRQ is pending because of this mechanism."},
            ]),
            _f("VF", 6, 6, "Virtual FIQ exception.", [
                {"val": 0, "label": "This mechanism is not making a virtual FIQ pending."},
                {"val": 1, "label": "A virtual FIQ is pending because of this mechanism."},
            ]),
            _f("AMO", 5, 5, "SError interrupt Mask Override. Overrides CPSR.A and enables virtual SError signaling via the VA bit."),
            _f("IMO", 4, 4, "IRQ Mask Override. Overrides CPSR.I and enables virtual IRQ signaling via the VI bit."),
            _f("FMO", 3, 3, "FIQ Mask Override. Overrides CPSR.F and enables virtual FIQ signaling via the VF bit."),
            _res0(2, 2),
            _f("SWIO", 1, 1, "Set/Way Invalidation Override. Causes EL1 data cache invalidate by set/way to operate as clean and invalidate.", [
                {"val": 0, "label": "This control has no effect on the operation of data cache invalidate by set/way instructions."},
                {"val": 1, "label": "Data cache invalidate by set/way instructions operate as data cache clean and invalidate by set/way."},
            ]),
            _f("VM", 0, 0, "Virtualization enable. Enables stage 2 protection for EL1 and EL0 accesses via the EL2 MPU.", [
                {"val": 0, "label": "EL1 and EL0 stage 2 address protection disabled."},
                {"val": 1, "label": "EL1 and EL0 stage 2 address protection enabled and attribute combination enabled."},
            ]),
        ],
    },
    {
        "name": "HCR2",
        "description": "Provides additional configuration controls for virtualization.",
        "fields": [
            _res0(31, 7),
            _f("MIOCNCE", 6, 6, "Mismatched Inner/Outer Cacheable Non-Coherency Enable for the EL1&0 translation regime.", [
                {"val": 0, "label": "No loss of coherency if Inner Cacheability attribute differs from Outer Cacheability attribute."},
                {"val": 1, "label": "There might be a loss of coherency if Inner Cacheability attribute differs from Outer Cacheability attribute."},
            ]),
            _res0(5, 0),
        ],
    },
    {
        "name": "HDCR",
        "description": "Controls the trapping to Hyp mode of Non-secure accesses, at EL1 or lower, to functions provided by the debug and trace architectures and the Performance Monitors Extension.",
        "fields": [
            _res0(31, 22),
            _f("EPMAD", 21, 21, "External debug interface access to Hyp mode Performance Monitors registers disable.", [
                {"val": 0, "label": "Access to all Performance Monitors counters by an external debugger is permitted."},
                {"val": 1, "label": "Access to Performance Monitors counters in the range [HPMN..(PMCR.N-1)] by an external debugger is disabled."},
            ]),
            _res0(20, 18),
            _f("HPMD", 17, 17, "Hyp Performance Monitors Disable. Prohibits event counting in Hyp mode by the counters accessible at EL1.", [
                {"val": 0, "label": "Event counting by EL1-accessible counters allowed in Hyp mode."},
                {"val": 1, "label": "Event counting by EL1-accessible counters prohibited in Hyp mode."},
            ]),
            _res0(16, 12),
            _f("TDRA", 11, 11, "Trap Debug ROM Address register access. Traps EL0 and EL1 accesses to DBGDRAR or DBGDSAR to Hyp mode.", [
                {"val": 0, "label": "EL0 and EL1 System register accesses to the Debug ROM registers are not trapped to Hyp mode."},
                {"val": 1, "label": "EL0 and EL1 System register accesses to the DBGDRAR or DBGDSAR are trapped to Hyp mode."},
            ]),
            _f("TDOSA", 10, 10, "Trap debug OS-related register access. Traps EL1 accesses to the powerdown debug registers to Hyp mode.", [
                {"val": 0, "label": "EL1 System register accesses to the powerdown debug registers are not trapped to Hyp mode."},
                {"val": 1, "label": "EL1 System register accesses to the powerdown debug registers are trapped to Hyp mode."},
            ]),
            _f("TDA", 9, 9, "Trap debug access. Traps EL0 and EL1 accesses to debug registers not trapped by TDRA or TDOSA.", [
                {"val": 0, "label": "Has no effect on System register accesses to the debug registers."},
                {"val": 1, "label": "EL0 or EL1 System register accesses to the debug registers (other than those trapped by TDRA/TDOSA) are trapped to Hyp mode."},
            ]),
            _f("TDE", 8, 8, "Trap Debug exceptions. Routes debug exceptions generated at EL1 or EL0 to EL2.", [
                {"val": 0, "label": "This control has no effect on the routing of debug exceptions."},
                {"val": 1, "label": "Debug exceptions generated at EL1 or EL0 are routed to EL2."},
            ]),
            _f("HPME", 7, 7, "Hyp Performance Monitors Enable. Controls whether counters not accessible at EL1 are enabled.", [
                {"val": 0, "label": "All counters that are not accessible at EL1 are disabled."},
                {"val": 1, "label": "All counters that are not accessible at EL1 are enabled by PMCNTENSET."},
            ]),
            _f("TPM", 6, 6, "Trap Performance Monitors accesses. Traps EL0 and EL1 accesses to all Performance Monitors registers to Hyp mode.", [
                {"val": 0, "label": "EL0 and EL1 accesses to all Performance Monitors registers are not trapped to Hyp mode."},
                {"val": 1, "label": "EL0 and EL1 accesses to all Performance Monitors registers are trapped to Hyp mode."},
            ]),
            _f("TPMCR", 5, 5, "Trap PMCR accesses. Traps EL0 and EL1 accesses to the PMCR to Hyp mode.", [
                {"val": 0, "label": "This control does not cause any instructions to be trapped."},
                {"val": 1, "label": "EL0 and EL1 accesses to the PMCR are trapped to Hyp mode."},
            ]),
            _f("HPMN", 4, 0, "Defines the number of Performance Monitors counters accessible from EL1 and (if unprivileged access is enabled) EL0."),
        ],
    },
    {
        "name": "HSCTLR",
        "description": "Provides top-level control of the system operation in Hyp mode.",
        "fields": [
            _res0(31, 31),
            _f("TE", 30, 30, "T32 Exception Enable. Controls whether exceptions to EL2 are taken to A32 or T32 state.", [
                {"val": 0, "label": "Exceptions, including reset, taken to A32 state."},
                {"val": 1, "label": "Exceptions, including reset, taken to T32 state."},
            ]),
            {"name": "RES1", "msb": 29, "lsb": 28, "description": "Reserved, RES1.", "values": [], "reserved": False, "rwtype": "RES1"},
            _res0(27, 26),
            _f("EE", 25, 25, "The value of the PSTATE.E bit on entry to Hyp mode.", [
                {"val": 0, "label": "Little-endian. PSTATE.E is cleared to 0 on entry to Hyp mode."},
                {"val": 1, "label": "Big-endian. PSTATE.E is set to 1 on entry to Hyp mode."},
            ]),
            _res0(24, 24),
            {"name": "RES1", "msb": 23, "lsb": 22, "description": "Reserved, RES1.", "values": [], "reserved": False, "rwtype": "RES1"},
            _f("FI", 21, 21, "Fast Interrupts enable. When set, enables low interrupt latency configuration with some performance features disabled.", [
                {"val": 0, "label": "All performance features enabled."},
                {"val": 1, "label": "Low interrupt latency configuration. Some performance features disabled."},
            ]),
            _res0(20, 20),
            _f("WXN", 19, 19, "Write permission implies XN (Execute-never) for the EL2 MPU translation regime.", [
                {"val": 0, "label": "This control has no effect on memory access permissions."},
                {"val": 1, "label": "Any region that is writable in the EL2 translation regime is forced to XN for accesses from EL2."},
            ]),
            {"name": "RES1", "msb": 18, "lsb": 18, "description": "Reserved, RES1.", "values": [], "reserved": False, "rwtype": "RES1"},
            _f("BR", 17, 17, "Background Region enable for EL2. Controls how EL2 accesses not matching any EL2 MPU region are handled.", [
                {"val": 0, "label": "EL2 MPU Background region disabled. Any EL2 transaction not matching an EL2 MPU region results in a fault."},
                {"val": 1, "label": "EL2 MPU Background region enabled. Transactions not matching an EL2 MPU region use Background region attributes."},
            ]),
            {"name": "RES1", "msb": 16, "lsb": 16, "description": "Reserved, RES1.", "values": [], "reserved": False, "rwtype": "RES1"},
            _res0(15, 13),
            _f("I", 12, 12, "Instruction access Cacheability control for accesses at EL2.", [
                {"val": 0, "label": "All instruction access to Normal memory from EL2 are Non-cacheable."},
                {"val": 1, "label": "All instruction access to Normal memory from EL2 can be cached at all levels."},
            ]),
            {"name": "RES1", "msb": 11, "lsb": 11, "description": "Reserved, RES1.", "values": [], "reserved": False, "rwtype": "RES1"},
            _res0(10, 9),
            _f("SED", 8, 8, "SETEND instruction disable. Disables SETEND instructions at EL2.", [
                {"val": 0, "label": "SETEND instruction execution is enabled at EL2."},
                {"val": 1, "label": "SETEND instructions are UNDEFINED at EL2."},
            ]),
            _f("ITD", 7, 7, "IT Disable. Disables some uses of IT instructions at EL2.", [
                {"val": 0, "label": "All IT instruction functionality is enabled at EL2."},
                {"val": 1, "label": "Any attempt at EL2 to execute certain IT-related instruction sequences is UNDEFINED."},
            ]),
            _res0(6, 6),
            _f("CP15BEN", 5, 5, "System instruction memory barrier enable. Enables DMB, DSB, and ISB System instructions (coproc==1111) from EL2.", [
                {"val": 0, "label": "EL2 execution of the CP15DMB, CP15DSB, and CP15ISB instructions is UNDEFINED."},
                {"val": 1, "label": "EL2 execution of the CP15DMB, CP15DSB, and CP15ISB instructions is enabled."},
            ]),
            {"name": "RES1", "msb": 4, "lsb": 3, "description": "Reserved, RES1.", "values": [], "reserved": False, "rwtype": "RES1"},
            _f("C", 2, 2, "Cacheability control for data accesses at EL2.", [
                {"val": 0, "label": "All data accesses to Normal memory from EL2 are Non-cacheable."},
                {"val": 1, "label": "All data accesses to Normal memory from EL2 can be cached at all levels."},
            ]),
            _f("A", 1, 1, "Alignment check enable. Enable bit for Alignment fault checking at EL2.", [
                {"val": 0, "label": "Alignment fault checking disabled when executing at EL2."},
                {"val": 1, "label": "Alignment fault checking enabled when executing at EL2."},
            ]),
            _f("M", 0, 0, "MPU enable for the EL2 MPU.", [
                {"val": 0, "label": "EL2 MPU disabled."},
                {"val": 1, "label": "EL2 MPU enabled."},
            ]),
        ],
    },
    {
        "name": "HSR",
        "description": "Holds syndrome information for an exception taken to Hyp mode.",
        "fields": [
            _f("EC", 31, 26, "Exception Class. Indicates the reason for the exception.", [
                {"val": 0b000000, "label": "Unknown reason."},
                {"val": 0b000001, "label": "Trapped WFI or WFE instruction execution."},
                {"val": 0b000011, "label": "Trapped MCR or MRC access with (coproc==1111) not reported using EC 0b000000."},
                {"val": 0b000100, "label": "Trapped MCRR or MRRC access with (coproc==1111) not reported using EC 0b000000."},
                {"val": 0b000101, "label": "Trapped MCR or MRC access with (coproc==1110)."},
                {"val": 0b000110, "label": "Trapped LDC or STC access."},
                {"val": 0b000111, "label": "Access to Advanced SIMD or floating-point functionality trapped by HCPTR.{TASE, TCP10}."},
                {"val": 0b001000, "label": "Trapped VMRS access from ID group trap, not reported using EC 0b000111."},
                {"val": 0b001100, "label": "Trapped MRRC access with (coproc==1110)."},
                {"val": 0b001110, "label": "Illegal exception return to AArch32 state."},
                {"val": 0b010001, "label": "Exception on SVC instruction execution in AArch32 state routed to EL2."},
                {"val": 0b010010, "label": "HVC instruction execution in AArch32 state, when HVC is not disabled."},
                {"val": 0b100000, "label": "Prefetch Abort from a lower Exception level."},
                {"val": 0b100001, "label": "Prefetch Abort taken without a change in Exception level."},
                {"val": 0b100010, "label": "PC alignment fault exception."},
                {"val": 0b100100, "label": "Data Abort from a lower Exception level."},
                {"val": 0b100101, "label": "Data Abort taken without a change in Exception level."},
            ]),
            _f("IL", 25, 25, "Instruction length bit. Indicates the size of the instruction trapped to Hyp mode.", [
                {"val": 0, "label": "16-bit instruction trapped."},
                {"val": 1, "label": "32-bit instruction trapped."},
            ]),
            _f("ISS", 24, 0, "Instruction Specific Syndrome. Format depends on the EC field value."),
        ],
    },
    {
        "name": "ID_MMFR0",
        "description": "Provides information about the implemented memory model and memory management support in AArch32 state.",
        "fields": [
            _f("InnerShr", 31, 28, "Innermost Shareability domain implemented.", [
                {"val": 0b0000, "label": "Implemented as Non-cacheable."},
                {"val": 0b0001, "label": "Implemented with hardware coherency support."},
                {"val": 0b1111, "label": "Shareability ignored."},
            ]),
            _f("FCSE", 27, 24, "Indicates whether the implementation includes the FCSE. In Armv8-R the only permitted value is 0000.", [
                {"val": 0b0000, "label": "Not supported."},
                {"val": 0b0001, "label": "Support for FCSE."},
            ]),
            _f("AuxReg", 23, 20, "Auxiliary Registers. Indicates support for Auxiliary registers.", [
                {"val": 0b0000, "label": "None supported."},
                {"val": 0b0001, "label": "Support for Auxiliary Control Register only."},
                {"val": 0b0010, "label": "Support for Auxiliary Fault Status Registers (AIFSR and ADFSR) and Auxiliary Control Register."},
            ]),
            _f("TCM", 19, 16, "Indicates support for TCMs and associated DMAs.", [
                {"val": 0b0000, "label": "Not supported."},
                {"val": 0b0001, "label": "Support is IMPLEMENTATION DEFINED."},
                {"val": 0b0010, "label": "Support for TCM only, Armv6 implementation."},
                {"val": 0b0011, "label": "Support for TCM and DMA, Armv6 implementation."},
            ]),
            _f("ShareLvl", 15, 12, "Shareability Levels. Indicates the number of Shareability levels implemented.", [
                {"val": 0b0000, "label": "One level of shareability implemented."},
                {"val": 0b0001, "label": "Two levels of shareability implemented."},
            ]),
            _f("OuterShr", 11, 8, "Outermost Shareability domain implemented.", [
                {"val": 0b0000, "label": "Implemented as Non-cacheable."},
                {"val": 0b0001, "label": "Implemented with hardware coherency support."},
                {"val": 0b1111, "label": "Shareability ignored."},
            ]),
            _f("PMSA", 7, 4, "Indicates support for a PMSA.", [
                {"val": 0b0000, "label": "Not supported."},
                {"val": 0b0001, "label": "Support for IMPLEMENTATION DEFINED PMSA."},
                {"val": 0b0010, "label": "Support for PMSAv6, with a Cache Type Register implemented."},
                {"val": 0b0011, "label": "Support for PMSAv7, with support for memory subsections (Armv7-R profile)."},
                {"val": 0b0100, "label": "Support for Armv8-R base and limit PMSA."},
            ]),
            _f("VMSA", 3, 0, "Indicates support for a VMSA. In Armv8-R the only permitted value is 0000.", [
                {"val": 0b0000, "label": "Not supported."},
                {"val": 0b0001, "label": "Support for IMPLEMENTATION DEFINED VMSA."},
                {"val": 0b0010, "label": "Support for VMSAv6, with Cache and TLB Type Registers implemented."},
                {"val": 0b0011, "label": "Support for VMSAv7, with support for remapping and the Access flag (Armv7-A profile)."},
                {"val": 0b0100, "label": "As for 0011, and adds support for the PXN bit in Short-descriptor translation table format descriptors."},
                {"val": 0b0101, "label": "As for 0100, and adds support for the Long-descriptor translation table format."},
            ]),
        ],
    },
    {
        "name": "ID_MMFR2",
        "description": "Provides information about the implemented memory model and memory management support in AArch32 state.",
        "fields": [
            _f("HWAccFlg", 31, 28, "Hardware Access Flag. Indicates support for a Hardware Access flag as part of VMSAv7. In Armv8-R the only permitted value is 0000.", [
                {"val": 0b0000, "label": "Not supported."},
                {"val": 0b0001, "label": "Support for VMSAv7 Access flag, updated in hardware."},
            ]),
            _f("WFIStall", 27, 24, "Wait For Interrupt Stall. Indicates the support for WFI stalling.", [
                {"val": 0b0000, "label": "Not supported."},
                {"val": 0b0001, "label": "Support for WFI stalling."},
            ]),
            _f("MemBarr", 23, 20, "Memory Barrier. Indicates the supported memory barrier System instructions in the (coproc==1111) encoding space.", [
                {"val": 0b0000, "label": "None supported."},
                {"val": 0b0001, "label": "Supported: DSB."},
                {"val": 0b0010, "label": "As for 0001, and adds ISB and DMB."},
            ]),
            _f("UniTLB", 19, 16, "Unified TLB. Indicates supported TLB maintenance operations. In Armv8-R ID_MMFR2.UniTLB == 0b0000.", [
                {"val": 0b0000, "label": "Not supported."},
                {"val": 0b0001, "label": "Supported: Invalidate all entries, Invalidate TLB entry by VA."},
                {"val": 0b0010, "label": "As for 0001, and adds: Invalidate TLB entries by ASID match."},
                {"val": 0b0011, "label": "As for 0010, and adds: Invalidate instruction TLB and data TLB entries by VA All ASID."},
                {"val": 0b0100, "label": "As for 0011, and adds: Invalidate Hyp mode unified TLB entry by VA."},
                {"val": 0b0101, "label": "As for 0100, and adds TLBIMVALIS, TLBIMVAALIS, TLBIMVALHIS, TLBIMVAL, TLBIMVAAL, TLBIMVALH."},
                {"val": 0b0110, "label": "As for 0101, and adds TLBIIPAS2IS, TLBIIPAS2LIS, TLBIIPAS2, TLBIIPAS2L."},
            ]),
            _f("HvdTLB", 15, 12, "IMPLEMENTATION DEFINED. Arm deprecates use of this field by software."),
            _f("L1HvdRng", 11, 8, "Level 1 Harvard cache Range. Indicates supported Level 1 cache maintenance range operations for a Harvard cache implementation.", [
                {"val": 0b0000, "label": "Not supported."},
                {"val": 0b0001, "label": "Supported: Invalidate data/instruction cache range by VA, Clean data cache range by VA, Clean and invalidate data cache range by VA."},
            ]),
            _f("L1HvdBG", 7, 4, "Level 1 Harvard cache Background fetch. Indicates supported Level 1 cache background fetch operations.", [
                {"val": 0b0000, "label": "Not supported."},
                {"val": 0b0001, "label": "Supported: Fetch instruction cache range by VA, Fetch data cache range by VA."},
            ]),
            _f("L1HvdFG", 3, 0, "Level 1 Harvard cache Foreground fetch. Indicates supported Level 1 cache foreground fetch operations.", [
                {"val": 0b0000, "label": "Not supported."},
                {"val": 0b0001, "label": "Supported: Fetch instruction cache range by VA, Fetch data cache range by VA."},
            ]),
        ],
    },
    {
        "name": "IFSR",
        "description": "Holds status information about the last instruction fault.",
        "fields": [
            _res0(31, 17),
            _f("FnV", 16, 16, "FAR not Valid, for a Synchronous External abort. RES0 for all other Prefetch Abort exceptions.", [
                {"val": 0, "label": "IFAR is valid."},
                {"val": 1, "label": "IFAR is not valid, and holds an UNKNOWN value."},
            ]),
            _res0(15, 13),
            _f("ExT", 12, 12, "External abort type. IMPLEMENTATION DEFINED classification of External aborts."),
            _res0(11, 10),
            _f("LPAE", 9, 9, "Reserved, RES1. Indicates long-descriptor translation table format."),
            _res0(8, 6),
            _f("STATUS", 5, 0, "Fault status bits.", [
                {"val": 0b000100, "label": "Translation fault"},
                {"val": 0b001100, "label": "Permission fault"},
                {"val": 0b010000, "label": "Synchronous External abort"},
                {"val": 0b011000, "label": "Synchronous parity or ECC error on memory access"},
                {"val": 0b100001, "label": "PC alignment fault"},
                {"val": 0b100010, "label": "Debug exception"},
            ]),
        ],
    },
    {
        "name": "PAR",
        "description": (
            "Returns the output address (OA) from an Address translation instruction that executed "
            "successfully, or fault information if the instruction did not execute successfully. "
            "In Armv8-R, PAR is a 64-bit register. F bit [0] indicates success (0) or abort (1). "
            "Fields below describe the successful-translation layout (F==0)."
        ),
        "fields": [
            _f("ATTR", 63, 56, "Memory attributes for the returned output address. Uses same encoding as Attr<n> fields in MAIR0 and MAIR1."),
            _res0(55, 40),
            _f("PA", 39, 12, "Output address bits[39:12] corresponding to the supplied input address."),
            _f("LPAE", 11, 11, "Long-descriptor format used. This bit is set to 1, indicating the PAR returned a 64-bit value."),
            _f("IMP_DEF", 10, 10, "IMPLEMENTATION DEFINED."),
            _f("NS", 9, 9, "In Armv8-R, this bit is UNKNOWN."),
            _f("SH", 8, 7, "Shareability attribute for the returned output address.", [
                {"val": 0b00, "label": "Non-shareable."},
                {"val": 0b10, "label": "Outer Shareable."},
                {"val": 0b11, "label": "Inner Shareable."},
            ]),
            _res0(6, 1),
            _f("F", 0, 0, "Indicates whether the instruction performed a successful address translation.", [
                {"val": 0, "label": "Address translation completed successfully."},
                {"val": 1, "label": "Address translation aborted."},
            ]),
        ],
    },
    {
        "name": "PMCR",
        "description": "Provides details of the Performance Monitors implementation, including the number of counters implemented, and configures and controls the counters.",
        "fields": [
            _f("IMP", 31, 24, "Implementer code. RO, IMPLEMENTATION DEFINED value. Use is deprecated."),
            _f("IDCODE", 23, 16, "Identification code. RO, IMPLEMENTATION DEFINED value. Use is deprecated."),
            _f("N", 15, 11, "Number of event counters. RO field indicating the number of event counters implemented."),
            _res0(10, 7),
            _f("LC", 6, 6, "Long cycle counter enable. Determines when unsigned overflow is recorded by the cycle counter.", [
                {"val": 0, "label": "Cycle counter overflow on increment that causes unsigned overflow of PMCCNTR[31:0]."},
                {"val": 1, "label": "Cycle counter overflow on increment that causes unsigned overflow of PMCCNTR[63:0]."},
            ]),
            _f("DP", 5, 5, "Disable cycle counter when event counting is prohibited.", [
                {"val": 0, "label": "Cycle counting by PMCCNTR is not affected by this bit."},
                {"val": 1, "label": "When event counting for counters in [0..(HDCR.HPMN-1)] is prohibited, cycle counting by PMCCNTR is disabled."},
            ]),
            _f("X", 4, 4, "Enable export of events in an IMPLEMENTATION DEFINED PMU event export bus.", [
                {"val": 0, "label": "Do not export events."},
                {"val": 1, "label": "Export events where not prohibited."},
            ]),
            _f("D", 3, 3, "Clock divider for PMCCNTR.", [
                {"val": 0, "label": "When enabled, PMCCNTR counts every clock cycle."},
                {"val": 1, "label": "When enabled, PMCCNTR counts once every 64 clock cycles."},
            ]),
            _f("C", 2, 2, "Cycle counter reset. WO bit; always RAZ. Writing 1 resets PMCCNTR to zero.", [
                {"val": 0, "label": "No action."},
                {"val": 1, "label": "Reset PMCCNTR to zero."},
            ]),
            _f("P", 1, 1, "Event counter reset. WO bit; always RAZ. Writing 1 resets all event counters accessible in the current Exception level (not including PMCCNTR) to zero.", [
                {"val": 0, "label": "No action."},
                {"val": 1, "label": "Reset all event counters in the current Exception level (not including PMCCNTR) to zero."},
            ]),
            _f("E", 0, 0, "Enable. Controls whether event counters and PMCCNTR are enabled.", [
                {"val": 0, "label": "All event counters in [0..(PMN-1)] and PMCCNTR are disabled."},
                {"val": 1, "label": "All event counters in [0..(PMN-1)] and PMCCNTR are enabled by PMCNTENSET."},
            ]),
        ],
    },
    {
        "name": "SCTLR",
        "description": "Provides the top-level control of the system, including its memory system.",
        "fields": [
            _res0(31, 31),
            _f("TE", 30, 30, "T32 Exception Enable. Controls whether exceptions to EL1 are taken to A32 or T32 state.", [
                {"val": 0, "label": "Exceptions, including reset, taken to A32 state."},
                {"val": 1, "label": "Exceptions, including reset, taken to T32 state."},
            ]),
            {"name": "RES1", "msb": 29, "lsb": 28, "description": "Reserved, RES1.", "values": [], "reserved": False, "rwtype": "RES1"},
            _res0(27, 26),
            _f("EE", 25, 25, "The value of the PSTATE.E bit on branch to an exception vector or coming out of reset.", [
                {"val": 0, "label": "Little-endian. PSTATE.E is cleared to 0 on taking an exception or coming out of reset."},
                {"val": 1, "label": "Big-endian. PSTATE.E is set to 1 on taking an exception or coming out of reset."},
            ]),
            _res0(24, 24),
            {"name": "RES1", "msb": 23, "lsb": 22, "description": "Reserved, RES1.", "values": [], "reserved": False, "rwtype": "RES1"},
            _f("FI", 21, 21, "Fast Interrupts enable. This bit is a read-only copy of the HSCTLR.FI bit."),
            _f("UWXN", 20, 20, "Unprivileged write permission implies EL1 XN. Can force regions writable at EL0 to be XN for EL1 accesses.", [
                {"val": 0, "label": "This control has no effect on memory access permissions."},
                {"val": 1, "label": "Any region that is writable at EL0 is forced to XN for accesses from EL1."},
            ]),
            _f("WXN", 19, 19, "Write permission implies XN (Execute-never) for the EL1&0 MPU translation regime.", [
                {"val": 0, "label": "This control has no effect on memory access permissions."},
                {"val": 1, "label": "Any region that is writable in the EL1&0 translation regime is forced to XN for accesses from EL1 or EL0."},
            ]),
            _f("nTWE", 18, 18, "Traps EL0 execution of WFE instructions to Undefined mode.", [
                {"val": 0, "label": "Any attempt to execute a WFE instruction at EL0 is trapped to Undefined mode if it would cause a low-power state."},
                {"val": 1, "label": "This control has no effect on the EL0 execution of WFE instruction."},
            ]),
            _f("BR", 17, 17, "Background Region enable. When the EL1 MPU is enabled, controls how EL1 accesses not matching any MPU region are handled.", [
                {"val": 0, "label": "EL1 MPU Background region disabled. Any EL1 transaction not matching an EL1 MPU region results in a fault."},
                {"val": 1, "label": "EL1 MPU Background region enabled. Transactions not matching an EL1 MPU region use Background region attributes."},
            ]),
            _f("nTWI", 16, 16, "Traps EL0 execution of WFI instructions to Undefined mode.", [
                {"val": 0, "label": "Any attempt to execute a WFI instruction at EL0 is trapped to Undefined mode if it would cause a low-power state."},
                {"val": 1, "label": "This control has no effect on the EL0 execution of WFI instructions."},
            ]),
            _res0(15, 13),
            _f("I", 12, 12, "Instruction access Cacheability control for accesses at EL1 and EL0.", [
                {"val": 0, "label": "All instruction access to Normal memory from EL1 and EL0 are Non-cacheable."},
                {"val": 1, "label": "All instruction access to Normal memory from EL1 and EL0 can be cached at all levels."},
            ]),
            {"name": "RES1", "msb": 11, "lsb": 11, "description": "Reserved, RES1.", "values": [], "reserved": False, "rwtype": "RES1"},
            _res0(10, 9),
            _f("SED", 8, 8, "SETEND instruction disable. Disables SETEND instructions at EL0 and EL1.", [
                {"val": 0, "label": "SETEND instruction execution is enabled at EL0 and EL1."},
                {"val": 1, "label": "SETEND instructions are UNDEFINED at EL0 and EL1."},
            ]),
            _f("ITD", 7, 7, "IT Disable. Disables some uses of IT instructions at EL1 and EL0.", [
                {"val": 0, "label": "All IT instruction functionality is enabled at EL1 and EL0."},
                {"val": 1, "label": "Any attempt at EL1 or EL0 to execute certain IT-related instruction sequences is UNDEFINED."},
            ]),
            _f("UNK", 6, 6, "Writes to this bit are IGNORED. Reads return an UNKNOWN value."),
            _f("CP15BEN", 5, 5, "System instruction memory barrier enable. Enables DMB, DSB, and ISB System instructions (coproc==1111) from EL1 and EL0.", [
                {"val": 0, "label": "EL0 and EL1 execution of the CP15DMB, CP15DSB, and CP15ISB instructions is UNDEFINED."},
                {"val": 1, "label": "EL0 and EL1 execution of the CP15DMB, CP15DSB, and CP15ISB instructions is enabled."},
            ]),
            {"name": "RES1", "msb": 4, "lsb": 3, "description": "Reserved, RES1.", "values": [], "reserved": False, "rwtype": "RES1"},
            _f("C", 2, 2, "Cacheability control for data accesses at EL1 and EL0.", [
                {"val": 0, "label": "All data access to Normal memory from EL1 and EL0 are Non-cacheable."},
                {"val": 1, "label": "All data access to Normal memory from EL1 and EL0 can be cached at all levels."},
            ]),
            _f("A", 1, 1, "Alignment check enable. Enable bit for Alignment fault checking at EL1 and EL0.", [
                {"val": 0, "label": "Alignment fault checking disabled when executing at EL1 or EL0."},
                {"val": 1, "label": "Alignment fault checking enabled when executing at EL1 or EL0."},
            ]),
            _f("M", 0, 0, "MPU enable for the EL1 MPU.", [
                {"val": 0, "label": "EL1 MPU disabled."},
                {"val": 1, "label": "EL1 MPU enabled."},
            ]),
        ],
    },
]

# Build lookup: name -> redefined data
REDEFINED_MAP = {r["name"]: r for r in REDEFINED_REGISTERS}


NEW_REGISTERS = [
    {
        "name": "HMPUIR",
        "long_name": "Hypervisor MPU Type Register",
        "description": "Identifies the number of regions supported by the EL2 MPU.",
        "state": "AArch32",
        "arm_url": "https://developer.arm.com/documentation/ddi0568/latest",
        "fields": [
            _res0(31, 8),
            {"name": "REGION", "msb": 7, "lsb": 0,
             "description": "The number of EL2 MPU regions implemented.",
             "values": [], "reserved": False, "rwtype": None},
        ],
    },
    {
        "name": "HPRBAR",
        "long_name": "Hypervisor Protection Region Base Address Register",
        "description": (
            "Provides indirect access to the base address of the EL2 MPU region "
            "currently defined by HPRSELR."
        ),
        "state": "AArch32",
        "arm_url": "https://developer.arm.com/documentation/ddi0568/latest",
        "fields": [
            {"name": "BASE", "msb": 31, "lsb": 6,
             "description": (
                 "Address[31:6] concatenated with zeroes to form Address[31:0], "
                 "the lower inclusive limit used as the base address for the selected memory region."
             ),
             "values": [], "reserved": False, "rwtype": None},
            _res0(5, 5),
            {"name": "SH[1:0]", "msb": 4, "lsb": 3,
             "description": "Shareability attribute.",
             "values": [
                 {"val": 0, "label": "Non-shareable"},
                 {"val": 2, "label": "Outer Shareable"},
                 {"val": 3, "label": "Inner Shareable"},
             ],
             "reserved": False, "rwtype": None},
            {"name": "AP[2:1]", "msb": 2, "lsb": 1,
             "description": "Access permissions attribute for stage 2 (EL2 MPU regions).",
             "values": [
                 {"val": 1, "label": "Read/write at EL2, EL1 and EL0"},
                 {"val": 2, "label": "Read-only at EL2, no access at EL1 or EL0"},
                 {"val": 3, "label": "Read-only at EL2, EL1 and EL0"},
             ],
             "reserved": False, "rwtype": None},
            {"name": "XN", "msb": 0, "lsb": 0,
             "description": "Execute-never.",
             "values": [], "reserved": False, "rwtype": None},
        ],
    },
    {
        "name": "HPRBAR<n>",
        "long_name": "Hypervisor Protection Region Base Address Registers, n = 0 - 31",
        "description": (
            "Provides direct access to the base addresses for the first 32 defined EL2 MPU regions."
        ),
        "state": "AArch32",
        "arm_url": "https://developer.arm.com/documentation/ddi0568/latest",
        "fields": [
            {"name": "BASE", "msb": 31, "lsb": 6,
             "description": (
                 "Address[31:6] concatenated with zeroes to form Address[31:0], "
                 "the lower inclusive limit used as the base address for the selected memory region."
             ),
             "values": [], "reserved": False, "rwtype": None},
            _res0(5, 5),
            {"name": "SH[1:0]", "msb": 4, "lsb": 3,
             "description": "Shareability attribute.",
             "values": [
                 {"val": 0, "label": "Non-shareable"},
                 {"val": 2, "label": "Outer Shareable"},
                 {"val": 3, "label": "Inner Shareable"},
             ],
             "reserved": False, "rwtype": None},
            {"name": "AP[2:1]", "msb": 2, "lsb": 1,
             "description": "Access permissions attribute for stage 2 (EL2 MPU regions).",
             "values": [
                 {"val": 1, "label": "Read/write at EL2, EL1 and EL0"},
                 {"val": 2, "label": "Read-only at EL2, no access at EL1 or EL0"},
                 {"val": 3, "label": "Read-only at EL2, EL1 and EL0"},
             ],
             "reserved": False, "rwtype": None},
            {"name": "XN", "msb": 0, "lsb": 0,
             "description": "Execute-never.",
             "values": [], "reserved": False, "rwtype": None},
        ],
    },
    {
        "name": "HPRENR",
        "long_name": "Hypervisor Protection Region Enable Register",
        "description": (
            "Provides direct access to the HPRLAR.EN bits for EL2 MPU regions 0 to 31."
        ),
        "state": "AArch32",
        "arm_url": "https://developer.arm.com/documentation/ddi0568/latest",
        "fields": [
            {"name": "ENABLE_bits", "msb": 31, "lsb": 0,
             "description": (
                 "An alias of the HPRLAR[31:0].EN bits. "
                 "Bits associated with unimplemented regions are RAZ/WI."
             ),
             "values": [], "reserved": False, "rwtype": None},
        ],
    },
    {
        "name": "HPRLAR",
        "long_name": "Hypervisor Protection Region Limit Address Register",
        "description": (
            "Provides indirect access to the limit address of the EL2 MPU region "
            "currently defined by HPRSELR."
        ),
        "state": "AArch32",
        "arm_url": "https://developer.arm.com/documentation/ddi0568/latest",
        "fields": [
            {"name": "LIMIT", "msb": 31, "lsb": 6,
             "description": (
                 "Address[31:6] concatenated with the value 0x3F to form Address[31:0], "
                 "the upper inclusive limit address for the selected memory region."
             ),
             "values": [], "reserved": False, "rwtype": None},
            _res0(5, 4),
            {"name": "AttrIndx[2:0]", "msb": 3, "lsb": 1,
             "description": "Selects memory attributes from HMAIR0 or HMAIR1.",
             "values": [
                 {"val": 0, "label": "Attr0 from HMAIR0"},
                 {"val": 1, "label": "Attr1 from HMAIR0"},
                 {"val": 2, "label": "Attr2 from HMAIR0"},
                 {"val": 3, "label": "Attr3 from HMAIR0"},
                 {"val": 4, "label": "Attr4 from HMAIR1"},
                 {"val": 5, "label": "Attr5 from HMAIR1"},
                 {"val": 6, "label": "Attr6 from HMAIR1"},
                 {"val": 7, "label": "Attr7 from HMAIR1"},
             ],
             "reserved": False, "rwtype": None},
            {"name": "EN", "msb": 0, "lsb": 0,
             "description": "Region enable.",
             "values": [
                 {"val": 0, "label": "Region disabled"},
                 {"val": 1, "label": "Region enabled"},
             ],
             "reserved": False, "rwtype": None},
        ],
    },
    {
        "name": "HPRLAR<n>",
        "long_name": "Hypervisor Protection Region Limit Address Registers, n = 0 - 31",
        "description": (
            "Provides direct access to the limit addresses for the first 32 defined EL2 MPU regions."
        ),
        "state": "AArch32",
        "arm_url": "https://developer.arm.com/documentation/ddi0568/latest",
        "fields": [
            {"name": "LIMIT", "msb": 31, "lsb": 6,
             "description": (
                 "Address[31:6] concatenated with the value 0x3F to form Address[31:0], "
                 "the upper inclusive limit address for the selected memory region."
             ),
             "values": [], "reserved": False, "rwtype": None},
            _res0(5, 4),
            {"name": "AttrIndx[2:0]", "msb": 3, "lsb": 1,
             "description": "Selects memory attributes from HMAIR0 or HMAIR1.",
             "values": [
                 {"val": 0, "label": "Attr0 from HMAIR0"},
                 {"val": 1, "label": "Attr1 from HMAIR0"},
                 {"val": 2, "label": "Attr2 from HMAIR0"},
                 {"val": 3, "label": "Attr3 from HMAIR0"},
                 {"val": 4, "label": "Attr4 from HMAIR1"},
                 {"val": 5, "label": "Attr5 from HMAIR1"},
                 {"val": 6, "label": "Attr6 from HMAIR1"},
                 {"val": 7, "label": "Attr7 from HMAIR1"},
             ],
             "reserved": False, "rwtype": None},
            {"name": "EN", "msb": 0, "lsb": 0,
             "description": "Region enable.",
             "values": [
                 {"val": 0, "label": "Region disabled"},
                 {"val": 1, "label": "Region enabled"},
             ],
             "reserved": False, "rwtype": None},
        ],
    },
    {
        "name": "HPRSELR",
        "long_name": "Hypervisor Protection Region Selector Register",
        "description": (
            "Selects the region number for the EL2 MPU region associated with the "
            "HPRBAR and HPRLAR registers."
        ),
        "state": "AArch32",
        "arm_url": "https://developer.arm.com/documentation/ddi0568/latest",
        "fields": [
            _res0(31, 8),
            {"name": "REGION", "msb": 7, "lsb": 0,
             "description": (
                 "The region number. Writing a value greater than or equal to the number "
                 "of implemented regions is UNPREDICTABLE."
             ),
             "values": [], "reserved": False, "rwtype": None},
        ],
    },
    {
        "name": "MPUIR",
        "long_name": "MPU Type Register",
        "description": "Identifies the number of regions supported by the EL1 MPU.",
        "state": "AArch32",
        "arm_url": "https://developer.arm.com/documentation/ddi0568/latest",
        "fields": [
            _res0(31, 16),
            {"name": "REGION", "msb": 15, "lsb": 8,
             "description": "The number of EL1 MPU regions implemented. An EL1 MPU region controls EL1 and EL0 access.",
             "values": [], "reserved": False, "rwtype": None},
            _res0(7, 0),
        ],
    },
    {
        "name": "PRBAR",
        "long_name": "Protection Region Base Address Register",
        "description": (
            "Provides indirect access to the base address of the EL1 MPU region "
            "currently defined by PRSELR."
        ),
        "state": "AArch32",
        "arm_url": "https://developer.arm.com/documentation/ddi0568/latest",
        "fields": [
            {"name": "BASE", "msb": 31, "lsb": 6,
             "description": (
                 "Address[31:6] concatenated with zeroes to form Address[31:0], "
                 "the lower inclusive limit used as the base address for the selected memory region."
             ),
             "values": [], "reserved": False, "rwtype": None},
            _res0(5, 5),
            {"name": "SH[1:0]", "msb": 4, "lsb": 3,
             "description": "Shareability attribute.",
             "values": [
                 {"val": 0, "label": "Non-shareable"},
                 {"val": 2, "label": "Outer Shareable"},
                 {"val": 3, "label": "Inner Shareable"},
             ],
             "reserved": False, "rwtype": None},
            {"name": "AP[2:1]", "msb": 2, "lsb": 1,
             "description": "Access permissions attribute.",
             "values": [
                 {"val": 0, "label": "Read/write at EL1, no access at EL0"},
                 {"val": 1, "label": "Read/write at EL1 or EL0"},
                 {"val": 2, "label": "Read-only at EL1, no access at EL0"},
                 {"val": 3, "label": "Read-only at EL1 and EL0"},
             ],
             "reserved": False, "rwtype": None},
            {"name": "XN", "msb": 0, "lsb": 0,
             "description": "Execute-never.",
             "values": [], "reserved": False, "rwtype": None},
        ],
    },
    {
        "name": "PRBAR<n>",
        "long_name": "Protection Region Base Address Registers, n = 0 - 31",
        "description": (
            "Provides direct access to the base addresses for the first 32 defined EL1 MPU regions."
        ),
        "state": "AArch32",
        "arm_url": "https://developer.arm.com/documentation/ddi0568/latest",
        "fields": [
            {"name": "BASE", "msb": 31, "lsb": 6,
             "description": (
                 "Address[31:6] concatenated with zeroes to form Address[31:0], "
                 "the lower inclusive limit used as the base address for the selected memory region."
             ),
             "values": [], "reserved": False, "rwtype": None},
            _res0(5, 5),
            {"name": "SH[1:0]", "msb": 4, "lsb": 3,
             "description": "Shareability attribute.",
             "values": [
                 {"val": 0, "label": "Non-shareable"},
                 {"val": 2, "label": "Outer Shareable"},
                 {"val": 3, "label": "Inner Shareable"},
             ],
             "reserved": False, "rwtype": None},
            {"name": "AP[2:1]", "msb": 2, "lsb": 1,
             "description": "Access permissions attribute.",
             "values": [
                 {"val": 0, "label": "Read/write at EL1, no access at EL0"},
                 {"val": 1, "label": "Read/write at EL1 or EL0"},
                 {"val": 2, "label": "Read-only at EL1, no access at EL0"},
                 {"val": 3, "label": "Read-only at EL1 and EL0"},
             ],
             "reserved": False, "rwtype": None},
            {"name": "XN", "msb": 0, "lsb": 0,
             "description": "Execute-never.",
             "values": [], "reserved": False, "rwtype": None},
        ],
    },
    {
        "name": "PRLAR",
        "long_name": "Protection Region Limit Address Register",
        "description": (
            "Provides indirect access to the limit address of the EL1 MPU region "
            "currently defined by PRSELR."
        ),
        "state": "AArch32",
        "arm_url": "https://developer.arm.com/documentation/ddi0568/latest",
        "fields": [
            {"name": "LIMIT", "msb": 31, "lsb": 6,
             "description": (
                 "Address[31:6] concatenated with the value 0x3F to form Address[31:0], "
                 "the upper inclusive limit address for the selected memory region."
             ),
             "values": [], "reserved": False, "rwtype": None},
            _res0(5, 4),
            {"name": "AttrIndx[2:0]", "msb": 3, "lsb": 1,
             "description": "Selects memory attributes from MAIR0 or MAIR1.",
             "values": [
                 {"val": 0, "label": "Attr0 from MAIR0"},
                 {"val": 1, "label": "Attr1 from MAIR0"},
                 {"val": 2, "label": "Attr2 from MAIR0"},
                 {"val": 3, "label": "Attr3 from MAIR0"},
                 {"val": 4, "label": "Attr4 from MAIR1"},
                 {"val": 5, "label": "Attr5 from MAIR1"},
                 {"val": 6, "label": "Attr6 from MAIR1"},
                 {"val": 7, "label": "Attr7 from MAIR1"},
             ],
             "reserved": False, "rwtype": None},
            {"name": "EN", "msb": 0, "lsb": 0,
             "description": "Region enable.",
             "values": [
                 {"val": 0, "label": "Region disabled"},
                 {"val": 1, "label": "Region enabled"},
             ],
             "reserved": False, "rwtype": None},
        ],
    },
    {
        "name": "PRLAR<n>",
        "long_name": "Protection Region Limit Address Registers, n = 0 - 31",
        "description": (
            "Provides direct access to the limit addresses for the first 32 defined EL1 MPU regions."
        ),
        "state": "AArch32",
        "arm_url": "https://developer.arm.com/documentation/ddi0568/latest",
        "fields": [
            {"name": "LIMIT", "msb": 31, "lsb": 6,
             "description": (
                 "Address[31:6] concatenated with the value 0x3F to form Address[31:0], "
                 "the upper inclusive limit address for the selected memory region."
             ),
             "values": [], "reserved": False, "rwtype": None},
            _res0(5, 4),
            {"name": "AttrIndx[2:0]", "msb": 3, "lsb": 1,
             "description": "Selects memory attributes from MAIR0 or MAIR1.",
             "values": [
                 {"val": 0, "label": "Attr0 from MAIR0"},
                 {"val": 1, "label": "Attr1 from MAIR0"},
                 {"val": 2, "label": "Attr2 from MAIR0"},
                 {"val": 3, "label": "Attr3 from MAIR0"},
                 {"val": 4, "label": "Attr4 from MAIR1"},
                 {"val": 5, "label": "Attr5 from MAIR1"},
                 {"val": 6, "label": "Attr6 from MAIR1"},
                 {"val": 7, "label": "Attr7 from MAIR1"},
             ],
             "reserved": False, "rwtype": None},
            {"name": "EN", "msb": 0, "lsb": 0,
             "description": "Region enable.",
             "values": [
                 {"val": 0, "label": "Region disabled"},
                 {"val": 1, "label": "Region enabled"},
             ],
             "reserved": False, "rwtype": None},
        ],
    },
    {
        "name": "PRSELR",
        "long_name": "Protection Region Selector Register",
        "description": (
            "Selects the region number for the EL1 MPU region associated with the "
            "PRBAR and PRLAR registers."
        ),
        "state": "AArch32",
        "arm_url": "https://developer.arm.com/documentation/ddi0568/latest",
        "fields": [
            _res0(31, 8),
            {"name": "REGION", "msb": 7, "lsb": 0,
             "description": (
                 "The region number. Writing a value greater than or equal to the number "
                 "of implemented regions is UNPREDICTABLE."
             ),
             "values": [], "reserved": False, "rwtype": None},
        ],
    },
    {
        "name": "VSCTLR",
        "long_name": "Virtualization System Control Register",
        "description": (
            "Provides control and configuration information for PMSA virtualization."
        ),
        "state": "AArch32",
        "arm_url": "https://developer.arm.com/documentation/ddi0568/latest",
        "fields": [
            _res0(31, 24),
            {"name": "VMID", "msb": 23, "lsb": 16,
             "description": "Virtual machine identifier.",
             "values": [], "reserved": False, "rwtype": None},
            _res0(15, 3),
            {"name": "S2NIE", "msb": 2, "lsb": 2,
             "description": (
                 "Stage 2 Normal Interrupt Enable. "
                 "When 1, multi-word accesses are interruptible at EL1/EL0 for memory "
                 "marked Normal in the EL2 MPU region (only effective when HSCTLR.FI==1)."
             ),
             "values": [
                 {"val": 0, "label": "Feature disabled"},
                 {"val": 1, "label": "Feature enabled"},
             ],
             "reserved": False, "rwtype": None},
            {"name": "S2DMAD", "msb": 1, "lsb": 1,
             "description": (
                 "Stage 2 Device Multiword Access Disable. "
                 "When 1, multi-word accesses at EL1/EL0 that span an aligned 64-bit boundary "
                 "generate a stage 2 Permission Fault if the memory region is Device in the EL2 MPU."
             ),
             "values": [
                 {"val": 0, "label": "Feature disabled"},
                 {"val": 1, "label": "Feature enabled"},
             ],
             "reserved": False, "rwtype": None},
            _res0(0, 0),
        ],
    },
]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default="data/registers.json",
                        help="Path to the A-profile registers.json (default: data/registers.json)")
    parser.add_argument("--out", default="data/registers_r_profile.json",
                        help="Output path (default: data/registers_r_profile.json)")
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"ERROR: {input_path} not found.", file=sys.stderr)
        sys.exit(1)

    with open(input_path) as f:
        a_profile = json.load(f)

    # Build lookup: name -> register entry (AArch32 only from A-profile)
    a_profile_map = {}
    for reg in a_profile:
        if reg.get("state") == "AArch32":
            a_profile_map[reg["name"]] = reg

    result = []
    covered = set()

    # 1. Include A-profile AArch32 registers that appear in R_PROFILE_STATUS
    for reg in a_profile:
        if reg.get("state") != "AArch32":
            continue
        name = reg["name"]
        status = R_PROFILE_STATUS.get(name)
        if status == "Unchanged":
            entry = dict(reg)
            entry["r_profile_status"] = "Unchanged"
            result.append(entry)
            covered.add(name)
        elif status == "Redefined":
            entry = dict(reg)
            entry["r_profile_status"] = "Redefined"
            if name in REDEFINED_MAP:
                rd = REDEFINED_MAP[name]
                entry["description"] = rd["description"]
                entry["fields"] = rd["fields"]
                entry["arm_url"] = DDI0568_URL
                # Remove any stale A-profile note
                entry.pop("r_profile_note", None)
            else:
                # FPSCR: access-only redefinition, no field changes
                entry["r_profile_note"] = (
                    "This register is redefined in Armv8-R (access only). "
                    "Field definitions shown here are from the Armv8-A profile; "
                    "consult ARM DDI 0568 for R-profile-specific access restrictions."
                )
            result.append(entry)
            covered.add(name)

    # 2. Inject New registers (R-profile only, from DDI0568 E2.2)
    for reg in NEW_REGISTERS:
        entry = dict(reg)
        entry["r_profile_status"] = "New"
        result.append(entry)
        covered.add(reg["name"])

    # 3. Report any R_PROFILE_STATUS entries not found in source data
    missing = [n for n, s in R_PROFILE_STATUS.items()
               if n not in covered and s in ("Unchanged", "Redefined")]
    if missing:
        print(f"WARNING: {len(missing)} register(s) listed in R-profile table "
              f"not found in A-profile data: {missing}", file=sys.stderr)

    # Sort: Unchanged first, then Redefined, then New; alphabetically within each group
    order = {"Unchanged": 0, "Redefined": 1, "New": 2}
    result.sort(key=lambda r: (order.get(r.get("r_profile_status", ""), 99), r["name"]))

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(result, f, indent=2)

    unchanged = sum(1 for r in result if r.get("r_profile_status") == "Unchanged")
    redefined = sum(1 for r in result if r.get("r_profile_status") == "Redefined")
    new       = sum(1 for r in result if r.get("r_profile_status") == "New")
    print(f"Written {len(result)} registers to {out_path}")
    print(f"  Unchanged: {unchanged}  Redefined: {redefined}  New: {new}")


if __name__ == "__main__":
    main()
