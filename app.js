"use strict";

// ── State ───────────────────────────────────────────────────────────────────

let registers = [];         // Full register list from JSON
let nameIndex = {};         // name.toUpperCase() -> register object
let currentReg = null;      // Currently selected register
let selectedIdx = -1;       // Highlighted index in autocomplete dropdown

// ── DOM refs ────────────────────────────────────────────────────────────────

const profileSelect = document.getElementById("profile-select");
const subtitle      = document.getElementById("subtitle");
const regInput      = document.getElementById("reg-input");
const dropdown      = document.getElementById("reg-dropdown");
const valInput      = document.getElementById("val-input");
const regInfo       = document.getElementById("reg-info");
const regTitle      = document.getElementById("reg-title");
const regBadge      = document.getElementById("reg-state-badge");
const regDesc       = document.getElementById("reg-desc");
const regLink       = document.getElementById("reg-link");
const rProfileNote        = document.getElementById("r-profile-note");
const rProfileDisclaimer  = document.getElementById("r-profile-disclaimer");
const fieldsBody    = document.getElementById("fields-body");
const loadingMsg    = document.getElementById("loading-msg");
const noDataMsg     = document.getElementById("no-data-msg");

// ── Profile config ───────────────────────────────────────────────────────────

const PROFILES = {
  "a-profile": {
    label: "A-Profile System Register Reference",
    url: "data/registers.json",
  },
  "r-profile": {
    label: "R-Profile System Register Reference",
    url: "data/registers_r_profile.json",
  },
};

// ── Load data ────────────────────────────────────────────────────────────────

function loadProfile(profileKey) {
  const profile = PROFILES[profileKey];
  if (!profile) return;

  subtitle.textContent = profile.label;
  rProfileDisclaimer.hidden = (profileKey !== "r-profile");
  regInput.disabled = true;
  valInput.disabled = true;
  regInfo.hidden = true;
  noDataMsg.hidden = true;
  loadingMsg.hidden = false;
  regInput.value = "";
  currentReg = null;
  hideDropdown();

  fetch(profile.url)
    .then(r => {
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      return r.json();
    })
    .then(data => {
      registers = data;
      nameIndex = {};
      for (const reg of registers) {
        nameIndex[reg.name.toUpperCase()] = reg;
      }
      console.log(`[ASRF] Loaded ${registers.length} registers (${profileKey})`);
      loadingMsg.hidden = true;
      regInput.disabled = false;
      valInput.disabled = false;
      regInput.focus();
    })
    .catch(err => {
      console.error(`[ASRF] Failed to load ${profile.url}:`, err);
      loadingMsg.hidden = true;
      noDataMsg.hidden = false;
    });
}

profileSelect.addEventListener("change", () => {
  loadProfile(profileSelect.value);
});

loadProfile(profileSelect.value);

// ── Autocomplete ─────────────────────────────────────────────────────────────

function showSuggestions(query) {
  const q = query.trim().toUpperCase();
  if (!q) {
    hideDropdown();
    return;
  }

  // Prefer prefix matches first, then substring matches
  const prefix = registers.filter(r => r.name.toUpperCase().startsWith(q));
  const substr = registers.filter(
    r => !r.name.toUpperCase().startsWith(q) && r.name.toUpperCase().includes(q)
  );
  const matches = [...prefix, ...substr].slice(0, 12);

  if (matches.length === 0) {
    hideDropdown();
    return;
  }

  dropdown.innerHTML = "";
  selectedIdx = -1;
  for (const reg of matches) {
    const li = document.createElement("li");
    li.setAttribute("role", "option");
    li.setAttribute("aria-selected", "false");
    li.dataset.name = reg.name;

    const nameSpan = document.createElement("span");
    nameSpan.textContent = reg.name;

    const longSpan = document.createElement("span");
    longSpan.className = "long-name";
    const stateLabel = { AArch64: "AArch64", AArch32: "AArch32", ext: "Ext" };
    const stateTag = reg.state ? `[${stateLabel[reg.state] || reg.state}]` : "";
    const rTag = reg.r_profile_status && reg.r_profile_status !== "Unchanged"
      ? `[${reg.r_profile_status}]` : "";
    longSpan.textContent = [stateTag, rTag, reg.long_name].filter(Boolean).join(" ");

    li.appendChild(nameSpan);
    if (longSpan.textContent) li.appendChild(longSpan);

    li.addEventListener("mousedown", e => {
      e.preventDefault(); // keep focus on input
      selectRegister(reg.name);
    });

    dropdown.appendChild(li);
  }

  dropdown.hidden = false;
}

