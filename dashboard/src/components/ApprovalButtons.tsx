"use client"

import { useState, useTransition } from "react"
import { approvePost, rejectPost, editPost } from "@/actions/posts"
import { Post, PostStatus } from "@/lib/types"

export function ApprovalButtons({ post }: { post: Post }) {
  const [isPending, startTransition] = useTransition()
  const [editMode, setEditMode] = useState(false)
  const [title, setTitle] = useState(post.title)
  const [body, setBody] = useState(post.body)

  const isRejected = post.status === PostStatus.REJECTED
  const isPublished = post.status === PostStatus.PUBLISHED

  function handleApprove() {
    startTransition(async () => {
      if (editMode) await editPost(post.id, title, body)
      await approvePost(post.id)
    })
  }

  function handleReject() {
    startTransition(async () => { await rejectPost(post.id) })
  }

  if (isPublished) {
    return <p className="text-xs text-gray-600">This post has been published and cannot be changed.</p>
  }

  return (
    <div className="flex flex-col gap-4">
      {!isRejected && (
        <button
          onClick={() => setEditMode(!editMode)}
          className="self-start text-xs text-gray-500 hover:text-gray-200 underline transition-colors"
        >
          {editMode ? "Cancel edit" : "Edit before approving"}
        </button>
      )}

      {editMode && !isRejected && (
        <div className="flex flex-col gap-3">
          <div>
            <label className="block text-xs text-gray-500 mb-1.5">Title</label>
            <input
              value={title}
              onChange={e => setTitle(e.target.value)}
              className="w-full bg-white/4 border border-white/8 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-emerald-500/50 transition-colors"
            />
          </div>
          <div>
            <label className="block text-xs text-gray-500 mb-1.5">Body</label>
            <textarea
              value={body}
              onChange={e => setBody(e.target.value)}
              rows={12}
              className="w-full bg-white/4 border border-white/8 rounded-lg px-3 py-2 text-sm text-white font-mono focus:outline-none focus:border-emerald-500/50 transition-colors resize-y"
            />
          </div>
        </div>
      )}

      <div className="flex gap-3">
        <button
          onClick={handleApprove}
          disabled={isPending}
          className="flex-1 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-40 disabled:cursor-not-allowed text-white font-semibold text-sm py-2.5 rounded-lg transition-colors"
        >
          {isPending ? "Saving…" : isRejected ? "Un-reject (Approve)" : "Approve"}
        </button>
        {!isRejected && (
          <button
            onClick={handleReject}
            disabled={isPending}
            className="flex-1 bg-white/5 hover:bg-red-500/20 hover:text-red-400 disabled:opacity-40 disabled:cursor-not-allowed text-gray-300 font-semibold text-sm py-2.5 rounded-lg transition-colors border border-white/8 hover:border-red-500/30"
          >
            {isPending ? "Saving…" : "Reject"}
          </button>
        )}
      </div>

      {isRejected && (
        <p className="text-xs text-gray-700">Rejected. Click approve above to restore it.</p>
      )}
    </div>
  )
}
