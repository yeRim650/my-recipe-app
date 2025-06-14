import { NextResponse } from "next/server"

const BACKEND = process.env.BACKEND_URL || "http://127.0.0.1:8000"

export async function POST(request: Request) {
  const { user_id, name, quantity } = await request.json()
  const res = await fetch(`${BACKEND}/api/user_ingredients/`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ user_id, name, quantity }),
  })
  const data = await res.json()
  return NextResponse.json(data, { status: res.status })
}
