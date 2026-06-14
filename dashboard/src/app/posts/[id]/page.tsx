import { notFound } from "next/navigation"
import Image from "next/image"
import Link from "next/link"
import { getServerClient } from "@/lib/supabase"
import { Post } from "@/lib/types"
import { StatusBadge } from "@/components/StatusBadge"
import { ApprovalButtons } from "@/components/ApprovalButtons"

export const dynamic = "force-dynamic"

export default async function PostDetailPage({
  params,
}: {
  params: Promise<{ id: string }>
}) {
  const { id } = await params
  const client = getServerClient()
  const { data } = await client.from("posts").select("*").eq("id", id).single()

  if (!data) notFound()

  const post = data as Post

  return (
    <div className="p-8 max-w-2xl mx-auto">
      {/* Back */}
      <Link
        href="/posts"
        className="inline-flex items-center gap-1 text-xs text-gray-600 hover:text-gray-300 mb-6 transition-colors"
      >
        ← Back to posts
      </Link>

      {/* Title + status */}
      <div className="flex items-start justify-between gap-4 mb-5">
        <h1 className="text-xl font-bold text-white leading-snug">{post.title}</h1>
        <StatusBadge status={post.status} />
      </div>

      {/* Meta pills */}
      <div className="flex gap-2 flex-wrap mb-5">
        <span className={`text-xs px-2 py-1 rounded-md font-medium ${
          post.post_type === "educational"
            ? "bg-sky-500/15 text-sky-400"
            : "bg-pink-500/15 text-pink-400"
        }`}>
          {post.post_type}
        </span>
        {post.creative_angle && (
          <span className="text-xs px-2 py-1 rounded-md font-medium bg-orange-500/15 text-orange-400">
            {post.creative_angle}
          </span>
        )}
        {post.target_platforms.map(p => (
          <span key={p} className={`text-xs px-2 py-1 rounded-md font-medium ${
            p === "reddit" ? "bg-orange-500/15 text-orange-400" : "bg-indigo-500/15 text-indigo-400"
          }`}>
            {p}
          </span>
        ))}
        {post.target_subreddits.map(sub => (
          <span key={sub} className="text-xs px-2 py-1 rounded-md bg-white/5 text-gray-400">
            {sub}
          </span>
        ))}
      </div>

      {/* Image */}
      {post.image_url && (
        <div className="relative h-52 w-full rounded-xl overflow-hidden mb-5 border border-white/8">
          <Image src={post.image_url} alt={post.title} fill className="object-cover" unoptimized />
        </div>
      )}

      {/* Sources */}
      {post.source_urls.length > 0 && (
        <div className="mb-5">
          <p className="text-[10px] font-semibold text-gray-600 uppercase tracking-widest mb-2">Sources</p>
          <ul className="flex flex-col gap-1">
            {post.source_urls.map(url => (
              <li key={url}>
                <a
                  href={url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-xs text-blue-400 hover:text-blue-300 underline break-all"
                >
                  {url}
                </a>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Actions */}
      <div className="border-t border-white/6 pt-5">
        <ApprovalButtons post={post} />
      </div>
    </div>
  )
}
