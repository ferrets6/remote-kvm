const driverSelect = document.getElementById('driver');
const statusEl = document.getElementById('status');
const mobileInput = document.getElementById('mobile-input');
const videoWrap = document.getElementById('video-wrap');

let ws = null;

function connect(driver) {
  if (ws) ws.close();
  statusEl.textContent = 'connecting…';
  statusEl.className = 'disconnected';
  const wsProto = location.protocol === 'https:' ? 'wss' : 'ws';
  ws = new WebSocket(`${wsProto}://${location.host}/ws/hid/${driver}`);
  ws.onopen = () => { statusEl.textContent = driver; statusEl.className = 'connected'; };
  ws.onclose = () => { statusEl.textContent = 'disconnected'; statusEl.className = 'disconnected'; };
  ws.onerror = () => { try { ws.close(); } catch (e) {} };
}

function send(code, key, mod, down) {
  if (!ws || ws.readyState !== WebSocket.OPEN) return;
  ws.send(JSON.stringify({ code, key, mod, down }));
}

// Full HID modifier byte, left/right distinct (AltGr is physically RightAlt) -
// see drivers/CONTRACT.md. `e.ctrlKey`/`e.shiftKey`/etc. can't tell left from
// right, so track real state from `code` instead.
const MOD_BIT_BY_CODE = {
  ControlLeft: 0x01, ShiftLeft: 0x02, AltLeft: 0x04, MetaLeft: 0x08,
  ControlRight: 0x10, ShiftRight: 0x20, AltRight: 0x40, MetaRight: 0x80,
};
let modMask = 0;

// Left+right bit pairs for the coarse booleans every KeyboardEvent carries.
const MOD_BITS_BY_FLAG = [
  ['ctrlKey', 0x01 | 0x10], ['shiftKey', 0x02 | 0x20],
  ['altKey', 0x04 | 0x40], ['metaKey', 0x08 | 0x80],
];

// modMask only learns about modifiers from their own keydown/keyup, so it can
// drift: a keyup swallowed while the page wasn't focused (Alt+Tab, Ctrl+Tab)
// leaves a bit stuck, a Ctrl already held when the page gained focus leaves
// one missing. Every event also carries the browser's own view (e.ctrlKey...),
// which can't tell left from right but is never stale - use it to repair.
function syncModifiers(e) {
  for (const [flag, bits] of MOD_BITS_BY_FLAG) {
    if (!e[flag]) modMask &= ~bits;
    else if (!(modMask & bits)) modMask |= bits & -bits; // held but unseen: assume left
  }
}

// Codes currently down on the target, so they can all be released if the page
// loses focus before their keyup arrives.
const heldCodes = new Set();

// Shared by every keydown/keyup path. A bare modifier press is a real
// keyboard event too (see CONTRACT.md), so it is forwarded like any key.
function handleKey(e, down) {
  const bit = MOD_BIT_BY_CODE[e.code];
  if (bit) modMask = down ? (modMask | bit) : (modMask & ~bit);
  syncModifiers(e);
  if (down) heldCodes.add(e.code); else heldCodes.delete(e.code);
  send(e.code, e.key, modMask, down);
}

// Losing focus mid-keypress means the keyups will never reach us: release
// everything on the target instead of leaving keys/modifiers stuck down.
window.addEventListener('blur', () => {
  if (!modMask && !heldCodes.size) return;
  modMask = 0;
  for (const code of heldCodes) send(code, '', 0, false);
  heldCodes.clear();
  send('ControlLeft', 'Control', 0, false); // usage 0 + mod 0: clears modifier state
});

driverSelect.addEventListener('change', () => connect(driverSelect.value));
connect(driverSelect.value);

// Ctrl/Cmd+V (and Shift+Insert) are forwarded to the target like any other
// key, exactly as RDP/AnyDesk would - the target pastes from ITS clipboard.
// The browser still fires a `paste` event for them, which must not also type
// the local clipboard, so remember when the shortcut was last pressed.
let lastPasteShortcutAt = 0;

function notePasteShortcut(e) {
  if (((e.ctrlKey || e.metaKey) && e.code === 'KeyV') || (e.shiftKey && e.code === 'Insert')) {
    lastPasteShortcutAt = performance.now();
  }
}

// Desktop: capture real keyboard while the page has focus.
window.addEventListener('keydown', (e) => {
  notePasteShortcut(e); // also sees keydowns bubbling up from mobileInput
  if (e.target === mobileInput) return; // mobile path handles this separately
  handleKey(e, true);
  e.preventDefault();
});
window.addEventListener('keyup', (e) => {
  if (e.target === mobileInput) return;
  handleKey(e, false);
  e.preventDefault();
});

// Mobile: tap the video to open the on-screen keyboard via the hidden input.
videoWrap.addEventListener('click', () => mobileInput.focus());

mobileInput.addEventListener('keydown', (e) => handleKey(e, true));
mobileInput.addEventListener('keyup', (e) => handleKey(e, false));
// Fallback for virtual keyboards that don't fire reliable keydown/keyup:
// react to the actual inserted character instead, then clear the field.
mobileInput.addEventListener('input', (e) => {
  if (e.inputType === 'insertText' && e.data) {
    for (const ch of e.data) {
      send('', ch, 0, true);
      send('', ch, 0, false);
    }
  } else if (e.inputType === 'deleteContentBackward') {
    send('Backspace', '', 0, true);
    send('Backspace', '', 0, false);
  }
  mobileInput.value = '';
});

// Paste (right-click -> Paste): the target is real HID, there's no clipboard
// channel to it, so the only way to get local text there is to type it.
// Intercept the browser's paste and replay it as key events. No `code` exists
// for pasted text (only the browser knows what was pasted, not which physical
// keys would have produced it) - drivers that need one (unifying) fall back
// to a literal-character table.
//
// The context menu only offers "Paste" on an editable element, so a
// transparent contenteditable layer covers the video. It never keeps text.
const pasteLayer = document.getElementById('paste-layer');
pasteLayer.addEventListener('beforeinput', (e) => e.preventDefault());

window.addEventListener('paste', (e) => {
  e.preventDefault();
  if (performance.now() - lastPasteShortcutAt < 500) return; // Ctrl+V: forwarded as a key instead
  const text = (e.clipboardData || window.clipboardData).getData('text');
  for (const ch of text) {
    send('', ch, 0, true);
    send('', ch, 0, false);
  }
});

// Special-key button row (Esc, Tab, arrows, ...): send a down+up pulse.
document.getElementById('specials').addEventListener('click', (e) => {
  const code = e.target.dataset.code;
  if (!code) return;
  send(code, '', 0, true);
  setTimeout(() => send(code, '', 0, false), 30);
});
