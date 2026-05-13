import { NextResponse } from 'next/server'
import { db, USER_ID } from '@/lib/mongodb'
import { v4 as uuidv4 } from 'uuid'

const json = (data, status = 200) => NextResponse.json(data, { status })
const err = (m, s = 400) => json({ error: m }, s)

const clean = (doc) => {
  if (!doc) return doc
  const { _id, ...rest } = doc
  return { id: _id, ...rest }
}

async function handle(method, segments, body) {
  const d = await db()
  const [root, sub] = segments

  // /api/user
  if (root === 'user') {
    const u = await d.collection('users').findOne({ _id: USER_ID })
    return json(clean(u))
  }

  // /api/missions & /api/missions/claim
  if (root === 'missions') {
    if (method === 'GET') {
      const list = await d.collection('missions').find({ claimed: false }).toArray()
      return json({
        daily: list.filter((m) => m.scope === 'daily').map(clean),
        weekly: list.filter((m) => m.scope === 'weekly').map(clean),
      })
    }
    if (method === 'POST' && sub === 'claim') {
      const id = body?.id
      if (!id) return err('id required')
      const m = await d.collection('missions').findOne({ _id: id, claimed: false })
      if (!m) return err('Mission not found', 404)
      if (m.progress < m.target) return err('Not yet completed')
      await d.collection('missions').updateOne({ _id: id }, { $set: { claimed: true } })
      const upd = await d.collection('users').findOneAndUpdate(
        { _id: USER_ID },
        { $inc: { balance: m.reward, xp: Math.floor(m.reward / 2) } },
        { returnDocument: 'after' }
      )
      const user = upd?.value || upd
      await d.collection('rewards').insertOne({
        _id: uuidv4(),
        label: `${m.scope === 'daily' ? 'Daily' : 'Weekly'} Mission`,
        amount: m.reward,
        time: 'Just now',
        createdAt: Date.now(),
      })
      await d.collection('activity').insertOne({
        _id: uuidv4(),
        text: `Claimed: ${m.title}`,
        reward: m.reward,
        time: 'Just now',
        createdAt: Date.now(),
      })
      return json({ ok: true, reward: m.reward, user: clean(user) })
    }
  }

  // /api/friends
  if (root === 'friends') {
    if (method === 'GET') {
      const list = await d.collection('friends').find({}).toArray()
      return json(list.map(clean))
    }
    if (method === 'POST') {
      const name = (body?.name || '').trim()
      if (!name) return err('name required')
      const id = uuidv4()
      const friend = { _id: id, name, level: 1, online: false, pending: true }
      await d.collection('friends').insertOne(friend)
      return json(clean(friend))
    }
  }

  // /api/activity
  if (root === 'activity') {
    const list = await d
      .collection('activity')
      .find({})
      .sort({ createdAt: -1 })
      .limit(10)
      .toArray()
    return json(list.map(clean))
  }

  // /api/rewards
  if (root === 'rewards') {
    const list = await d
      .collection('rewards')
      .find({})
      .sort({ createdAt: -1 })
      .limit(20)
      .toArray()
    return json(list.map(clean))
  }

  // /api/health
  if (root === 'health' || !root) {
    return json({ ok: true, app: 'NovaPlay' })
  }

  return err('Not found', 404)
}

async function readBody(request) {
  try {
    return await request.json()
  } catch {
    return null
  }
}

export async function GET(request, { params }) {
  try {
    const segs = params?.path || []
    return await handle('GET', segs, null)
  } catch (e) {
    console.error(e)
    return err(e.message, 500)
  }
}

export async function POST(request, { params }) {
  try {
    const segs = params?.path || []
    const body = await readBody(request)
    return await handle('POST', segs, body)
  } catch (e) {
    console.error(e)
    return err(e.message, 500)
  }
}

export async function PATCH(request, { params }) {
  try {
    const segs = params?.path || []
    const body = await readBody(request)
    return await handle('PATCH', segs, body)
  } catch (e) {
    console.error(e)
    return err(e.message, 500)
  }
}
