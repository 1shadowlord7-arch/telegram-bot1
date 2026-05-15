// Telegram WebApp helpers
export function getTelegramUser() {
  try {
    const tg = typeof window !== 'undefined' ? window.Telegram?.WebApp : null;
    const u = tg?.initDataUnsafe?.user;
    if (u && u.id) {
      return {
        id: String(u.id),
        username: u.username || `user_${u.id}`,
        displayName: [u.first_name, u.last_name].filter(Boolean).join(' ') || `Player ${u.id}`,
      };
    }
  } catch (_) {}
  // Fallback: stable per-device id stored in localStorage (web preview / non-Telegram)
  let did = null;
  try { did = localStorage.getItem('nexro_device_id'); } catch (_) {}
  if (!did) {
    did = 'dev_' + Math.random().toString(36).slice(2, 10);
    try { localStorage.setItem('nexro_device_id', did); } catch (_) {}
  }
  return { id: did, username: 'guest', displayName: 'NEXRO Player' };
}

export function initTelegramWebApp() {
  try {
    const tg = window?.Telegram?.WebApp;
    if (tg) {
      tg.ready();
      tg.expand();
      tg.setHeaderColor?.('#07080d');
    }
  } catch (_) {}
}
