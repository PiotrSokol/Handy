This document maps the Python accessibility code in `/Users/piotr/util/Handy/py-api/test2.py` to Rust crates:
- [`eiz/accessibility`](https://github.com/eiz/accessibility)
- [`yury/cidre`](https://github.com/yury/cidre)
- [`madsmtm/objc2`](https://github.com/madsmtm/objc2)

---

## 1. Focus Discovery

**Python**
- Uses `AXUIElementCreateSystemWide` → `kAXFocusedUIElementAttribute`.
- Refs: `test2.py:L127–L136`.

**Rust**
- Crates: `accessibility` / `accessibility-sys`.
- Functions: `AXUIElementCreateSystemWide`, `AXUIElementCopyAttributeValue`.
- Constants: `kAXFocusedUIElementAttribute`.
- CF handling: via `cidre` or `core-foundation`.

---

## 2. Role Checking

**Python**
- Reads `kAXRoleAttribute` to determine if element is text-like.
- Refs: `test2.py:L137–L150`.

**Rust**
- Use `AXUIElementCopyAttributeValue` + `kAXRoleAttribute`.
- Result: CFString → compare against `"AXTextField"`, `"AXTextView"`, etc.
- Wrap with `CFString` from `core-foundation`/`cidre`.

---

## 3. Insertion Path A — Setting Value

**Python**
- `AXUIElementIsAttributeSettable(kAXValueAttribute)`, then `AXUIElementSetAttributeValue`.
- Refs: `test2.py:L151–L190`, `L211–L240`.

**Rust**
- Crates: `accessibility-sys`.
- Functions: `AXUIElementIsAttributeSettable`, `AXUIElementSetAttributeValue`.
- Constants: `kAXValueAttribute`.
- CF strings with `core-foundation`/`cidre`.

---

## 4. Insertion Path B — Actions

**Python**
- Enumerates `AXUIElementCopyActionNames`, uses `AXUIElementPerformAction`.
- Refs: `test2.py:L211–L240`.

**Rust**
- Crates: `accessibility-sys`.
- Functions: `AXUIElementCopyActionNames`, `AXUIElementPerformAction`.
- CFArray<CFString> → Rust vector.

---

## 5. Insertion Path C — Synthetic Keystrokes

**Python**
- Gets PID with `AXUIElementGetPid`, builds app element, calls `AXUIElementPostKeyboardEvent`.
- Refs: `test2.py:L191–L210`.

**Rust**
- Crates: `accessibility-sys`.
- Functions: `AXUIElementGetPid`, `AXUIElementCreateApplication`, `AXUIElementPostKeyboardEvent`.

---

## 6. Selection & Context Inspection

**Python**
- Selected text: `kAXSelectedTextAttribute`.
- Selected range: `kAXSelectedTextRangeAttribute` with `AXValueGetValue`.
- Number of chars: `kAXNumberOfCharactersAttribute`.
- String for range: `kAXStringForRangeParameterizedAttribute`.
- Refs: `test2.py:L241–L342`.

**Rust**
- Crates: `accessibility-sys`.
- Functions: `AXUIElementCopyAttributeValue`, `AXUIElementCopyParameterizedAttributeValue`.
- Handle `CFRange` via `AXValueCreate`/`AXValueGetValue`.

---

## 7. Permissions & Errors

**Python**
- `_ax_ok()` checks `kAXErrorSuccess`.
- Refs: `test2.py:L77–L126`.

**Rust**
- Function: `AXIsProcessTrustedWithOptions`.
- Guard calls by checking error codes.

---

## 8. Hotkey Binding

**Python**
- Global hotkey via `pynput`.
- Refs: `test2.py:L343–L372`.

**Rust**
- Out of scope for AX crates.
- Use CGEvent taps (`cidre`/`core-graphics`) or cross-platform hotkey crates.

---

## 9. Interop Building Blocks

- **CF types**: Use `cidre` or `core-foundation`.
- **ObjC messaging**: `objc2` if extending into AppKit/Foundation.

---

## Suggested Rust Module Structure

1. `ax::focus`
    - `system_wide()`, `focused_element()`.
2. `ax::role`
    - `role(&AXUIElement)`, `is_text_like`.
3. `ax::insert`
    - `can_set_value`, `get_value`, `set_value`.
    - `actions`, `perform_action`.
    - `post_keystrokes`.
4. `ax::selection`
    - `selected_text`, `selected_range`, `num_chars`, `string_for_range`.
5. `bootstrap`
    - `ensure_accessibility_trusted()`.

---

## Notes

- Some apps only accept whole-value sets, so append logic must re-read the value.
- Parameterized attributes need careful `CFRange` marshalling.
- Synthetic key events are least reliable.

---