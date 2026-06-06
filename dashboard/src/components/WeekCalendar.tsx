"use client"

import { useState } from "react"
import Image from "next/image"
import { Post, PostStatus } from "@/lib/types"
import { format, parseISO, addDays, isSameDay, isToday } from "date-fns"
import { CheckCircle2, Clock3, X, ExternalLink } from "lucide-react"

const DAY_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

// Left accent bar = platform (WHERE it posts)
const PLATFORM_BAR: Record<string, string> = {
  reddit:  "bg-orange-500",
  discord: "bg-indigo-500",
}

// Background tint + text = status (current STATE)
const STATUS_STYLE: Record<PostStatus, { bg: string; ring: string; dot: string; label: string }> = {
  [PostStatus.APPROVED]:  { bg: "bg-emerald-500/10",  ring: "border-emerald-500/20", dot: "bg-emerald-400",  label: "approved"  },
  [PostStatus.SCHEDULED]: { bg: "bg-blue-500/10",     ring: "border-blue-500/20",    dot: "bg-blue-400",     label: "scheduled" },
  [PostStatus.PUBLISHED]: { bg: "bg-purple-500/10",   ring: "border-purple-500/20",  dot: "bg-purple-400",   label: "published" },
  [PostStatus.PENDING]:   { bg: "bg-yellow-500/10",   ring: "border-yellow-500/20",  dot: "bg-yellow-400",   label: "pending"   },
  [PostStatus.REJECTED]:  { bg: "bg-red-500/10",      ring: "border-red-500/20",     dot: "bg-red-400",      label: "rejected"  },
  [PostStatus.FAILED]:    { bg: "bg-gray-500/10",     ring: "border-gray-500/20",    dot: "bg-gray-400",     label: "failed"    },
}

