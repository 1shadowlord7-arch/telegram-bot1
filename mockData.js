// Mock data for the Mini App MVP. Replace with API calls later.
export const user = {
  id: 'u_001',
  username: 'nova_player',
  displayName: 'Nova Player',
  avatar: null,
  level: 12,
  xp: 2840,
  xpToNext: 4000,
  balance: 12450,
  currency: 'NVC',
}

export const quickStats = [
  { key: 'wins', label: 'Wins', value: 87, accent: 'cyan' },
  { key: 'streak', label: 'Streak', value: 5, accent: 'violet' },
  { key: 'rank', label: 'Rank', value: '#284', accent: 'green' },
  { key: 'hours', label: 'Hours', value: '24h', accent: 'amber' },
]

export const recentActivity = [
  { id: 'a1', type: 'win', text: 'Won a Blitz match', reward: '+120 NVC', time: '2m ago' },
  { id: 'a2', type: 'mission', text: 'Daily login claimed', reward: '+50 NVC', time: '1h ago' },
  { id: 'a3', type: 'friend', text: 'Aria sent you a gift', reward: '+10 NVC', time: '3h ago' },
]

export const categories = ['All', 'Arcade', 'Strategy', 'Multiplayer', 'Casual']

export const games = [
  { id: 'g1', title: 'Neon Drift', category: 'Arcade', accent: 'from-cyan-500/40 to-blue-600/40' },
  {
    id: 'g2',
    title: 'Cipher Wars',
    category: 'Strategy',
    accent: 'from-violet-500/40 to-fuchsia-600/40',
  },
  {
    id: 'g3',
    title: 'Pixel Royale',
    category: 'Multiplayer',
    accent: 'from-emerald-500/40 to-teal-600/40',
  },
  {
    id: 'g4',
    title: 'Tap Tempo',
    category: 'Casual',
    accent: 'from-amber-500/40 to-orange-600/40',
  },
  {
    id: 'g5',
    title: 'Astro Crush',
    category: 'Arcade',
    accent: 'from-pink-500/40 to-rose-600/40',
  },
  {
    id: 'g6',
    title: 'Hex Tactics',
    category: 'Strategy',
    accent: 'from-sky-500/40 to-indigo-600/40',
  },
  {
    id: 'g7',
    title: 'Arena 5v5',
    category: 'Multiplayer',
    accent: 'from-red-500/40 to-orange-600/40',
  },
  {
    id: 'g8',
    title: 'Solitaire+',
    category: 'Casual',
    accent: 'from-lime-500/40 to-green-600/40',
  },
]

export const dailyMissions = [
  { id: 'd1', title: 'Play 3 matches', progress: 2, target: 3, reward: 75 },
  { id: 'd2', title: 'Win a match', progress: 1, target: 1, reward: 100, claimable: true },
  { id: 'd3', title: 'Invite a friend', progress: 0, target: 1, reward: 200 },
]

export const weeklyMissions = [
  { id: 'w1', title: 'Play 25 matches', progress: 14, target: 25, reward: 500 },
  {
    id: 'w2',
    title: 'Reach win streak of 5',
    progress: 5,
    target: 5,
    reward: 750,
    claimable: true,
  },
  { id: 'w3', title: 'Collect 1500 NVC', progress: 920, target: 1500, reward: 1000 },
]

export const friends = [
  { id: 'f1', name: 'Aria', level: 18, online: true },
  { id: 'f2', name: 'Kai', level: 9, online: true },
  { id: 'f3', name: 'Lyra', level: 22, online: false },
  { id: 'f4', name: 'Orion', level: 7, online: false },
  { id: 'f5', name: 'Vex', level: 14, online: true },
]

export const rewardHistory = [
  { id: 'r1', label: 'Daily Mission', amount: 50, time: 'Today, 10:24' },
  { id: 'r2', label: 'Match Win', amount: 120, time: 'Today, 09:50' },
  { id: 'r3', label: 'Weekly Bonus', amount: 500, time: 'Yesterday' },
  { id: 'r4', label: 'Referral', amount: 200, time: '2d ago' },
]

export const achievements = [
  { id: 'ac1', label: 'First Blood', unlocked: true },
  { id: 'ac2', label: 'Win Streak x5', unlocked: true },
  { id: 'ac3', label: 'Top 500', unlocked: false },
  { id: 'ac4', label: 'Marathon', unlocked: false },
  { id: 'ac5', label: 'Social Butterfly', unlocked: true },
  { id: 'ac6', label: 'Night Owl', unlocked: false },
]
