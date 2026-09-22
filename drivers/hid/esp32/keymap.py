# Browser KeyboardEvent.code -> ESP32 hidSpecialKey() name (see hid_bridge.h).
# Anything not in this table is treated as a literal character via kt:.
SPECIAL_KEYS = {
    "Enter": "ENTER", "Backspace": "BACKSPACE", "Tab": "TAB", "Escape": "ESC",
    "Delete": "DELETE", "Home": "HOME", "End": "END",
    "ArrowUp": "ARROW_UP", "ArrowDown": "ARROW_DOWN",
    "ArrowLeft": "ARROW_LEFT", "ArrowRight": "ARROW_RIGHT",
    "PageUp": "PAGE_UP", "PageDown": "PAGE_DOWN", "CapsLock": "CAPSLOCK",
    **{f"F{n}": f"F{n}" for n in range(1, 13)},
}

# mod bitmask (contract: ctrl=0x01 shift=0x02 alt=0x04 meta=0x08) -> hidModCombo name.
# SHIFT is left out: it only changes which character `key` already resolved to,
# it never needs to be held separately for a plain character.
MOD_NAMES = [(0x01, "CTRL"), (0x04, "ALT"), (0x08, "WIN")]