function hideDropdown() {
  dropdown.hidden = true;
  selectedIdx = -1;
}

function moveSuggestion(dir) {
  const items = dropdown.querySelectorAll("li");
  if (!items.length) return;
  if (selectedIdx >= 0) items[selectedIdx].setAttribute("aria-selected", "false");
  selectedIdx = (selectedIdx + dir + items.length) % items.length;
  items[selectedIdx].setAttribute("aria-selected", "true");
  items[selectedIdx].scrollIntoView({ block: "nearest" });
}

regInput.addEventListener("input", () => {
  showSuggestions(regInput.value);
});

regInput.addEventListener("keydown", e => {
  if (e.key === "ArrowDown") { e.preventDefault(); if (!dropdown.hidden) moveSuggestion(1); }
  else if (e.key === "ArrowUp") { e.preventDefault(); if (!dropdown.hidden) moveSuggestion(-1); }
  else if (e.key === "Enter") {
    e.preventDefault();
    if (!dropdown.hidden && selectedIdx >= 0) {
      const item = dropdown.querySelectorAll("li")[selectedIdx];
      if (item) selectRegister(item.dataset.name);
    } else {
      // Try exact match regardless of dropdown state
      const exact = nameIndex[regInput.value.trim().toUpperCase()];
      if (exact) selectRegister(exact.name);
    }
  } else if (e.key === "Escape") {
    hideDropdown();
  }
});

regInput.addEventListener("blur", () => {
  // Small delay so mousedown on a suggestion can fire first
  setTimeout(() => {
    hideDropdown();
    // Auto-select if the typed name is an exact match and no register selected yet
    const typed = regInput.value.trim().toUpperCase();
    if (typed && (!currentReg || currentReg.name.toUpperCase() !== typed)) {
      const exact = nameIndex[typed];
      if (exact) selectRegister(exact.name);
    }
  }, 150);
});

// ── Register selection ────────────────────────────────────────────────────────

function selectRegister(name) {
  const reg = nameIndex[name.toUpperCase()];
  console.log(`[ASRF] selectRegister("${name}") →`, reg ? `found, fields=${reg.fields.length}` : "NOT FOUND");
  if (!reg) return;

  currentReg = reg;
  regInput.value = reg.name;
  hideDropdown();

  // Header
  regTitle.textContent = reg.long_name ? `${reg.name}  —  ${reg.long_name}` : reg.name;

  const stateLabel = { AArch64: "AArch64", AArch32: "AArch32", ext: "External" };
  const stateClass = { AArch64: "aarch64", AArch32: "aarch32", ext: "ext" };
  const rClass = { Unchanged: "r-unchanged", Redefined: "r-redefined", New: "r-new" };

  let badgeText = stateLabel[reg.state] || reg.state || "";
  let badgeClass = "state-badge " + (stateClass[reg.state] || "");
  if (reg.r_profile_status) {
    badgeText += (badgeText ? "  ·  " : "") + reg.r_profile_status;
    badgeClass += " " + (rClass[reg.r_profile_status] || "");
  }
  regBadge.textContent = badgeText;
  regBadge.className = badgeClass;
  regBadge.hidden = !badgeText;

  regDesc.textContent = reg.description || "";
  regDesc.hidden = !reg.description;

  if (reg.r_profile_note) {
    rProfileNote.textContent = reg.r_profile_note;
    rProfileNote.hidden = false;
  } else {
    rProfileNote.hidden = true;
  }

  regLink.href = reg.arm_url;
  regInfo.hidden = false;

  decodeAndRender();
}

// ── Value parsing ─────────────────────────────────────────────────────────────

function parseValue(str) {
  const s = str.trim().replace(/[\s_]/g, "");
  if (!s) return null;
  let result = null;
  try {
    if (s.startsWith("0x") || s.startsWith("0X")) result = BigInt(s);
    else if (/^[0-9]+$/.test(s)) result = BigInt(s);
    // Bare hex without 0x prefix (e.g. "DEADBEEF", "ff00")
    else if (/^[0-9a-fA-F]+$/.test(s)) result = BigInt("0x" + s);
  } catch (e) {
    console.warn("[ASRF] parseValue error:", e.message);
  }
  console.log(`[ASRF] parseValue("${str}") →`, result);
  return result;
}

