export const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";

export function getTelegramInitData(): string {
  if (typeof window === "undefined") return "";
  // @ts-expect-error Telegram injected object
  return window.Telegram?.WebApp?.initData || "";
}

export async function apiFetch(path: string, init?: RequestInit) {
  const token = typeof window !== "undefined" ? localStorage.getItem("tg_token") : null;
  const headers = new Headers(init?.headers || {});
  headers.set("Content-Type", "application/json");
  if (token) headers.set("Authorization", `Bearer ${token}`);
  const res = await fetch(`${API_BASE}${path}`, { ...init, headers, cache: "no-store" });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function loginIfNeeded() {
  if (typeof window === "undefined") return;
  if (localStorage.getItem("tg_token")) return;
  const initData = getTelegramInitData();
  if (!initData) return;
  const res = await fetch(`${API_BASE}/api/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ initData }),
  });
  if (!res.ok) return;
  const data = await res.json();
  localStorage.setItem("tg_token", data.token);
}
