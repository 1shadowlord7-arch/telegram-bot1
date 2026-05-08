"use client";
import { useEffect, useState } from "react";
import { apiFetch, loginIfNeeded } from "@/lib/api";
import { Card } from "@/components/Card";

export default function GroupSettingsPage() {
  const [groupId, setGroupId] = useState("");
  const [data, setData] = useState<any>(null);
  const [query, setQuery] = useState("");

  useEffect(() => { loginIfNeeded(); }, []);

  async function loadGroup() {
    if (!groupId) return;
    const result = await apiFetch(`/api/groups/${groupId}`);
    setData(result);
  }

  async function search() {
    if (!groupId || !query) return;
    const result = await apiFetch(`/api/search`, {
      method: "POST",
      body: JSON.stringify({ group_id: Number(groupId), query }),
    });
    setData(result);
  }

  return (
    <main className="min-h-screen p-4">
      <div className="mx-auto max-w-md space-y-4">
        <Card title="⚙️ Group Settings" subtitle="Server-side only permissions.">
          <input className="w-full rounded-2xl bg-white/10 p-3 outline-none" placeholder="Group ID" value={groupId} onChange={(e) => setGroupId(e.target.value)} />
          <button className="mt-3 w-full rounded-2xl bg-white/15 p-3" onClick={loadGroup}>Load group</button>
          <input className="mt-3 w-full rounded-2xl bg-white/10 p-3 outline-none" placeholder="Search channel content" value={query} onChange={(e) => setQuery(e.target.value)} />
          <button className="mt-3 w-full rounded-2xl bg-white/15 p-3" onClick={search}>Search</button>
          <pre className="mt-4 overflow-auto rounded-2xl bg-black/20 p-3 text-xs text-white/80">{JSON.stringify(data, null, 2)}</pre>
        </Card>
      </div>
    </main>
  );
}
