"use client"

import { Post, PostStatus } from "@/lib/types"
import { format, parseISO, addDays, isSameDay, isToday } from "date-fns"
import { CheckCircle2, Clock3 } from "lucide-react"

const DAY_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

const PLATFORM_STYLE: Record<string, { bar: string; bg: string; text: string; badge: string }> = {
  reddit:  { bar: "bg-orange-500",  bg: "bg-orange-500/8",  text: "text-orange-300",  badge: "bg-orange-500/20 text-orange-400"  },
  discord: { bar: "bg-indigo-500",  bg: "bg-indigo-500/8",  text: "text-indigo-300",  badge: "bg-indigo-500/20 text-indigo-400"  },
}
const DEFAULT_STYLE = { bar: "bg-gray-500", bg: "bg-gray-500/8", text: "text-gray-300", badge: "bg-gray-500/20 text-gray-400" }

export function WeekCalendar({ posts, weekMonday }: { posts: Post[]; weekMonday: Date }) {
  const days = DAY_NAMES.map((name, i) => ({
    name,
    date: addDays(weekMonday, i),
  }))

  function postsForDay(day: Date) {
    return posts
      .filter(p => {
        const d = p.scheduled_at ?? p.published_at
        return d ? isSameDay(parseISO(d), day) : false
      })
      .sort((a, b) => {
        const da = a.scheduled_at ?? a.published_at ?? ""
        const db = b.scheduled_at ?? b.published_at ?? ""
        return da.localeCompare(db)
      })
  }

  return (
    <div className="grid grid-cols-7 gap-px bg-white/5 rounded-xl overflow-hidden border border-white/8">
      {days.map(({ name, date }) => {
        const today = isToday(date)
        const dayPosts = postsForDay(date)

        return (
          <div
            key={name}
            className={`flex flex-col min-h-[200px] ${today ? "bg-emerald-950/20" : "bg-[#0d0d14]"}`}
          >
            {/* Day header */}
            <div className={`px-3 py-2 border-b ${today ? "border-emerald-900/50" : "border-white/5"}`}>
              <p className={`text-xs font-semibold ${today ? "text-emerald-400" : "text-gray-500"}`}>
                {name}
              </p>
              <p className={`text-lg font-bold leading-none mt-0.5 ${today ? "text-emerald-300" : "text-gray-400"}`}>
                {format(date, "d")}
              </p>
              <p className="text-[10px] text-gray-700">{format(date, "MMM")}</p>
            </div>

            {/* Events */}
            <div className="flex flex-col gap-1.5 p-1.5 flex-1">
              {dayPosts.length === 0 ? (
                <div className="flex-1 flex items-center justify-center">
                  <span className="text-[10px] text-gray-800">—</span>
                </div>
              ) : (
                dayPosts.map(post => {
                  const platform = post.target_platforms[0] ?? "reddit"
                  const style = PLATFORM_STYLE[platform] ?? DEFAULT_STYLE
                  const timeStr = format(parseISO(post.scheduled_at ?? post.published_at!), "HH:mm")
                  const isPublished = post.status === PostStatus.PUBLISHED

                  return (
                    <a
                      key={post.id}
                      href={`/posts/${post.id}`}
                      className={`relative flex flex-col gap-0.5 rounded-md px-2 py-1.5 overflow-hidden border border-white/5 hover:border-white/15 transition-colors group ${style.bg}`}
                    >
                      {/* Left accent bar */}
                      <div className={`absolute left-0 top-0 bottom-0 w-[3px] rounded-l-md ${style.bar}`} />

                      {/* Time + status icon */}
                      <div className="flex items-center gap-1 pl-1">
                        {isPublished
                          ? <CheckCircle2 className="w-2.5 h-2.5 text-emerald-400 shrink-0" />
                          : <Clock3 className="w-2.5 h-2.5 text-gray-500 shrink-0" />
                        }
                        <span className={`text-[10px] font-bold ${style.text}`}>{timeStr}</span>
                        <span className={`ml-auto text-[9px] px-1 rounded font-medium ${style.badge}`}>
                          {platform}
                        </span>
                      </div>

                      {/* Title */}
                      <p className="text-[11px] text-gray-300 leading-tight line-clamp-2 pl-1 group-hover:text-white transition-colors">
                        {post.title}
                      </p>
                    </a>
                  )
                })
              )}
            </div>
          </div>
        )
      })}
    </div>
  )
}
