#!/usr/bin/env python3
# macOS only. Requires: pip install pyobjc-framework-Quartz pyobjc-framework-Accessibility

import sys
import time
from typing import Optional, Tuple

from Quartz import (
    # Trust / prompt for Accessibility
    AXIsProcessTrustedWithOptions, kAXTrustedCheckOptionPrompt,
    # AX objects & attributes
    AXUIElementCreateSystemWide, AXUIElementCopyAttributeValue, AXUIElementSetAttributeValue,
    AXUIElementCopyParameterizedAttributeValue, AXValueCreate, AXValueGetValue,
    kAXFocusedUIElementAttribute, kAXRoleAttribute, kAXValueAttribute,
    kAXSelectedTextAttribute, kAXSelectedTextRangeAttribute,
    kAXStringForRangeParameterizedAttribute, kAXNumberOfCharactersAttribute,
    kAXTextFieldRole, kAXTextAreaRole, kAXTextViewRole,
    kAXValueCFRangeType,
    # Global hotkey via event tap
    CGEventTapCreate, CGEventMaskBit, CGEventTapEnable,
    kCGHIDEventTap, kCGHeadInsertEventTap, kCGEventTapOptionDefault,
    CGEventGetIntegerValueField, CGEventGetFlags,
    kCGKeyboardEventKeycode, kCGEventKeyDown,
    kCGEventFlagMaskCommand, kCGEventFlagMaskAlternate,
    CFRunLoopGetCurrent, CFRunLoopAddSource, CFRunLoopRun, CFRunLoopStop,
    CFMachPortCreateRunLoopSource,
)

# ---------- Hotkey handling (⌘⌥T) ----------

def wait_for_cmd_opt_t() -> None:
    """Blocks until ⌘⌥T is pressed anywhere."""
    target_keycode = 17  # 'T' on US keyboards
    hit = {"ok": False}

    def callback(proxy, type_, event, refcon):
        if type_ == kCGEventKeyDown:
            keycode = CGEventGetIntegerValueField(event, kCGKeyboardEventKeycode)
            flags = CGEventGetFlags(event)
            if (keycode == target_keycode and
                (flags & kCGEventFlagMaskCommand) and
                (flags & kCGEventFlagMaskAlternate)):
                hit["ok"] = True
                CFRunLoopStop(CFRunLoopGetCurrent())
        return event

    tap = CGEventTapCreate(
        kCGHIDEventTap, kCGHeadInsertEventTap, kCGEventTapOptionDefault,
        CGEventMaskBit(kCGEventKeyDown), callback, None
    )
    if not tap:
        raise RuntimeError("Failed to create event tap (enable Input Monitoring?).")

    source = CFMachPortCreateRunLoopSource(None, tap, 0)
    CFRunLoopAddSource(CFRunLoopGetCurrent(), source, 0)
    CGEventTapEnable(tap, True)
    CFRunLoopRun()
    if not hit["ok"]:
        raise RuntimeError("Hotkey wait aborted.")

# ---------- AX helpers ----------

def ax_trusted_or_prompt() -> bool:
    """Prompt for Accessibility (first run) and return trust state."""
    # Pass a CFDictionary with kAXTrustedCheckOptionPrompt: True
    return bool(AXIsProcessTrustedWithOptions({kAXTrustedCheckOptionPrompt: True}))

def get_focused_element():
    syswide = AXUIElementCreateSystemWide()
    err, focused = AXUIElementCopyAttributeValue(syswide, kAXFocusedUIElementAttribute, None)
    if err != 0 or focused is None:
        raise RuntimeError("Could not get focused UI element (is a text field focused?).")
    return focused

def get_role(element) -> str:
    err, role = AXUIElementCopyAttributeValue(element, kAXRoleAttribute, None)
    if err != 0 or role is None:
        return ""
    return role

def is_text_input(role: str) -> bool:
    return role in (kAXTextFieldRole, kAXTextAreaRole, kAXTextViewRole)

def get_value(element) -> str:
    err, value = AXUIElementCopyAttributeValue(element, kAXValueAttribute, None)
    if err != 0:
        raise RuntimeError("Failed to read kAXValueAttribute")
    return value or ""

def set_value(element, text: str) -> None:
    # Directly sets the entire value (many apps allow this; secure fields won’t).
    err = AXUIElementSetAttributeValue(element, kAXValueAttribute, text)
    if err != 0:
        raise RuntimeError("Failed to set kAXValueAttribute")

def get_selected_text(element) -> str:
    err, sel_text = AXUIElementCopyAttributeValue(element, kAXSelectedTextAttribute, None)
    if err != 0:
        # Not all apps expose selected text directly
        return ""
    return sel_text or ""

