import Link from "next/link"
import Image from "next/image"
import { Post, PostStatus } from "@/lib/types"

const STATUS_DOT: Record<PostStatus, string> = {
  [PostStatus.PENDING]:   "bg-yellow-400",
  [PostStatus.APPROVED]:  "bg-emerald-400",
  [PostStatus.REJECTED]:  "bg-red-400",
  [PostStatus.SCHEDULED]: "bg-blue-400",
  [PostStatus.PUBLISHED]: "bg-purple-400",
  [PostStatus.FAILED]:    "bg-gray-400",
}

const PLATFORM_PILL: Record<string, string> = {
  reddit:  "bg-orange-500/15 text-orange-400",
  discord: "bg-indigo-500/15 text-indigo-400",
}

export function PostCard({ post }: { post: Post }) {
  const preview = post.body.replace(/[#*`>\-]/g, "").replace(/\n+/g, " ").trim().slice(0, 120)

  return (
    <Link
      href={`/posts/${post.id}`}
      className="group flex flex-col bg-white/4 hover:bg-white/6 border border-white/6 hover:border-white/12 rounded-xl overflow-hidden transition-all"
    >
      {/* Thumbnail */}
      {post.image_url ? (
        <div className="relative h-36 w-full bg-gray-900 shrink-0">
          <Image
            src={post.image_url}
            alt={post.title}
            fill
            className="object-cover opacity-80 group-hover:opacity-100 transition-opacity"
            unoptimized
          />
          {/* Status dot overlay */}
          <div className="absolute top-2 right-2">
            <span className={`block w-2.5 h-2.5 rounded-full ring-2 ring-black/40 ${STATUS_DOT[post.status]}`} />
          </div>
        </div>
      ) : (
        <div className="h-2 w-full shrink-0">
          <div className={`h-full ${STATUS_DOT[post.status]} opacity-70`} />
        </div>
      )}

      {/* Body */}
      <div className="p-4 flex flex-col gap-2 flex-1">
        {/* Type + status */}
        <div className="flex items-center gap-2">
          <span className={`text-[10px] px-1.5 py-0.5 rounded font-semibold uppercase tracking-wide ${
            post.post_type === "educational"
              ? "bg-sky-500/15 text-sky-400"
              : "bg-pink-500/15 text-pink-400"
          }`}>
            {post.post_type === "educational" ? "edu" : post.creative_angle ?? "creative"}
          </span>
          {!post.image_url && (
            <span className={`ml-auto block w-2 h-2 rounded-full ${STATUS_DOT[post.status]}`} />
          )}
        </div>

        {/* Title */}
        <h2 className="text-sm font-semibold text-white leading-snug line-clamp-2 group-hover:text-emerald-300 transition-colors">
          {post.title}
        </h2>

        {/* Preview */}
        <p className="text-xs text-gray-500 leading-relaxed line-clamp-2 flex-1">
          {preview}
        </p>

        {/* Platform pills */}
        <div className="flex items-center gap-1.5 pt-1">
          {post.target_platforms.map(p => (
            <span key={p} className={`text-[10px] px-2 py-0.5 rounded-full font-medium ${PLATFORM_PILL[p] ?? "bg-gray-500/15 text-gray-400"}`}>
              {p}
            </span>
          ))}
          <span className="ml-auto text-[10px] text-gray-600">
            {post.source_urls.length > 0 ? `${post.source_urls.length} src` : ""}
          </span>
        </div>
      </div>
    </Link>
  )
}
