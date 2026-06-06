"use client"

import { Post, PostStatus } from "@/lib/types"
import { format, parseISO, addDays, isSameDay } from "date-fns"
import { CheckCircle, Clock } from "lucide-react"

const DAY_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

export function WeekCalendar({
  posts,
  weekMonday,
}: {
  posts: Post[]
  weekMonday: Date
}) {
  const days = DAY_NAMES.map((name, i) => ({
    name,
    date: addDays(weekMonday, i),
  }))

  function postsForDay(day: Date): Post[] {
    return posts.filter(post => {
      const dateStr = post.scheduled_at ?? post.published_at
      if (!dateStr) return false
      return isSameDay(parseISO(dateStr), day)
    })
  }

  return (
    <div className="grid grid-cols-7 gap-2">
      {days.map(({ name, date }) => {
        const dayPosts = postsForDay(date)
        const isToday = isSameDay(date, new Date())

        return (
          <div key={name} className="flex flex-col gap-2">
            {/* Column header */}
            <div
              className={`text-center py-1 border-b ${
                isToday ? "border-emerald-700" : "border-gray-800"
              }`}
            >
              <p className={`text-xs font-semibold ${isToday ? "text-emerald-400" : "text-gray-400"}`}>
                {name}
              </p>
              <p className={`text-[10px] ${isToday ? "text-emerald-600" : "text-gray-600"}`}>
                {format(date, "d MMM")}
              </p>
            </div>

            {/* Posts */}
            {dayPosts.map(post => (
              <a
                key={post.id}
                href={`/posts/${post.id}`}
                className="bg-gray-900 border border-gray-800 rounded p-2 hover:border-gray-600 transition-colors group"
              >
                <div className="flex items-center gap-1 mb-1">
                  {post.status === PostStatus.PUBLISHED ? (
                    <CheckCircle className="w-3 h-3 text-emerald-400 shrink-0" />
                  ) : (
                    <Clock className="w-3 h-3 text-blue-400 shrink-0" />
                  )}
                  <span className="text-[10px] text-gray-500">
                    {format(parseISO(post.scheduled_at ?? post.published_at!), "HH:mm")}
                  </span>
                </div>
                <p className="text-xs text-gray-300 leading-tight line-clamp-2 group-hover:text-white transition-colors">
                  {post.title}
                </p>
                <div className="mt-1 flex flex-wrap gap-1">
                  {post.target_platforms.map(p => (
                    <span key={p} className="text-[10px] text-gray-500">{p}</span>
                  ))}
                </div>
              </a>
            ))}

            {dayPosts.length === 0 && (
              <div className="text-[10px] text-gray-700 text-center py-2">—</div>
            )}
          </div>
        )
      })}
    </div>
  )
}
