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

// Updates modMask if `code` is itself a modifier key. Returns true when it
// was (so the caller still forwards the event - a bare modifier press is a
// real keyboard event too, see CONTRACT.md).
function trackModifier(code, down) {
  const bit = MOD_BIT_BY_CODE[code];
  if (!bit) return false;
  modMask = down ? (modMask | bit) : (modMask & ~bit);
  return true;
}

driverSelect.addEventListener('change', () => connect(driverSelect.value));
connect(driverSelect.value);

// Desktop: capture real keyboard while the page has focus.
window.addEventListener('keydown', (e) => {
  if (e.target === mobileInput) return; // mobile path handles this separately
  trackModifier(e.code, true);
  send(e.code, e.key, modMask, true);
  e.preventDefault();
});
window.addEventListener('keyup', (e) => {
  if (e.target === mobileInput) return;
  trackModifier(e.code, false);
  send(e.code, e.key, modMask, false);
  e.preventDefault();
});

// Mobile: tap the video to open the on-screen keyboard via the hidden input.
videoWrap.addEventListener('click', () => mobileInput.focus());

mobileInput.addEventListener('keydown', (e) => {
  trackModifier(e.code, true);
  send(e.code, e.key, modMask, true);
});
mobileInput.addEventListener('keyup', (e) => {
  trackModifier(e.code, false);
  send(e.code, e.key, modMask, false);
});
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

// Paste: the target is real HID, there's no clipboard on the other end, so
// intercept the browser's own paste and replay it as a sequence of key
// events instead. No `code` exists for pasted text (only the browser knows
// what was pasted, not which physical keys would have produced it) - drivers
// that need one (unifying) fall back to a literal-character table.
window.addEventListener('paste', (e) => {
  e.preventDefault();
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
