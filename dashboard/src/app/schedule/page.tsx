import { getServerClient } from "@/lib/supabase"
import { Post, PostStatus } from "@/lib/types"
import { WeekCalendar } from "@/components/WeekCalendar"
import Link from "next/link"
import { addDays, startOfWeek, endOfDay, format } from "date-fns"

export const dynamic = "force-dynamic"

export default async function SchedulePage({
  searchParams,
}: {
  searchParams: Promise<{ week?: string }>
}) {
  const { week } = await searchParams
  const weekOffset = Math.max(-12, Math.min(12, parseInt(week ?? "0", 10) || 0))

  const now = new Date()
  const thisMonday = startOfWeek(now, { weekStartsOn: 1 })
  const weekMonday = addDays(thisMonday, weekOffset * 7)
  const weekSunday = endOfDay(addDays(weekMonday, 6))

  const weekLabel = `${format(weekMonday, "d MMM")} – ${format(weekSunday, "d MMM yyyy")}`

  const client = getServerClient()
  const [{ data }, { data: unslottedData }] = await Promise.all([
    client
      .from("posts")
      .select("*")
      .in("status", [PostStatus.SCHEDULED, PostStatus.PUBLISHED])
      .gte("scheduled_at", weekMonday.toISOString())
      .lte("scheduled_at", weekSunday.toISOString())
      .order("scheduled_at", { ascending: true }),
    client
      .from("posts")
      .select("*")
      .eq("status", PostStatus.APPROVED)
      .is("scheduled_at", null),
  ])

  const calendarPosts = (data ?? []) as Post[]
  const awaitingSlot = (unslottedData ?? []) as Post[]

  return (
    <div className="p-8">
      {/* Header */}
      <div className="mb-6 flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Schedule</h1>
          <p className="text-sm text-gray-500 mt-1">{calendarPosts.length} posts this week</p>
        </div>
        <div className="flex items-center gap-4 text-xs text-gray-600">
          <span className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-blue-400" /> scheduled
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-emerald-400" /> published
          </span>
        </div>
      </div>

      {/* Week navigator */}
      <div className="flex items-center gap-3 mb-5">
        <Link
          href={`/schedule?week=${weekOffset - 1}`}
          className="px-3 py-1.5 rounded-lg bg-white/5 hover:bg-white/10 text-gray-300 text-sm transition-colors border border-white/8"
        >
          ← Prev
        </Link>
        <div className="flex-1 text-center">
          <span className="text-sm font-semibold text-white">{weekLabel}</span>
          {weekOffset !== 0 && (
            <Link href="/schedule" className="ml-3 text-xs text-gray-600 hover:text-gray-400 underline">
              Today
            </Link>
          )}
        </div>
        <Link
          href={`/schedule?week=${weekOffset + 1}`}
          className="px-3 py-1.5 rounded-lg bg-white/5 hover:bg-white/10 text-gray-300 text-sm transition-colors border border-white/8"
        >
          Next →
        </Link>
      </div>

      {/* Calendar */}
      <WeekCalendar posts={calendarPosts} weekMonday={weekMonday} />

      {/* Awaiting slot */}
      {awaitingSlot.length > 0 && (
        <div className="mt-8">
          <div className="flex items-center gap-2 mb-3">
            <span className="w-2 h-2 rounded-full bg-emerald-500" />
            <p className="text-xs font-semibold text-gray-400 uppercase tracking-widest">
              Approved — no calendar slot yet ({awaitingSlot.length})
            </p>
          </div>
          <div className="flex flex-col gap-1.5">
            {awaitingSlot.map(post => (
              <Link
                key={post.id}
                href={`/posts/${post.id}`}
                className="flex items-center justify-between bg-white/3 hover:bg-white/6 border border-white/5 hover:border-white/10 rounded-lg px-4 py-3 transition-colors group"
              >
                <div className="min-w-0">
                  <p className="text-sm text-white group-hover:text-emerald-300 transition-colors truncate">
                    {post.title}
                  </p>
                  <p className="text-xs text-gray-600 mt-0.5">
                    {post.post_type}{post.creative_angle ? ` · ${post.creative_angle}` : ""} · {post.target_platforms.join(", ")}
                  </p>
                </div>
                <span className="text-xs text-gray-700 shrink-0 ml-4 group-hover:text-gray-500">→</span>
              </Link>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
