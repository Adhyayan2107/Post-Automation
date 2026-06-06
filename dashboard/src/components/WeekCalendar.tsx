import { Post, PostStatus } from "@/lib/types"
import { format, parseISO, startOfWeek, addDays } from "date-fns"
import { CheckCircle, Clock } from "lucide-react"

const DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

function groupByDay(posts: Post[]): Record<string, Post[]> {
  const groups: Record<string, Post[]> = {}
  for (const post of posts) {
    const date = post.scheduled_at ?? post.published_at
    if (!date) continue
    const day = format(parseISO(date), "EEE")
    groups[day] = groups[day] ?? []
    groups[day].push(post)
  }
  return groups
}

export function WeekCalendar({ posts }: { posts: Post[] }) {
  const grouped = groupByDay(posts)

  return (
    <div className="grid grid-cols-7 gap-2">
      {DAYS.map(day => (
        <div key={day} className="flex flex-col gap-2">
          <div className="text-xs font-semibold text-gray-400 text-center py-1 border-b border-gray-800">
            {day}
          </div>
          {(grouped[day] ?? []).map(post => (
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
          {!(grouped[day]?.length) && (
            <div className="text-[10px] text-gray-700 text-center py-2">—</div>
          )}
        </div>
      ))}
    </div>
  )
}