def get_selected_range(element) -> Optional[Tuple[int, int]]:
    err, axval = AXUIElementCopyAttributeValue(element, kAXSelectedTextRangeAttribute, None)
    if err != 0 or axval is None:
        return None
    rng = (0, 0)
    ok = AXValueGetValue(axval, kAXValueCFRangeType, rng)
    # AXValueGetValue cannot write into an immutable tuple; use a list container:
    rng_holder = [0, 0]
    ok = AXValueGetValue(axval, kAXValueCFRangeType, rng_holder)
    if not ok:
        return None
    location, length = rng_holder
    return (location, length)

def set_selected_range(element, location: int, length: int) -> None:
    ax_range = AXValueCreate(kAXValueCFRangeType, (location, length))
    err = AXUIElementSetAttributeValue(element, kAXSelectedTextRangeAttribute, ax_range)
    if err != 0:
        raise RuntimeError("Failed to set kAXSelectedTextRangeAttribute")

def string_for_range(element, location: int, length: int) -> str:
    ax_range = AXValueCreate(kAXValueCFRangeType, (location, length))
    err, substr = AXUIElementCopyParameterizedAttributeValue(
        element, kAXStringForRangeParameterizedAttribute, ax_range, None
    )
    if err != 0:
        return ""
    return substr or ""

def number_of_characters(element) -> int:
    err, n = AXUIElementCopyAttributeValue(element, kAXNumberOfCharactersAttribute, None)
    if err != 0 or n is None:
        # Best effort; some fields may not expose it.
        return -1
    return int(n)

# ---------- The test routine ----------

def wait_and_test_ax_text_ops(insert_text_direct="<<DIRECT SET VALUE>>",
                              replace_selection_with="<<REPLACED SELECTION>>",
                              context_window=20):
    """
    After ⌘⌥T is pressed:
      1) Verify focused element is a text input.
      2) Insert text by direct value set (append).
      3) Replace selection (if any) with a marker.
      3b) If no selection, make a 0-length selection at end and insert replacement at caret.
      4) Report selected text, caret position, and surrounding text.
    Prints a concise report.
    """
    if not ax_trusted_or_prompt():
        print("This script needs Accessibility permission (prompt shown). Rerun after granting.")
        return

    print("Focus a text field / editor, then press ⌘⌥T...")
    wait_for_cmd_opt_t()

    el = get_focused_element()
    role = get_role(el)
    print(f"Focused role: {role!r}")
    if not is_text_input(role):
        print("Focused element is not a text input (AXTextField/AXTextArea/AXTextView). Aborting.")
        return

    # Read current value & selection
    value0 = get_value(el)
    sel_text0 = get_selected_text(el)
    sel_rng0 = get_selected_range(el)  # (loc, len) or None
    n0 = number_of_characters(el)

    # 2) Direct value setting: append a marker at the end and set value
    new_value = (value0 or "") + insert_text_direct
    try:
        set_value(el, new_value)
        ok_direct = True
    except Exception as e:
        ok_direct = False
        print(f"[Direct set] Failed: {e}")

    # 3) Replace selection (or simulate an insertion at caret/end)
    # Refresh selection after direct set (some apps reset it)
    sel_rng = get_selected_range(el)
    if not sel_rng:
        # If no selection API, try to infer caret at end
        loc = (number_of_characters(el) if number_of_characters(el) >= 0 else len(get_value(el)))
        sel_rng = (loc, 0)

    try:
        loc, length = sel_rng
        # Ensure a valid location
        total = number_of_characters(el)
        if total >= 0:
            loc = max(0, min(loc, total))
            length = max(0, min(length, total - loc))

        # Replace by setting the selected range then setting kAXValueAttribute around it:
        before = string_for_range(el, 0, loc) if loc > 0 else ""
        after_len = (total - (loc + length)) if total >= 0 else 0
        after = string_for_range(el, loc + length, after_len) if after_len > 0 else ""

        set_selected_range(el, loc, length)
        set_value(el, before + replace_selection_with + after)
        ok_replace = True
    except Exception as e:
        ok_replace = False
        print(f"[Replace selection] Failed: {e}")

    # 4) Selection / caret / context
    sel_text = get_selected_text(el)
    rng = get_selected_range(el) or (len(get_value(el)), 0)
    caret = (rng[0] if rng else 0)  # insertion point if length==0

    total = number_of_characters(el)
    if total < 0:
        total = len(get_value(el))

    left = max(0, caret - context_window)
    right = min(total, caret + context_window)
    context = string_for_range(el, left, right - left)

    print("\n=== AX TEXT TEST REPORT ===")
    print(f"Text role OK: {is_text_input(role)}")
    print(f"Direct set value success: {ok_direct}")
    print(f"Replace selection success: {ok_replace}")
    print(f"Selected text (now): {sel_text!r}")
    print(f"Caret index (if length==0): {caret}")
    print(f"Context [{left}:{right}]: {context!r}")
    print("===========================")


if __name__ == "__main__":
    try:
        wait_and_test_ax_text_ops()
    except KeyboardInterrupt:
        print("\nCancelled.")
        sys.exit(1)