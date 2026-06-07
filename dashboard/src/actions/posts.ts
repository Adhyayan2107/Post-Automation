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

  const { data: row } = await client
    .from("posts")
    .select("gcal_event_id, title")
    .eq("id", id)
    .single()

  const { error } = await client
    .from("posts")
    .update({ scheduled_at: scheduledAt })
    .eq("id", id)

  if (error) throw new Error(`Failed to reschedule post: ${error.message}`)

  const gcalEventId = row?.gcal_event_id as string | null
  const title = row?.title as string | undefined

  try {
    if (gcalEventId) {
      await updateGoogleCalendarEvent(gcalEventId, scheduledAt)
    } else {
      // No event yet — create one and persist the event ID
      const newEventId = await createGoogleCalendarEvent(title ?? "EduBot Post", scheduledAt)
      if (newEventId) {
        await client.from("posts").update({ gcal_event_id: newEventId }).eq("id", id)
      }
    }
  } catch {
    // Google Calendar is best-effort; DB is already updated
  }

  revalidatePath("/schedule")
}

async function getAccessToken(): Promise<string | null> {
  const refreshToken = process.env.GOOGLE_REFRESH_TOKEN
  const clientId     = process.env.GOOGLE_CLIENT_ID
  const clientSecret = process.env.GOOGLE_CLIENT_SECRET

  if (!refreshToken || !clientId || !clientSecret) return null

  const resp = await fetch("https://oauth2.googleapis.com/token", {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams({
      grant_type:    "refresh_token",
      refresh_token: refreshToken,
      client_id:     clientId,
      client_secret: clientSecret,
    }),
  })

  if (!resp.ok) return null
  const { access_token } = await resp.json() as { access_token: string }
  return access_token
}

async function updateGoogleCalendarEvent(
  eventId: string,
  scheduledAt: string
): Promise<void> {
  const calendarId = process.env.GOOGLE_CALENDAR_ID
  if (!calendarId) return

  const token = await getAccessToken()
  if (!token) return

  const start = new Date(scheduledAt)
  const end   = new Date(start.getTime() + 60 * 60 * 1000)

  await fetch(
    `https://www.googleapis.com/calendar/v3/calendars/${encodeURIComponent(calendarId)}/events/${eventId}`,
    {
      method: "PATCH",
      headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
      body: JSON.stringify({
        start: { dateTime: start.toISOString(), timeZone: "UTC" },
        end:   { dateTime: end.toISOString(),   timeZone: "UTC" },
      }),
    }
  )
}

async function createGoogleCalendarEvent(
  title: string,
  scheduledAt: string
): Promise<string | null> {
  const calendarId = process.env.GOOGLE_CALENDAR_ID
  if (!calendarId) return null

  const token = await getAccessToken()
  if (!token) return null

  const start = new Date(scheduledAt)
  const end   = new Date(start.getTime() + 60 * 60 * 1000)

  const resp = await fetch(
    `https://www.googleapis.com/calendar/v3/calendars/${encodeURIComponent(calendarId)}/events`,
    {
      method: "POST",
      headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
      body: JSON.stringify({
        summary: `[EduBot] ${title}`,
        start: { dateTime: start.toISOString(), timeZone: "UTC" },
        end:   { dateTime: end.toISOString(),   timeZone: "UTC" },
      }),
    }
  )

  if (!resp.ok) return null
  const event = await resp.json() as { id: string }
  return event.id ?? null
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
