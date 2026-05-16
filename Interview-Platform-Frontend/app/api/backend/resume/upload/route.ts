import { NextResponse } from "next/server";
import { getBackendUrl } from "@/lib/backend";

export async function POST(request: Request) {
  const formData = await request.formData();

  const response = await fetch(`${getBackendUrl()}/resume/upload`, {
    method: "POST",
    body: formData
  });

  const payload = await response.json();

  return NextResponse.json(payload, {
    status: response.status
  });
}
