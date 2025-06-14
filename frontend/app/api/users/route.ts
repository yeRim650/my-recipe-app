// app/api/users/route.ts
import { NextResponse } from "next/server"

const BACKEND = process.env.BACKEND_URL || "http://127.0.0.1:8000"

export async function POST(request: Request) {
  const body = await request.json()
  const res = await fetch(`${BACKEND}/api/users/`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
  })
  const data = await res.json()
  return NextResponse.json(data, { status: res.status })
}
