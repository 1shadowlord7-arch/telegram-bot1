import { MongoClient } from 'mongodb'

const uri = process.env.MONGO_URL
const dbName = process.env.DB_NAME || 'novaplay'

let cached = global._mongo
if (!cached) cached = global._mongo = { client: null, db: null, seeded: false }

async function getDb() {
  if (cached.db) return cached.db
  const client = new MongoClient(uri)
  await client.connect()
  cached.client = client
  cached.db = client.db(dbName)
  return cached.db
}

const USER_ID = 'me'

async function seed(db) {
  if (cached.seeded) return

  const users = db.collection('users')
  const exists = await users.findOne({ _id: USER_ID })

  if (!exists) {
    await users.insertOne({
      _id: USER_ID,
      username: 'nova_player',
      displayName: 'Nova Player',
      level: 12,
      xp: 2840,
      xpToNext: 4000,
      balance: 12450,
      currency: 'NVC',
      stats: { wins: 87, streak: 5, rank: '#284', hours: '24h' },
    })
  }

  await db.collection('missions').insertMany([
    {
      _id: 'd1',
      scope: 'daily',
      title: 'Play 3 matches',
      progress: 2,
      target: 3,
      reward: 70,
      claimed: false,
    },
    {
      _id: 'd2',
      scope: 'daily',
      title: 'Win a match',
      progress: 1,
      target: 1,
      reward: 100,
      claimed: false,
    },
    {
      _id: 'd3',
      scope: 'daily',
      title: 'Invite a friend',
      progress: 0,
      target: 1,
      reward: 50,
      claimed: false,
    },
    {
      _id: 'w1',
      scope: 'weekly',
      title: 'Play 25 matches',
      progress: 14,
      target: 25,
      reward: 500,
      claimed: false,
    },
    {
      _id: 'w2',
      scope: 'weekly',
      title: 'Reach win streak of 5',
      progress: 5,
      target: 5,
      reward: 750,
      claimed: false,
    },
    {
      _id: 'w3',
      scope: 'weekly',
      title: 'Collect 1500 NVC',
      progress: 920,
      target: 1500,
      reward: 1000,
      claimed: false,
    },
  ])

  await db.collection('friends').insertMany([
    { _id: 'f1', name: 'Aria', level: 18, online: true },
    { _id: 'f2', name: 'Kai', level: 9, online: true },
    { _id: 'f3', name: 'Lyra', level: 22, online: false },
    { _id: 'f4', name: 'Orion', level: 7, online: false },
    { _id: 'f5', name: 'Vex', level: 14, online: true },
  ])

  await db.collection('activity').insertMany([
    {
      _id: 'a1',
      text: 'Won a Blitz match',
      reward: 120,
      time: '2m ago',
      createdAt: Date.now() - 120000,
    },
    {
      _id: 'a2',
      text: 'Daily login claimed',
      reward: 50,
      time: '1h ago',
      createdAt: Date.now() - 3600000,
    },
    {
      _id: 'a3',
      text: 'Aria sent you a gift',
      reward: 10,
      time: '3h ago',
      createdAt: Date.now() - 10800000,
    },
  ])

  await db.collection('rewards').insertMany([
    {
      _id: 'r1',
      label: 'Daily Mission',
      amount: 50,
      time: 'Today, 10:24',
      createdAt: Date.now() - 1000,
    },
    {
      _id: 'r2',
      label: 'Match Win',
      amount: 120,
      time: 'Today, 09:50',
      createdAt: Date.now() - 2000,
    },
    {
      _id: 'r3',
      label: 'Weekly Bonus',
      amount: 500,
      time: 'Yesterday',
      createdAt: Date.now() - 3000,
    },
    {
      _id: 'r4',
      label: 'Referral',
      amount: 200,
      time: '2d ago',
      createdAt: Date.now() - 4000,
    },
  ])

  cached.seeded = true
}

export async function db() {
  const d = await getDb()
  await seed(d)
  return d
}

export { USER_ID }
