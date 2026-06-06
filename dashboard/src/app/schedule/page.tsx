import { getServerClient } from "@/lib/supabase"
import { Post, PostStatus } from "@/lib/types"
import { WeekCalendar } from "@/components/WeekCalendar"
import Link from "next/link"

export const dynamic = "force-dynamic"

export default async function SchedulePage() {
  const client = getServerClient()
  const { data } = await client
    .from("posts")
    .select("*")
    .in("status", [PostStatus.APPROVED, PostStatus.SCHEDULED, PostStatus.PUBLISHED])
    .order("scheduled_at", { ascending: true })

  const all = (data ?? []) as Post[]
  const calendarPosts = all.filter(p => p.status === PostStatus.SCHEDULED || p.status === PostStatus.PUBLISHED)
  const awaitingSlot = all.filter(p => p.status === PostStatus.APPROVED)

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-xl font-bold text-white">Weekly Schedule</h1>
        <div className="flex gap-4 text-xs text-gray-500">
          <span className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-blue-400 inline-block" /> scheduled
          </span>
          <span className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-emerald-400 inline-block" /> published
          </span>
        </div>
      </div>

      {calendarPosts.length === 0 ? (
        <div className="flex flex-col items-center justify-center h-40 text-gray-600 border border-gray-800 rounded-lg mb-6">
          <p className="text-sm">No scheduled or published posts this week</p>
        </div>
      ) : (
        <WeekCalendar posts={calendarPosts} />
      )}

      {awaitingSlot.length > 0 && (
        <div className="mt-8">
          <p className="text-xs text-emerald-400 font-semibold uppercase tracking-widest mb-3">
            Approved — awaiting Google Calendar slot ({awaitingSlot.length})
          </p>
          <div className="flex flex-col gap-2">
            {awaitingSlot.map(post => (
              <Link
                key={post.id}
                href={`/posts/${post.id}`}
                className="flex items-center justify-between bg-gray-900 border border-gray-800 hover:border-gray-600 rounded-lg px-4 py-3 transition-colors group"
              >
                <div>
                  <p className="text-sm text-white group-hover:text-emerald-300 transition-colors line-clamp-1">
                    {post.title}
                  </p>
                  <p className="text-xs text-gray-500 mt-0.5">
                    {post.post_type}{post.creative_angle ? ` · ${post.creative_angle}` : ""} · {post.target_platforms.join(", ")}
                  </p>
                </div>
                <span className="text-xs text-gray-600 shrink-0 ml-4">no slot yet →</span>
              </Link>
            ))}
          </div>
          <p className="text-xs text-gray-600 mt-3">
            Run the scheduler locally (<code className="text-gray-500">uv run python scripts/mini_run.py</code>) to assign Google Calendar slots.
          </p>
        </div>
      )}
    </div>
  )
}
