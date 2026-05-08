"use client";
import { useEffect, useState } from "react";
import { apiFetch, loginIfNeeded } from "@/lib/api";
import { Card } from "@/components/Card";

export default function FriendsPage() {
  const [friends, setFriends] = useState<any[]>([]);
  useEffect(() => { loginIfNeeded().then(load); }, []);

  async function load() {
    try {
      const res = await apiFetch("/api/friends");
      setFriends(res.friends || []);
    } catch {}
  }

  return (
    <main className="min-h-screen p-4">
      <div className="mx-auto max-w-md space-y-4">
        <Card title="👥 Friends" subtitle="Friend cards powered by MongoDB.">
          <div className="space-y-3">
            {friends.length ? friends.map((f) => (
              <div key={f.user_id} className="rounded-2xl bg-white/10 p-4">
                <div className="font-medium">{f.display_name}</div>
                <div className="text-sm text-white/70">{f.username ? `@${f.username}` : "No username"}</div>
              </div>
            )) : <div className="text-sm text-white/70">No friends yet.</div>}
          </div>
        </Card>
      </div>
    </main>
  );
}
