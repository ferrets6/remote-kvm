# Browser KeyboardEvent.code -> USB HID Usage Page 0x07 code.
# Modifier bits already match the driver contract 1:1 (ctrl=0x01 shift=0x02
# alt=0x04 meta=0x08), so only regular keys need a table.
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
}
