# Browser KeyboardEvent.code -> USB HID Usage Page 0x07 code.
CODE_TO_HID = {
    **{f"Key{c}": 0x04 + i for i, c in enumerate("ABCDEFGHIJKLMNOPQRSTUVWXYZ")},
    **{f"Digit{d}": 0x1E + i for i, d in enumerate("123456789")},
    "Digit0": 0x27,
    "Enter": 0x28, "Escape": 0x29, "Backspace": 0x2A, "Tab": 0x2B, "Space": 0x2C,
    "Minus": 0x2D, "Equal": 0x2E, "BracketLeft": 0x2F, "BracketRight": 0x30,
    "Backslash": 0x31, "Semicolon": 0x33, "Quote": 0x34, "Backquote": 0x35,
    "Comma": 0x36, "Period": 0x37, "Slash": 0x38, "CapsLock": 0x39,
    "F1": 0x3A, "F2": 0x3B, "F3": 0x3C, "F4": 0x3D, "F5": 0x3E, "F6": 0x3F,
    "F7": 0x40, "F8": 0x41, "F9": 0x42, "F10": 0x43, "F11": 0x44, "F12": 0x45,
    "Delete": 0x4C, "End": 0x4D, "PageDown": 0x4E, "ArrowRight": 0x4F,
    "ArrowLeft": 0x50, "ArrowDown": 0x51, "ArrowUp": 0x52,
    "Home": 0x4A, "PageUp": 0x4B,
    # Bare modifier press/release: no regular key, HID usage 0 (the standard
    # "no key" sentinel) - the state change lives entirely in `mod`, exactly
    # like a real keyboard's own report.
    "ControlLeft": 0, "ShiftLeft": 0, "AltLeft": 0, "MetaLeft": 0,
    "ControlRight": 0, "ShiftRight": 0, "AltRight": 0, "MetaRight": 0,
}

# Literal character -> (HID usage, needs_shift). Used when there's no
# KeyboardEvent.code to go on (paste: the browser only gives us the resolved
# text, not which physical keys produced it). US layout, since HID usage
# codes are positional, not character-based.
_DIGIT_ROW = {
    "1": (0x1E, "!"), "2": (0x1F, "@"), "3": (0x20, "#"), "4": (0x21, "$"),
    "5": (0x22, "%"), "6": (0x23, "^"), "7": (0x24, "&"), "8": (0x25, "*"),
    "9": (0x26, "("), "0": (0x27, ")"),
}
_PUNCT_ROW = {
    "-": (0x2D, "_"), "=": (0x2E, "+"), "[": (0x2F, "{"), "]": (0x30, "}"),
    "\\": (0x31, "|"), ";": (0x33, ":"), "'": (0x34, '"'), "`": (0x35, "~"),
    ",": (0x36, "<"), ".": (0x37, ">"), "/": (0x38, "?"),
}

CHAR_TO_HID = {" ": (0x2C, False), "\n": (0x28, False), "\t": (0x2B, False)}
for _c, _hid in {c: 0x04 + i for i, c in enumerate("abcdefghijklmnopqrstuvwxyz")}.items():
    CHAR_TO_HID[_c] = (_hid, False)
    CHAR_TO_HID[_c.upper()] = (_hid, True)
for _unshifted, (_hid, _shifted_ch) in {**_DIGIT_ROW, **_PUNCT_ROW}.items():
    CHAR_TO_HID[_unshifted] = (_hid, False)
    CHAR_TO_HID[_shifted_ch] = (_hid, True)
