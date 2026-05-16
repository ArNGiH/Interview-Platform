import { NextResponse } from "next/server";
import { getBackendUrl } from "@/lib/backend";

export async function GET() {
  const response = await fetch(`${getBackendUrl()}/`, {
    cache: "no-store"
  });

  const payload = await response.json();

  return NextResponse.json(payload, {
    status: response.status
  });
}
