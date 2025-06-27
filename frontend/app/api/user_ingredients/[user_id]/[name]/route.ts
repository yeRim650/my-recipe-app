import { NextResponse } from "next/server";

const BACKEND = process.env.BACKEND_URL || "http://127.0.0.1:8000"

export async function DELETE(
  request: Request,
  { params }: { params: { user_id: string; name: string } }
) {
  const { user_id, name } = params;
  const res = await fetch(
    `${BACKEND}/api/user_ingredients/${user_id}/${encodeURIComponent(name)}`,
    { method: "DELETE" }
  );
  // 204 No Content 이므로 본문은 비워서 반환
  return new NextResponse(null, { status: res.status });
}