function PostModal({ post, onClose }: { post: Post; onClose: () => void }) {
  const timeStr = post.scheduled_at ?? post.published_at
  const preview = post.body.replace(/[#*`>\-]/g, "").replace(/\n+/g, " ").trim()
  const statusStyle = STATUS_STYLE[post.status]

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
      onClick={onClose}
    >
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" />

      {/* Panel */}
      <div
        className="relative z-10 w-full max-w-lg bg-[#111118] border border-white/10 rounded-2xl shadow-2xl overflow-hidden"
        onClick={e => e.stopPropagation()}
      >
        {/* Image */}
        {post.image_url && (
          <div className="relative h-44 w-full bg-gray-900">
            <Image src={post.image_url} alt={post.title} fill className="object-cover opacity-80" unoptimized />
            <div className="absolute inset-0 bg-gradient-to-t from-[#111118] via-transparent to-transparent" />
          </div>
        )}

        <div className="p-5">
          {/* Header */}
          <div className="flex items-start justify-between gap-3 mb-3">
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-1.5 flex-wrap">
                <span className={`inline-flex items-center gap-1 text-[10px] font-semibold px-2 py-0.5 rounded-full ${statusStyle.bg} border ${statusStyle.ring}`}>
                  <span className={`w-1.5 h-1.5 rounded-full ${statusStyle.dot}`} />
                  {statusStyle.label}
                </span>
                <span className={`text-[10px] px-2 py-0.5 rounded-full font-medium ${
                  post.post_type === "educational" ? "bg-sky-500/15 text-sky-400" : "bg-pink-500/15 text-pink-400"
                }`}>
                  {post.post_type === "educational" ? "edu" : post.creative_angle ?? "creative"}
                </span>
              </div>
              <h2 className="text-base font-bold text-white leading-snug">{post.title}</h2>
            </div>
            <button
              onClick={onClose}
              className="shrink-0 p-1.5 rounded-lg hover:bg-white/8 text-gray-500 hover:text-gray-200 transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          {/* Time + platforms */}
          <div className="flex items-center gap-2 mb-4 flex-wrap">
            {timeStr && (
              <span className="text-xs text-gray-400 font-medium">
                {format(parseISO(timeStr), "EEE d MMM · HH:mm")} UTC
              </span>
            )}
            <span className="text-gray-700">·</span>
            {post.target_platforms.map(p => (
              <span key={p} className={`text-[10px] px-2 py-0.5 rounded-full font-medium ${
                p === "reddit" ? "bg-orange-500/15 text-orange-400" : "bg-indigo-500/15 text-indigo-400"
              }`}>
                {p}
              </span>
            ))}
          </div>

          {/* Body preview */}
          <div className="bg-white/3 border border-white/6 rounded-xl p-4 mb-4 max-h-40 overflow-y-auto">
            <p className="text-xs text-gray-400 leading-relaxed whitespace-pre-wrap">{preview.slice(0, 600)}{preview.length > 600 ? "…" : ""}</p>
          </div>

          {/* Actions */}
          <a
            href={`/posts/${post.id}`}
            className="flex items-center justify-center gap-2 w-full bg-white/5 hover:bg-white/10 border border-white/8 hover:border-white/15 text-gray-300 hover:text-white text-sm font-medium py-2.5 rounded-lg transition-colors"
          >
            View full post
            <ExternalLink className="w-3.5 h-3.5" />
          </a>
        </div>
      </div>
    </div>
  )
}

export function WeekCalendar({ posts, weekMonday }: { posts: Post[]; weekMonday: Date }) {
  const [selected, setSelected] = useState<Post | null>(null)

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
    <>
      <div className="grid grid-cols-7 gap-px bg-white/5 rounded-xl overflow-hidden border border-white/8">
        {days.map(({ name, date }) => {
          const today = isToday(date)
          const dayPosts = postsForDay(date)

          return (
            <div
              key={name}
              className={`flex flex-col min-h-[220px] ${today ? "bg-emerald-950/20" : "bg-[#0d0d14]"}`}
            >
              {/* Day header */}
              <div className={`px-3 py-2 border-b ${today ? "border-emerald-900/50" : "border-white/5"}`}>
                <p className={`text-xs font-semibold ${today ? "text-emerald-400" : "text-gray-500"}`}>{name}</p>
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
                    const bar = PLATFORM_BAR[platform] ?? "bg-gray-500"
                    const statusStyle = STATUS_STYLE[post.status] ?? STATUS_STYLE[PostStatus.SCHEDULED]
                    const timeStr = format(parseISO(post.scheduled_at ?? post.published_at!), "HH:mm")
                    const isPublished = post.status === PostStatus.PUBLISHED

                    return (
                      <button
                        key={post.id}
                        onClick={() => setSelected(post)}
                        className={`relative w-full text-left flex flex-col gap-0.5 rounded-md px-2 py-1.5 overflow-hidden border hover:brightness-125 transition-all group cursor-pointer ${statusStyle.bg} ${statusStyle.ring}`}
                      >
                        {/* Left accent bar = platform */}
                        <div className={`absolute left-0 top-0 bottom-0 w-[3px] ${bar}`} />

                        {/* Time + icon */}
                        <div className="flex items-center gap-1 pl-1">
                          {isPublished
                            ? <CheckCircle2 className="w-2.5 h-2.5 text-purple-400 shrink-0" />
                            : <Clock3 className="w-2.5 h-2.5 text-gray-500 shrink-0" />
                          }
                          <span className="text-[10px] font-bold text-gray-300">{timeStr}</span>
                          <span className={`ml-auto text-[9px] px-1 rounded font-semibold ${statusStyle.dot} bg-current/20`}
                            style={{ color: "inherit" }}
                          >
                            <span className={`inline-block w-1.5 h-1.5 rounded-full ${statusStyle.dot}`} />
                          </span>
                        </div>

                        {/* Title */}
                        <p className="text-[11px] text-gray-300 leading-tight line-clamp-2 pl-1 group-hover:text-white transition-colors">
                          {post.title}
                        </p>
                      </button>
                    )
                  })
                )}
              </div>
            </div>
          )
        })}
      </div>

      {/* Preview modal */}
      {selected && <PostModal post={selected} onClose={() => setSelected(null)} />}
    </>
  )
}
