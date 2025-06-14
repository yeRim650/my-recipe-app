import { NextResponse } from "next/server";

const BACKEND_URL = process.env.BACKEND_URL!;

export async function DELETE(
  request: Request,
  { params }: { params: { userId: string; name: string } }
) {
  const { userId, name } = params;
  const res = await fetch(
    `${BACKEND_URL}/api/user_ingredients/${userId}/${encodeURIComponent(name)}`,
    { method: "DELETE" }
  );
  // 204 No Content 이므로 본문은 비워서 반환
  return new NextResponse(null, { status: res.status });
}
