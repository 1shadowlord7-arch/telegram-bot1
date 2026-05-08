"use client";
import { Card } from "@/components/Card";
export default function GamesPage() {
  return (
    <main className="min-h-screen p-4">
      <div className="mx-auto max-w-md space-y-4">
        <Card title="🕹 Play Games" subtitle="Rock Paper Scissors and Tic Tac Toe architecture is ready.">
          <div className="grid gap-3">
            <div className="rounded-2xl bg-white/10 p-4">Rock Paper Scissors</div>
            <div className="rounded-2xl bg-white/10 p-4">Tic Tac Toe</div>
          </div>
        </Card>
      </div>
    </main>
  );
}
