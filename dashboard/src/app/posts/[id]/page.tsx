import { notFound } from "next/navigation"
import Image from "next/image"
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
    <div className="max-w-3xl">
      <div className="flex items-start justify-between gap-4 mb-6">
        <h1 className="text-xl font-bold text-white leading-snug">{post.title}</h1>
        <StatusBadge status={post.status} />
      </div>

      {post.image_url && (
        <div className="relative h-56 w-full rounded-lg overflow-hidden mb-6 border border-gray-800">
          <Image src={post.image_url} alt={post.title} fill className="object-cover" unoptimized />
        </div>
      )}

      <div className="flex gap-2 flex-wrap mb-6">
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
        {post.target_subreddits.map(sub => (
          <span key={sub} className="text-xs px-2 py-0.5 rounded border bg-gray-800 text-gray-400 border-gray-700">
            {sub}
          </span>
        ))}
        {post.target_platforms.map(p => (
          <span key={p} className="text-xs px-2 py-0.5 rounded border bg-gray-800 text-gray-500 border-gray-700">
            {p}
          </span>
        ))}
      </div>

      <div className="bg-gray-900 border border-gray-800 rounded-lg p-6 mb-6">
        <pre className="whitespace-pre-wrap text-sm text-gray-300 font-sans leading-relaxed">
          {post.body}
        </pre>
      </div>

      {post.source_urls.length > 0 && (
        <div className="mb-6">
          <h2 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">Sources</h2>
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

      <div className="border-t border-gray-800 pt-6">
        <ApprovalButtons post={post} />
      </div>
    </div>
  )
}
