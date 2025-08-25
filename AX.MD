I’m listing the exact function and attribute names you’ll want (Rust crates like accessibility-sys expose these 1:1).

1) Detect the focused text field
   •	Get the system object: AXUIElementCreateSystemWide().  ￼
   •	Ask it for the currently focused UI element: AXUIElementCopyAttributeValue(system, kAXFocusedUIElementAttribute, &elem).  ￼
   •	Optionally confirm the element itself reports focus: kAXFocusedAttribute on elem.  ￼
   •	(Often useful) Inspect role/subrole via kAXRoleAttribute to ensure it’s a text control. (Same header as above.)  ￼

2) Determine if you can insert/modify text

Use both the “attribute is settable” path and the “actions” path:
•	Check if the text value can be set directly:
•	AXUIElementIsAttributeSettable(elem, kAXValueAttribute, &settable).
•	If true, set with AXUIElementSetAttributeValue(elem, kAXValueAttribute, CFString).  ￼ ￼
•	Check supported actions in case the control prefers actions over direct setting:
•	AXUIElementCopyActionNames(elem, &actions), then perform with AXUIElementPerformAction(elem, action) if an insertion-related action is advertised. (Action names vary by host app.)  ￼ ￼
•	Last-resort (simulated typing) if neither of the above is available:
•	AXUIElementPostKeyboardEvent(appElem, virtualKey, isDown).  ￼ ￼

3) Read selection and “surrounding” text from the same field
   •	Current selection: kAXSelectedTextRangeAttribute (character range), kAXSelectedTextAttribute (string).  ￼
   •	Total length (to bound ranges): kAXNumberOfCharactersAttribute.  ￼
   •	Extract text for an arbitrary range via parameterized attributes:
   •	AXUIElementCopyParameterizedAttributeValue(elem, kAXAttributedStringForRangeParameterizedAttribute, range, &value) (rich text) or the plain-string variant.  ￼
   •	Helpful range utilities (also parameterized):
   •	kAXRangeForLineParameterizedAttribute, kAXRangeForIndexParameterizedAttribute, kAXRangeForPositionParameterizedAttribute to map lines, indices, or screen positions to text ranges before calling “string for range”.  ￼

Minimal call flow (conceptual)
1.	sys = AXUIElementCreateSystemWide() → AXUIElementCopyAttributeValue(sys, kAXFocusedUIElementAttribute, &elem) → check kAXFocusedAttribute / kAXRoleAttribute.  ￼ ￼
2.	Try AXUIElementIsAttributeSettable(elem, kAXValueAttribute) → AXUIElementSetAttributeValue(...); else look for an insertion action via AXUIElementCopyActionNames → AXUIElementPerformAction; else AXUIElementPostKeyboardEvent(...).  ￼ ￼
3.	Read context: kAXSelectedTextRangeAttribute / kAXNumberOfCharactersAttribute → compute desired AXTextRange → AXUIElementCopyParameterizedAttributeValue(..., kAXAttributedStringForRangeParameterizedAttribute, ...). 