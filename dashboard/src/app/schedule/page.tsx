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
  const { data } = await client
    .from("posts")
    .select("*")
    .in("status", [PostStatus.PENDING, PostStatus.APPROVED, PostStatus.SCHEDULED, PostStatus.PUBLISHED])
    .not("scheduled_at", "is", null)
    .gte("scheduled_at", weekMonday.toISOString())
    .lte("scheduled_at", weekSunday.toISOString())
    .order("scheduled_at", { ascending: true })

  const calendarPosts = (data ?? []) as Post[]

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
            <span className="w-2 h-2 rounded-full bg-yellow-400" /> pending approval
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-emerald-400" /> approved
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-purple-400" /> published
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
      <WeekCalendar posts={calendarPosts} weekMonday={weekMonday} weekOffset={weekOffset} />

    </div>
  )
}
