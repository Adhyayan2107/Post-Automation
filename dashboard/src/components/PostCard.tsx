import Link from "next/link"
import Image from "next/image"
import { Post } from "@/lib/types"
import { StatusBadge } from "./StatusBadge"

export function PostCard({ post }: { post: Post }) {
  const preview = post.body.replace(/[#*`]/g, "").slice(0, 150)

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-lg p-5 flex flex-col gap-3">
      <div className="flex items-start justify-between gap-2">
        <h2 className="text-white font-semibold text-sm leading-snug line-clamp-2">
          {post.title}
        </h2>
        <StatusBadge status={post.status} />
      </div>

      {post.image_url && (
        <div className="relative h-32 w-full rounded overflow-hidden">
          <Image
            src={post.image_url}
            alt={post.title}
            fill
            className="object-cover"
            unoptimized
          />
        </div>
      )}

      <p className="text-gray-400 text-xs leading-relaxed line-clamp-3">
        {preview}
        {post.body.length > 150 ? "…" : ""}
      </p>

      <div className="flex items-center gap-2 flex-wrap">
        <span className={`text-xs px-2 py-0.5 rounded border ${
          post.post_type === "educational"
            ? "bg-sky-500/10 text-sky-400 border-sky-500/20"
            : "bg-pink-500/10 text-pink-400 border-pink-500/20"
        }`}>
          {post.post_type}
        </span>
        {post.creative_angle && (
          <span className="text-xs px-2 py-0.5 rounded border bg-orange-500/10 text-orange-400 border-orange-500/20">
            {post.creative_angle}
          </span>
        )}
        {post.source_urls.length > 0 && (
          <span className="text-xs text-gray-500">
            {post.source_urls.length} source{post.source_urls.length !== 1 ? "s" : ""}
          </span>
        )}
      </div>

      <Link
        href={`/posts/${post.id}`}
        className="mt-auto self-start text-xs font-medium text-emerald-400 hover:text-emerald-300 transition-colors"
      >
        Review →
      </Link>
    </div>
  )
}
