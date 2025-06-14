import { NextResponse } from "next/server";

const BACKEND_URL = process.env.BACKEND_URL!;

export async function GET(
  request: Request,
  { params }: { params: { userId: string } }
) {
  const { userId } = params;
  const res = await fetch(`${BACKEND_URL}/api/user_ingredients/${userId}`);
  const data = await res.json();
  return NextResponse.json(data, { status: res.status });
}
