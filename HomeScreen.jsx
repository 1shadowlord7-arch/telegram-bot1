'use client'

import { useEffect, useState } from 'react'
import ScreenShell from '@/components/shared/ScreenShell'
import SectionHeader from '@/components/shared/SectionHeader'
import { SkelCard, SkelLine } from '@/components/shared/Skeleton'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import {
  Bell,
  Coins,
  Trophy,
  Flame,
  Clock,
  ArrowUpRight,
  ChevronRight,
  Gift,
} from 'lucide-react'
import { api } from '@/lib/api'

const iconMap = {
  wins: Trophy,
  streak: Flame,
  rank: ArrowUpRight,
  hours: Clock,
}

const statLabels = {
  wins: 'Wins',
  streak: 'Streak',
  rank: 'Rank',
  hours: 'Hours',
}

export default function HomeScreen({ onNavigate }) {
  const [user, setUser] = useState(null)
  const [activity, setActivity] = useState(null)

  useEffect(() => {
    api.user().then(setUser).catch(() => {})
    api.activity().then(setActivity).catch(() => {})
  }, [])

  return (
    <ScreenShell title={null}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Avatar className="h-11 w-11 ring-2 ring-primary/40">
            <AvatarFallback className="grad-primary text-primary-foreground font-semibold">
              {user ? user.displayName.split(' ').map((p) => p[0]).join('') : 'NP'}
            </AvatarFallback>
          </Avatar>

          <div>
            <p className="text-xs text-muted-foreground">Welcome back</p>
            {user ? (
              <p className="text-sm font-semibold">@{user.username}</p>
            ) : (
              <SkelLine className="h-3.5 w-24 mt-1" />
            )}
          </div>
        </div>

        <Button
          variant="ghost"
          size="icon"
          className="rounded-full bg-secondary/60"
        >
          <Bell className="h-4 w-4" />
        </Button>
      </div>

      {/* Balance card */}
      <Card className="relative overflow-hidden border-border bg-gradient-to-br from-secondary to-card p-4 transition-transform active:scale-[0.99]">
        <div className="absolute -top-10 -right-10 h-40 w-40 rounded-full bg-primary/15 blur-3xl" />
        <div className="absolute -bottom-12 -left-10 h-40 w-40 rounded-full bg-accent/15 blur-3xl" />
        <div className="relative flex items-center justify-between">
          <div>
            <p className="text-[11px] uppercase tracking-wider text-muted-foreground">
              Balance
            </p>
            {user ? (
              <div className="mt-1 flex items-baseline gap-1.5 transition-all duration-500">
                <span className="text-3xl font-bold grad-text">
                  {user.balance.toLocaleString()}
                </span>
                <span className="text-sm font-medium text-muted-foreground">
                  {user.currency}
                </span>
              </div>
            ) : (
              <SkelLine className="h-8 w-32 mt-1" />
            )}
          </div>

          <div className="h-12 w-12 rounded-xl grad-primary flex items-center justify-center">
            <Coins className="h-6 w-6 text-primary-foreground" />
          </div>
        </div>

        <div className="relative mt-4 grid grid-cols-2 gap-2">
          <Button
            onClick={() => onNavigate('wallet')}
            variant="secondary"
            className="h-9 rounded-xl text-xs transition-transform active:scale-95"
          >
            View Wallet
          </Button>
          <Button
            onClick={() => onNavigate('missions')}
            className="h-9 rounded-xl text-xs grad-primary text-primary-foreground hover:opacity-90 transition-transform active:scale-95"
          >
            Earn More
          </Button>
        </div>
      </Card>

      {/* Featured banner */}
      <Card className="relative overflow-hidden border-0 p-0 transition-transform active:scale-[0.99]">
        <div className="relative aspect-[16/8] grad-primary">
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_80%_20%,rgba(255,255,255,0.18),transparent_50%)]" />
          <div className="absolute inset-0 p-4 flex flex-col justify-between">
            <div className="inline-flex items-center gap-1 self-start rounded-full bg-black/30 backdrop-blur px-2.5 py-1 text-[10px] font-medium border border-white/15">
              <Gift className="h-3 w-3" /> Limited Event
            </div>

            <div>
              <p className="text-lg font-bold leading-tight text-primary-foreground">
                Season Pass – Vol 1
              </p>
              <p className="text-xs text-primary-foreground/80">
                Unlock exclusive rewards & skins
              </p>
            </div>

            <div className="flex items-center gap-0.5 self-start">
              <Button
                variant="ghost"
                size="sm"
                className="h-9 rounded-xl bg-white/10 text-xs text-primary-foreground hover:bg-white/15 transition-transform active:scale-95"
              >
                View Pass
              </Button>
              <Button
                variant="ghost"
                size="sm"
                className="h-9 rounded-xl bg-white/10 text-xs text-primary-foreground hover:bg-white/15 transition-transform active:scale-95"
              >
                Collect
              </Button>
            </div>
          </div>
        </div>
      </Card>

      {/* Quick stats */}
      <div>
        <SectionHeader title="Quick Stats" />
        <div className="grid grid-cols-4 gap-2">
          {user
            ? ['wins', 'streak', 'rank', 'hours'].map((k) => {
                const Icon = iconMap[k]
                return (
                  <Card
                    key={k}
                    className="p-3 bg-card border-border transition-transform hover:-translate-y-0.5"
                  >
                    <Icon className="h-4 w-4 text-primary mb-2" />
                    <p className="text-base font-bold leading-none">{user.stats[k]}</p>
                    <p className="text-[10px] text-muted-foreground mt-1">
                      {statLabels[k]}
                    </p>
                  </Card>
                )
              })
            : Array.from({ length: 4 }).map((_, i) => (
                <SkelCard key={i} className="h-[78px]" />
              ))}
        </div>
      </div>

      {/* Recent activity */}
      <div>
        <SectionHeader
          title="Recent Activity"
          action={
            <button
              onClick={() => onNavigate('wallet')}
              className="flex items-center gap-0.5 text-xs transition-colors hover:opacity-80"
            >
              View all <ChevronRight className="h-3 w-3" />
            </button>
          }
        />

        {activity ? (
          <Card className="divide-y divide-border bg-card border-border overflow-hidden">
            {activity.slice(0, 3).map((a) => (
              <div
                key={a.id}
                className="flex items-center justify-between px-3 py-3 transition-colors hover:bg-secondary/30"
              >
                <div className="flex items-center gap-3">
                  <div className="h-8 w-8 rounded-full bg-secondary flex items-center justify-center">
                    <Trophy className="h-4 w-4 text-primary" />
                  </div>
                  <div>
                    <p className="text-sm leading-tight">{a.text}</p>
                    <p className="text-[11px] text-muted-foreground">{a.time}</p>
                  </div>
                </div>
                <span className="text-xs font-semibold text-emerald-400">
                  +{a.reward} NVC
                </span>
              </div>
            ))}
          </Card>
        ) : (
          <SkelCard className="h-[160px]" />
        )}
      </div>
    </ScreenShell>
  )
}
