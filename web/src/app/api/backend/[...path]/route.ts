import { NextRequest, NextResponse } from "next/server";
import { proxyApiRequest } from "@/lib/server-api";

type RouteContext = { params: Promise<{ path: string[] }> };

async function handle(request: NextRequest, context: RouteContext) {
  const { path } = await context.params;
  if (
    path.length < 2 ||
    path[0] !== "v2" ||
    path.some((part) => !/^[a-zA-Z0-9_-]+$/.test(part))
  ) {
    return NextResponse.json({ detail: "Route API invalide." }, { status: 404 });
  }
  return proxyApiRequest(request, `${path.join("/")}/`);
}

export const GET = handle;
export const POST = handle;
export const PATCH = handle;
export const PUT = handle;
export const DELETE = handle;
