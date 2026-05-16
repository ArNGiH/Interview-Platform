import { NextResponse } from "next/server";
import { proxyJsonRequest } from "@/lib/backend";

export async function POST(request: Request) {
  const payload = await request.json();

  const response = await proxyJsonRequest("/interview/chat", {
    method: "POST",
    body: JSON.stringify(payload)
  });

  const responsePayload = await response.json();

  return NextResponse.json(responsePayload, {
    status: response.status
  });
}
