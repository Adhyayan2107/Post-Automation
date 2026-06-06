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

  // Compute the Mon–Sun window for the selected week
  const now = new Date()
  const thisMonday = startOfWeek(now, { weekStartsOn: 1 })
  const weekMonday = addDays(thisMonday, weekOffset * 7)
  const weekSunday = endOfDay(addDays(weekMonday, 6))

  const weekLabel = `${format(weekMonday, "d MMM")} – ${format(weekSunday, "d MMM yyyy")}`
  const isCurrentWeek = weekOffset === 0

  const client = getServerClient()
  const { data } = await client
    .from("posts")
    .select("*")
    .in("status", [PostStatus.APPROVED, PostStatus.SCHEDULED, PostStatus.PUBLISHED])
    .gte("scheduled_at", weekMonday.toISOString())
    .lte("scheduled_at", weekSunday.toISOString())
    .order("scheduled_at", { ascending: true })

  // Also fetch approved posts with no scheduled_at (unslotted) — not filtered by date
  const { data: unslottedData } = await client
    .from("posts")
    .select("*")
    .eq("status", PostStatus.APPROVED)
    .is("scheduled_at", null)

  const weekPosts = (data ?? []) as Post[]
  const calendarPosts = weekPosts.filter(
    p => p.status === PostStatus.SCHEDULED || p.status === PostStatus.PUBLISHED
  )
  const awaitingSlot = (unslottedData ?? []) as Post[]

  const prevHref = `/schedule?week=${weekOffset - 1}`
  const nextHref = `/schedule?week=${weekOffset + 1}`

  return (
    <div>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-4">
          <h1 className="text-xl font-bold text-white">Weekly Schedule</h1>
          {!isCurrentWeek && (
            <Link
              href="/schedule"
              className="text-xs text-gray-500 hover:text-gray-300 underline transition-colors"
            >
              Back to this week
            </Link>
          )}
        </div>
        <div className="flex gap-4 text-xs text-gray-500">
          <span className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-blue-400 inline-block" /> scheduled
          </span>
          <span className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-emerald-400 inline-block" /> published
          </span>
        </div>
      </div>

      {/* Week navigator */}
      <div className="flex items-center justify-between mb-4">
        <Link
          href={prevHref}
          className="text-sm px-3 py-1.5 rounded bg-gray-800 hover:bg-gray-700 text-gray-300 transition-colors"
        >
          ← Prev
        </Link>
        <span className="text-sm font-medium text-gray-300">{weekLabel}</span>
        <Link
          href={nextHref}
          className="text-sm px-3 py-1.5 rounded bg-gray-800 hover:bg-gray-700 text-gray-300 transition-colors"
        >
          Next →
        </Link>
      </div>

      {/* Calendar */}
      {calendarPosts.length === 0 ? (
        <div className="flex flex-col items-center justify-center h-40 text-gray-600 border border-gray-800 rounded-lg mb-6">
          <p className="text-sm">No scheduled or published posts this week</p>
        </div>
      ) : (
        <WeekCalendar posts={calendarPosts} weekMonday={weekMonday} />
      )}

      {/* Unslotted approved posts */}
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
            Run <code className="text-gray-500">uv run python scripts/mini_run.py</code> to assign slots.
          </p>
        </div>
      )}
    </div>
  )
}
