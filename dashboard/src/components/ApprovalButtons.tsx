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
  const isReadOnly = isPublished

  function handleApprove() {
    startTransition(async () => {
      if (editMode) await editPost(post.id, title, body)
      await approvePost(post.id)
    })
  }

  function handleReject() {
    startTransition(async () => { await rejectPost(post.id) })
  }

  if (isReadOnly) {
    return (
      <p className="text-xs text-gray-500">This post has been published and cannot be changed.</p>
    )
  }

  return (
    <div className="flex flex-col gap-4">
      {!isRejected && (
        <button
          onClick={() => setEditMode(!editMode)}
          className="self-start text-xs text-gray-400 hover:text-gray-200 underline transition-colors"
        >
          {editMode ? "Cancel edit" : "Edit before approving"}
        </button>
      )}

      {editMode && !isRejected && (
        <div className="flex flex-col gap-3">
          <div>
            <label className="block text-xs text-gray-400 mb-1">Title</label>
            <input
              value={title}
              onChange={e => setTitle(e.target.value)}
              className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-sm text-white focus:outline-none focus:border-emerald-500"
            />
          </div>
          <div>
            <label className="block text-xs text-gray-400 mb-1">Body</label>
            <textarea
              value={body}
              onChange={e => setBody(e.target.value)}
              rows={12}
              className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-sm text-white font-mono focus:outline-none focus:border-emerald-500 resize-y"
            />
          </div>
        </div>
      )}

      <div className="flex gap-3">
        <button
          onClick={handleApprove}
          disabled={isPending}
          className="flex-1 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 disabled:cursor-not-allowed text-white font-semibold text-sm py-2.5 rounded transition-colors"
        >
          {isPending ? "Saving…" : isRejected ? "Un-reject (Approve)" : "Approve"}
        </button>
        {!isRejected && (
          <button
            onClick={handleReject}
            disabled={isPending}
            className="flex-1 bg-red-700 hover:bg-red-600 disabled:opacity-50 disabled:cursor-not-allowed text-white font-semibold text-sm py-2.5 rounded transition-colors"
          >
            {isPending ? "Saving…" : "Reject"}
          </button>
        )}
      </div>

      {isRejected && (
        <p className="text-xs text-gray-600">This post was rejected. You can un-reject it by approving above.</p>
      )}
    </div>
  )
}