// ── Bit extraction ────────────────────────────────────────────────────────────

function extractBits(value, msb, lsb) {
  const width = BigInt(msb - lsb + 1);
  const mask = (1n << width) - 1n;
  return (value >> BigInt(lsb)) & mask;
}

function fmtHex(val, width) {
  const nibbles = Math.max(1, Math.ceil(width / 4));
  return "0x" + val.toString(16).toUpperCase().padStart(nibbles, "0");
}

function fmtBin(val, width) {
  return val.toString(2).padStart(width, "0");
}

// ── Render ────────────────────────────────────────────────────────────────────

function decodeAndRender() {
  if (!currentReg) {
    console.log("[ASRF] decodeAndRender: no register selected, skipping");
    return;
  }

  const rawValue = valInput.value;
  const value = rawValue.trim() ? parseValue(rawValue) : null;
  console.log(`[ASRF] decodeAndRender: reg=${currentReg.name}, fields=${currentReg.fields.length}, value=${value}`);

  fieldsBody.innerHTML = "";

  for (const field of currentReg.fields) {
    const tr = document.createElement("tr");
    const width = field.msb - field.lsb + 1;

    if (field.reserved) tr.classList.add("is-reserved");

    // Bits column
    const tdBits = document.createElement("td");
    tdBits.className = "bits";
    tdBits.textContent = field.msb === field.lsb ? String(field.msb) : `${field.msb}:${field.lsb}`;
    tr.appendChild(tdBits);

    // Field name column
    const tdName = document.createElement("td");
    tdName.className = "field-name";
    if (field.rwtype && field.reserved) {
      tdName.innerHTML = `<span title="${field.rwtype}">${field.name}</span>`;
    } else {
      tdName.textContent = field.name;
    }
    tr.appendChild(tdName);

    // Value column
    const tdVal = document.createElement("td");
    tdVal.className = "field-val";
    if (value !== null) {
      const bits = extractBits(value, field.msb, field.lsb);
      const hexSpan = document.createElement("span");
      hexSpan.className = "hex";
      hexSpan.textContent = width <= 4 ? bits.toString(10) : fmtHex(bits, width);
      const binSpan = document.createElement("span");
      binSpan.className = "bin";
      binSpan.textContent = width > 1 ? ` (${fmtBin(bits, width)})` : "";
      tdVal.appendChild(hexSpan);
      if (width > 1) tdVal.appendChild(binSpan);
    } else {
      tdVal.textContent = "—";
    }
    tr.appendChild(tdVal);

    // Meaning column
    const tdMeaning = document.createElement("td");
    tdMeaning.className = "meaning";

    if (value !== null && field.values && field.values.length > 0) {
      const bits = extractBits(value, field.msb, field.lsb);
      const match = field.values.find(v => v.val !== null && BigInt(v.val) === bits);
      if (match) {
        const enumSpan = document.createElement("span");
        enumSpan.className = "enum-match";
        enumSpan.textContent = match.label;
        tdMeaning.appendChild(enumSpan);
      } else if (field.description) {
        const descDiv = document.createElement("div");
        descDiv.className = "desc";
        descDiv.textContent = truncate(field.description, 120);
        tdMeaning.appendChild(descDiv);
      }
    } else if (field.description) {
      const descDiv = document.createElement("div");
      descDiv.className = "desc";
      descDiv.textContent = truncate(field.description, 120);
      tdMeaning.appendChild(descDiv);
    }

    tr.appendChild(tdMeaning);
    fieldsBody.appendChild(tr);
  }
}

function truncate(str, maxLen) {
  if (!str || str.length <= maxLen) return str;
  return str.slice(0, maxLen).trimEnd() + "…";
}

// ── Value input ───────────────────────────────────────────────────────────────

valInput.addEventListener("input", () => {
  console.log(`[ASRF] valInput input event: "${valInput.value}", currentReg=${currentReg?.name ?? "null"}`);
  decodeAndRender();
});

// Pre-fill placeholder with zeros on focus if empty
valInput.addEventListener("focus", () => {
  if (!valInput.value && currentReg) {
    valInput.placeholder = "0x0000000000000000";
  }
});
