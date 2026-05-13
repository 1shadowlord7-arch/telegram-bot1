'use client'

import { useEffect, useState } from 'react'
import ScreenShell from '@/components/shared/ScreenShell'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { ArrowDownLeft, ArrowUpRight, Coins } from 'lucide-react'
import { SkelCard, SkelLine } from '@/components/shared/Skeleton'
import { api } from '@/lib/api'

export default function WalletScreen() {
  const [user, setUser] = useState(null)
  const [rewards, setRewards] = useState(null)

  useEffect(() => {
    api.user().then(setUser).catch(() => {})
    api.rewards().then(setRewards).catch(() => {})
  }, [])

  return (
    <ScreenShell title="Wallet">
      <Card className="relative overflow-hidden p-5 border-border bg-gradient-to-br from-secondary to-card">
        <div className="absolute -top-12 -right-12 h-44 w-44 rounded-full bg-primary/15 blur-3xl" />
        <div className="absolute -bottom-16 -left-12 h-44 w-44 rounded-full bg-accent/15 blur-3xl" />

        <div className="relative">
          <p className="text-xs uppercase tracking-wider text-muted-foreground px-1 mb-2">
            Total Balance
          </p>
          {user ? (
            <div className="mt-1 flex items-baseline gap-2 transition-all duration-500">
              <span className="text-4xl font-bold grad-text">
                {user.balance.toLocaleString()}
              </span>
              <span className="text-sm text-muted-foreground">{user.currency}</span>
            </div>
          ) : (
            <SkelLine className="h-10 w-40 mt-1" />
          )}

          <div className="mt-5 grid grid-cols-2 gap-2">
            <Button
              variant="secondary"
              className="h-10 rounded-xl gap-2 transition-transform active:scale-95"
            >
              <ArrowDownLeft className="h-4 w-4" />
              Receive
            </Button>
            <Button className="h-10 rounded-xl grad-primary text-primary-foreground hover:opacity-90 gap-2 transition-transform active:scale-95">
              <ArrowUpRight className="h-4 w-4" />
              Send
            </Button>
          </div>
        </div>
      </Card>

      <div className="mt-4">
        <p className="text-xs uppercase tracking-wider text-muted-foreground px-1 mb-2">
          Reward History
        </p>
        {rewards ? (
          <Card className="divide-y divide-border bg-card border-border overflow-hidden">
            {rewards.map((r) => (
              <div
                key={r.id}
                className="flex items-center justify-between px-3 py-3 transition-colors hover:bg-secondary/30 animate-in fade-in slide-in-from-bottom-1"
              >
                <div className="flex items-center gap-3">
                  <div className="h-9 w-9 rounded-xl bg-secondary flex items-center justify-center">
                    <Coins className="h-4 w-4 text-amber-300" />
                  </div>
                  <div>
                    <p className="text-sm font-medium leading-tight">{r.label}</p>
                    <p className="text-[11px] text-muted-foreground">{r.time}</p>
                  </div>
                </div>
                <span className="text-sm font-semibold text-emerald-400">
                  +{r.amount} NVC
                </span>
              </div>
            ))}
          </Card>
        ) : (
          <SkelCard className="h-[200px]" />
        )}
      </div>
    </ScreenShell>
  )
}
