import { getDb } from "@/db";
import { runs } from "@/db/schema";

export async function GET() {
  try {
    await getDb().select({ id: runs.id }).from(runs).limit(1);
    return Response.json({ status: "ready", database: "available" }, { headers: { "cache-control": "no-store" } });
  } catch (error) {
    console.error("Readiness check failed", error);
    return Response.json({ status: "degraded", database: "unavailable" }, { status: 503, headers: { "cache-control": "no-store" } });
  }
}
