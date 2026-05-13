'use client'

import { useEffect, useState } from 'react'
import ScreenShell from '@/components/shared/ScreenShell'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { Card } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import { Button } from '@/components/ui/button'
import {
  Settings,
  Trophy,
  Lock,
  ChevronRight,
  Bell,
  Shield,
  HelpCircle,
  LogOut,
} from 'lucide-react'
import { SkelCard, SkelLine } from '@/components/shared/Skeleton'
import { api } from '@/lib/api'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'

const achievements = [
  { id: 'a1', label: 'First Win', unlocked: true },
  { id: 'a2', label: 'Streak Master', unlocked: true },
  { id: 'a3', label: 'Elite Rank', unlocked: false },
]

export default function ProfileScreen() {
  const [open, setOpen] = useState(false)
  const [user, setUser] = useState(null)

  useEffect(() => {
    api.user().then(setUser).catch(() => {})
  }, [])

  const xpPct = user ? Math.round((user.xp / user.xpToNext) * 100) : 0

  const settings = [
    { label: 'Notifications', icon: Bell },
    { label: 'Privacy', icon: Shield },
    { label: 'Help & Support', icon: HelpCircle },
    { label: 'Sign Out', icon: LogOut, danger: true },
  ]

  return (
    <ScreenShell
      title="Profile"
      right={
        <Button
          onClick={() => setOpen(true)}
          variant="ghost"
          size="icon"
          className="rounded-full bg-secondary/60 transition-transform active:scale-95"
        >
          <Settings className="h-4 w-4" />
        </Button>
      }
    >
      <Card className="relative overflow-hidden p-5 border-border bg-gradient-to-br from-secondary to-card">
        <div className="absolute -top-10 -right-10 h-40 w-40 rounded-full bg-accent/20 blur-3xl" />
        <div className="relative flex items-center gap-4">
          <Avatar className="h-16 w-16 ring-2 ring-primary/40">
            <AvatarFallback className="grad-primary text-primary-foreground font-bold text-lg">
              {user
                ? user.displayName
                    .split(' ')
                    .map((p) => p[0])
                    .join('')
                : 'NP'}
            </AvatarFallback>
          </Avatar>

          <div className="min-w-0 flex-1">
            {user ? (
              <>
                <p className="text-base font-semibold leading-tight truncate">
                  {user.displayName}
                </p>
                <p className="text-xs text-muted-foreground">@{user.username}</p>
                <div className="mt-2 inline-flex items-center gap-1.5 rounded-full bg-black/30 px-2 py-0.5 border border-white/10">
                  <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
                  <span className="text-[11px] font-medium">Level {user.level}</span>
                </div>
              </>
            ) : (
              <div className="space-y-2">
                <SkelLine className="h-4 w-32" />
                <SkelLine className="h-3 w-24" />
                <SkelLine className="h-3 w-20" />
              </div>
            )}
          </div>
        </div>

        <div className="relative mt-5">
          <div className="flex justify-between text-[11px] text-muted-foreground mb-1.5">
            <span>XP {user ? user.xp.toLocaleString() : '...'}</span>
            <span>Next: {user ? user.xpToNext.toLocaleString() : '...'}</span>
          </div>
          <Progress value={xpPct} className="h-2 bg-secondary transition-all duration-700" />
        </div>
      </Card>

      <div className="mt-5">
        <p className="text-xs uppercase tracking-wider text-muted-foreground px-1 mb-2">
          Achievements
        </p>
        <div className="grid grid-cols-3 gap-2">
          {achievements.map((a) => (
            <Card
              key={a.id}
              className={`p-3 border-border transition-transform hover:-translate-y-0.5 ${
                a.unlocked ? 'bg-card' : 'bg-card/50'
              }`}
            >
              <div
                className={`h-10 w-10 rounded-xl flex items-center justify-center mx-auto ${
                  a.unlocked ? 'grad-primary' : 'bg-secondary'
                }`}
              >
                {a.unlocked ? (
                  <Trophy className="h-5 w-5 text-primary-foreground" />
                ) : (
                  <Lock className="h-4 w-4 text-muted-foreground" />
                )}
              </div>
              <p
                className={`mt-2 text-[11px] text-center leading-tight ${
                  a.unlocked ? 'text-foreground' : 'text-muted-foreground'
                }`}
              >
                {a.label}
              </p>
            </Card>
          ))}
        </div>
      </div>

      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent className="max-w-[90vw] rounded-2xl bg-card border-border p-0 overflow-hidden">
          <DialogHeader className="px-5 pt-5">
            <DialogTitle>Settings</DialogTitle>
          </DialogHeader>
          <div className="divide-y divide-border">
            {settings.map((s) => (
              <button
                key={s.label}
                className={`w-full flex items-center justify-between px-5 py-3.5 text-sm hover:bg-secondary/40 transition ${
                  s.danger ? 'text-rose-400' : ''
                }`}
              >
                <span className="flex items-center gap-3">
                  <s.icon className="h-4 w-4" />
                  {s.label}
                </span>
                <ChevronRight className="h-4 w-4 text-muted-foreground" />
              </button>
            ))}
          </div>
        </DialogContent>
      </Dialog>
    </ScreenShell>
  )
}
