'use client'

import { useEffect, useState } from 'react'
import ScreenShell from '@/components/shared/ScreenShell'
import { Card } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import { Button } from '@/components/ui/button'
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs'
import { Coins, CheckCircle2, Target, Loader2 } from 'lucide-react'
import { SkelCard } from '@/components/shared/Skeleton'
import { api } from '@/lib/api'
import { toast } from 'sonner'

function MissionItem({ m, onClaim, claiming }) {
  const progress = Number(m.progress ?? 0)
  const target = Number(m.target ?? 1)
  const pct = Math.min(100, Math.round((progress / target) * 100))
  const done = progress >= target

  return (
    <Card className="p-3.5 bg-card border-border transition-all duration-300 animate-in fade-in slide-in-from-bottom-2">
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-start gap-3 min-w-0">
          <div className="h-9 w-9 rounded-xl bg-secondary flex items-center justify-center shrink-0">
            {done ? (
              <CheckCircle2 className="h-4 w-4 text-emerald-400" />
            ) : (
              <Target className="h-4 w-4 text-primary" />
            )}
          </div>

          <div className="min-w-0">
            <p className="text-sm font-medium leading-tight truncate">{m.title}</p>
            <div className="mt-1 flex items-center gap-1 text-xs text-amber-300">
              <Coins className="h-3 w-3" /> +{m.reward} NVC
            </div>
          </div>
        </div>

        <Button
          size="sm"
          disabled={!done || claiming}
          onClick={() => onClaim(m)}
          className={
            done
              ? 'h-8 rounded-lg bg-primary text-primary-foreground hover:opacity-90'
              : 'h-8 rounded-lg'
          }
          variant={done ? 'default' : 'secondary'}
        >
          {claiming ? (
            <Loader2 className="h-3.5 w-3.5 animate-spin" />
          ) : done ? (
            'Claim'
          ) : (
            'In progress'
          )}
        </Button>
      </div>

      <div className="mt-3">
        <Progress value={pct} className="h-1.5 bg-secondary transition-all duration-700" />
        <div className="mt-1 flex justify-between text-[11px] text-muted-foreground">
          <span>
            {progress}/{target}
          </span>
          <span>{pct}%</span>
        </div>
      </div>
    </Card>
  )
}

export default function MissionsScreen() {
  const [data, setData] = useState(null)
  const [claiming, setClaiming] = useState(null)

  const load = async () => {
    try {
      const res = await api.missions()
      setData(res)
    } catch {
      // keep silent for skeleton fallback
    }
  }

  useEffect(() => {
    load()
  }, [])

  const claim = async (m) => {
    setClaiming(m.id)
    try {
      const res = await api.claim(m.id)
      toast.success(`Reward claimed: +${res.reward} NVC`)
      await load()
    } catch (e) {
      toast.error(e?.message || 'Failed to claim mission')
    } finally {
      setClaiming(null)
    }
  }

  return (
    <ScreenShell title="Missions">
      <Tabs defaultValue="daily" className="w-full">
        <TabsList className="grid grid-cols-2 bg-secondary/60 rounded-xl h-10">
          <TabsTrigger
            value="daily"
            className="rounded-lg data-[state=active]:bg-primary data-[state=active]:text-primary-foreground transition-all"
          >
            Daily
          </TabsTrigger>
          <TabsTrigger
            value="weekly"
            className="rounded-lg data-[state=active]:bg-primary data-[state=active]:text-primary-foreground transition-all"
          >
            Weekly
          </TabsTrigger>
        </TabsList>

        <TabsContent value="daily" className="mt-4 space-y-2.5">
          {!data ? (
            Array.from({ length: 3 }).map((_, i) => (
              <SkelCard key={i} className="h-[96px]" />
            ))
          ) : data.daily?.length === 0 ? (
            <p className="text-center text-sm text-muted-foreground py-8">
              All daily missions complete!
            </p>
          ) : (
            data.daily?.map((m) => (
              <MissionItem
                key={m.id}
                m={m}
                claiming={claiming === m.id}
                onClaim={claim}
              />
            ))
          )}
        </TabsContent>

        <TabsContent value="weekly" className="mt-4 space-y-2.5">
          {!data ? (
            Array.from({ length: 3 }).map((_, i) => (
              <SkelCard key={i} className="h-[96px]" />
            ))
          ) : data.weekly?.length === 0 ? (
            <p className="text-center text-sm text-muted-foreground py-8">
              All weekly missions complete!
            </p>
          ) : (
            data.weekly?.map((m) => (
              <MissionItem
                key={m.id}
                m={m}
                claiming={claiming === m.id}
                onClaim={claim}
              />
            ))
          )}
        </TabsContent>
      </Tabs>
    </ScreenShell>
  )
}
