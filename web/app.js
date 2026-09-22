const driverSelect = document.getElementById('driver');
const statusEl = document.getElementById('status');
const mobileInput = document.getElementById('mobile-input');
const videoWrap = document.getElementById('video-wrap');

let ws = null;

function connect(driver) {
  if (ws) ws.close();
  statusEl.textContent = 'connecting…';
  statusEl.className = 'disconnected';
  ws = new WebSocket(`ws://${location.host}/ws/hid/${driver}`);
  ws.onopen = () => { statusEl.textContent = driver; statusEl.className = 'connected'; };
  ws.onclose = () => { statusEl.textContent = 'disconnected'; statusEl.className = 'disconnected'; };
  ws.onerror = () => { try { ws.close(); } catch (e) {} };
}

function send(code, key, mod, down) {
  if (!ws || ws.readyState !== WebSocket.OPEN) return;
  ws.send(JSON.stringify({ code, key, mod, down }));
}

function modBitmask(e) {
  return (e.ctrlKey ? 0x01 : 0) | (e.shiftKey ? 0x02 : 0) | (e.altKey ? 0x04 : 0) | (e.metaKey ? 0x08 : 0);
}

driverSelect.addEventListener('change', () => connect(driverSelect.value));
connect(driverSelect.value);

// Desktop: capture real keyboard while the page has focus.
window.addEventListener('keydown', (e) => {
  if (e.target === mobileInput) return; // mobile path handles this separately
  send(e.code, e.key, modBitmask(e), true);
  e.preventDefault();
});
window.addEventListener('keyup', (e) => {
  if (e.target === mobileInput) return;
  send(e.code, e.key, modBitmask(e), false);
  e.preventDefault();
});

// Mobile: tap the video to open the on-screen keyboard via the hidden input.
videoWrap.addEventListener('click', () => mobileInput.focus());

mobileInput.addEventListener('keydown', (e) => {
  send(e.code, e.key, modBitmask(e), true);
});
mobileInput.addEventListener('keyup', (e) => {
  send(e.code, e.key, modBitmask(e), false);
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

// Special-key button row (Esc, Tab, arrows, ...): send a down+up pulse.
document.getElementById('specials').addEventListener('click', (e) => {
  const code = e.target.dataset.code;
  if (!code) return;
  send(code, '', 0, true);
  setTimeout(() => send(code, '', 0, false), 30);
});
