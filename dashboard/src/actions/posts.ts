"use server"

import { revalidatePath } from "next/cache"
import { redirect } from "next/navigation"
import { getServiceClient } from "@/lib/supabase"

export async function approvePost(id: string): Promise<void> {
  const client = getServiceClient()
  const { error } = await client
    .from("posts")
    .update({ status: "approved" })
    .eq("id", id)

  if (error) throw new Error(`Failed to approve post: ${error.message}`)

  revalidatePath("/posts")
  redirect("/posts")
}

export async function rejectPost(id: string): Promise<void> {
  const client = getServiceClient()
  const { error } = await client
    .from("posts")
    .update({ status: "rejected" })
    .eq("id", id)

  if (error) throw new Error(`Failed to reject post: ${error.message}`)

  revalidatePath("/posts")
  redirect("/posts")
}

export async function reschedulePost(id: string, scheduledAt: string): Promise<void> {
  const client = getServiceClient()

  // Fetch current gcal_event_id
  const { data: row } = await client
    .from("posts")
    .select("gcal_event_id")
    .eq("id", id)
    .single()

  const { error } = await client
    .from("posts")
    .update({ scheduled_at: scheduledAt })
    .eq("id", id)

  if (error) throw new Error(`Failed to reschedule post: ${error.message}`)

  // Try to update Google Calendar event (silently skip if not configured)
  const gcalEventId = row?.gcal_event_id as string | null
  if (gcalEventId) {
    try {
      await updateGoogleCalendarEvent(gcalEventId, scheduledAt)
    } catch {
      // Google Calendar update is best-effort; DB is already updated
    }
  }

  revalidatePath("/schedule")
}

async function updateGoogleCalendarEvent(
  eventId: string,
  scheduledAt: string
): Promise<void> {
  const refreshToken = process.env.GOOGLE_REFRESH_TOKEN
  const clientId     = process.env.GOOGLE_CLIENT_ID
  const clientSecret = process.env.GOOGLE_CLIENT_SECRET
  const calendarId   = process.env.GOOGLE_CALENDAR_ID

  if (!refreshToken || !clientId || !clientSecret || !calendarId) return

  // Exchange refresh token for access token
  const tokenResp = await fetch("https://oauth2.googleapis.com/token", {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams({
      grant_type:    "refresh_token",
      refresh_token: refreshToken,
      client_id:     clientId,
      client_secret: clientSecret,
    }),
  })

  if (!tokenResp.ok) return
  const { access_token } = await tokenResp.json() as { access_token: string }

  const start = new Date(scheduledAt)
  const end   = new Date(start.getTime() + 60 * 60 * 1000) // +1 hour

  await fetch(
    `https://www.googleapis.com/calendar/v3/calendars/${encodeURIComponent(calendarId)}/events/${eventId}`,
    {
      method: "PATCH",
      headers: {
        Authorization:  `Bearer ${access_token}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        start: { dateTime: start.toISOString(), timeZone: "UTC" },
        end:   { dateTime: end.toISOString(),   timeZone: "UTC" },
      }),
    }
  )
}

export async function editPost(
  id: string,
  title: string,
  body: string
): Promise<void> {
  const client = getServiceClient()
  const { error } = await client
    .from("posts")
    .update({ title, body })
    .eq("id", id)

  if (error) throw new Error(`Failed to edit post: ${error.message}`)

  revalidatePath(`/posts/${id}`)
}
