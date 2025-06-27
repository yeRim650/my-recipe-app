import { NextResponse } from "next/server"

const BACKEND = process.env.BACKEND_URL || "http://127.0.0.1:8000"

export async function GET(
  request: Request,
  { params }: { params: { user_id: string } }
) {
  const { user_id } = params;
  const res = await fetch(
    `${BACKEND}/api/user_ingredients/${user_id}`,
    { method: "GET" }
  )
  const data = await res.json()
  return NextResponse.json(data, { status: res.status })
}