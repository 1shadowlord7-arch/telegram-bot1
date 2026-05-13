// Tiny client wrapper.
async function req(path, options = {}) {
  const res = await fetch(`/api${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!res.ok) {
    const t = await res.json().catch(() => ({}))
    throw new Error(t.error || `Request failed: ${res.status}`)
  }
  return res.json()
}

export const api = {
  user: () => req('/user'),
  missions: () => req('/missions'),
  claim: (id) =>
    req('/missions/claim', { method: 'POST', body: JSON.stringify({ id }) }),
  friends: () => req('/friends'),
  addFriend: (name) =>
    req('/friends', { method: 'POST', body: JSON.stringify({ name }) }),
  activity: () => req('/activity'),
  rewards: () => req('/rewards'),
}
