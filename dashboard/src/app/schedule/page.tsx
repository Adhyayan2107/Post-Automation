import { getServerClient } from "@/lib/supabase"
import { Post, PostStatus } from "@/lib/types"
import { WeekCalendar } from "@/components/WeekCalendar"

export const dynamic = "force-dynamic"

export default async function SchedulePage() {
  const client = getServerClient()
  const { data } = await client
    .from("posts")
    .select("*")
    .in("status", [PostStatus.SCHEDULED, PostStatus.PUBLISHED])
    .order("scheduled_at", { ascending: true })

  const posts = (data ?? []) as Post[]

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

      {posts.length === 0 ? (
        <div className="flex flex-col items-center justify-center h-64 text-gray-600">
          <p className="text-lg">Nothing scheduled yet</p>
          <p className="text-sm mt-1">Approve posts to schedule them</p>
        </div>
      ) : (
        <WeekCalendar posts={posts} />
      )}
    </div>
  )
}
