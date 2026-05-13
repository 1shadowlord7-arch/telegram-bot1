'use client'

import { useEffect, useState } from 'react'
import ScreenShell from '@/components/shared/ScreenShell'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  DialogFooter,
} from '@/components/ui/dialog'
import { UserPlus, Search, Loader2 } from 'lucide-react'
import { SkelCard } from '@/components/shared/Skeleton'
import { api } from '@/lib/api'
import { toast } from 'sonner'

function FriendRow({ f }) {
  return (
    <div className="flex items-center justify-between px-3 py-3 transition-colors hover:bg-secondary/30 animate-in fade-in slide-in-from-left-2">
      <div className="flex items-center gap-3 min-w-0">
        <div className="relative shrink-0">
          <Avatar className="h-10 w-10">
            <AvatarFallback className="bg-secondary text-foreground text-xs">
              {f.name.slice(0, 2).toUpperCase()}
            </AvatarFallback>
          </Avatar>
          <span
            className={`absolute bottom-0 right-0 h-2.5 w-2.5 rounded-full border-2 border-card ${
              f.online ? 'bg-emerald-400 pulse-glow' : 'bg-muted-foreground/40'
            }`}
          />
        </div>
        <div className="min-w-0">
          <p className="text-sm font-medium leading-tight truncate">
            {f.name}
            {f.pending ? (
              <span className="ml-2 text-[10px] text-amber-300">pending</span>
            ) : null}
          </p>
          <p className="text-[11px] text-muted-foreground">
            Lv {f.level} · {f.online ? 'Online' : 'Offline'}
          </p>
        </div>
      </div>
      <Button
        size="sm"
        variant="secondary"
        className="h-8 rounded-lg text-xs transition-transform active:scale-95"
      >
        Invite
      </Button>
    </div>
  )
}

export default function FriendsScreen() {
  const [open, setOpen] = useState(false)
  const [handle, setHandle] = useState('')
  const [busy, setBusy] = useState(false)
  const [list, setList] = useState(null)

  const load = () => api.friends().then(setList).catch(() => {})

  useEffect(() => {
    load()
  }, [])

  const send = async () => {
    const name = handle.trim()
    if (!name) return
    setBusy(true)
    try {
      await api.addFriend(name)
      toast.success(`Friend request sent to @${name}`)
      setHandle('')
      setOpen(false)
      await load()
    } catch (e) {
      toast.error(e.message)
    } finally {
      setBusy(false)
    }
  }

  const online = list ? list.filter((f) => f.online) : []
  const offline = list ? list.filter((f) => !f.online) : []

  return (
    <ScreenShell
      title="Friends"
      right={
        <Dialog open={open} onOpenChange={setOpen}>
          <DialogTrigger asChild>
            <Button
              size="sm"
              className="h-9 rounded-full gap-1.5 px-3 transition-transform active:scale-95"
            >
              <UserPlus className="h-4 w-4" /> Add
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-[90vw] rounded-2xl bg-card border-border">
            <DialogHeader>
              <DialogTitle>Add a friend</DialogTitle>
            </DialogHeader>
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                value={handle}
                onChange={(e) => setHandle(e.target.value)}
                placeholder="Enter username"
                className="pl-9 h-11 rounded-xl bg-secondary/60"
              />
            </div>
            <DialogFooter>
              <Button
                onClick={send}
                disabled={busy}
                className="w-full h-10 rounded-xl gap-1.5 px-3 transition-transform active:scale-95"
              >
                {busy ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
                {busy ? 'Sending...' : 'Send Request'}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      }
    >
      {!list ? (
        <div className="space-y-3">
          <SkelCard className="h-[168px]" />
          <SkelCard className="h-[120px]" />
        </div>
      ) : (
        <>
          {online.length > 0 ? (
            <div>
              <p className="text-xs uppercase tracking-wider text-muted-foreground px-1 mb-2">
                Online — {online.length}
              </p>
              <Card className="divide-y divide-border bg-card border-border overflow-hidden">
                {online.map((f) => (
                  <FriendRow key={f.id} f={f} />
                ))}
              </Card>
            </div>
          ) : null}

          {offline.length > 0 ? (
            <div>
              <p className="text-xs uppercase tracking-wider text-muted-foreground px-1 mb-2">
                Offline — {offline.length}
              </p>
              <Card className="divide-y divide-border bg-card border-border overflow-hidden">
                {offline.map((f) => (
                  <FriendRow key={f.id} f={f} />
                ))}
              </Card>
            </div>
          ) : null}
        </>
      )}
    </ScreenShell>
  )
}
