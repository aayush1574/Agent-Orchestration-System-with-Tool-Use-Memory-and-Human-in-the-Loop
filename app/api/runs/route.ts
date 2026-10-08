import { desc, eq } from "drizzle-orm";
import { getDb } from "@/db";
import { decisions, runs } from "@/db/schema";

export async function GET() {
  try {
    const rows = await getDb().select().from(runs).orderBy(desc(runs.createdAt)).limit(20);
    return Response.json({ runs: rows });
  } catch (error) {
    return Response.json({ error: error instanceof Error ? error.message : "State unavailable" }, { status: 503 });
  }
}

export async function POST(request: Request) {
  try {
    const body = await request.json() as { action?: string; task?: string; runId?: number; note?: string };
    const db = getDb();
    if (body.action === "start") {
      const task = body.task?.trim();
      if (!task) return Response.json({ error: "task is required" }, { status: 400 });
      const [run] = await db.insert(runs).values({ task, status: "running", progress: 10 }).returning();
      return Response.json({ run }, { status: 201 });
    }
    if (body.action === "approve" && body.runId) {
      const [decision] = await db.insert(decisions).values({ runId: body.runId, decision: "approved", note: body.note ?? "" }).returning();
      const [run] = await db.update(runs).set({ status: "complete", progress: 100, updatedAt: new Date().toISOString() }).where(eq(runs.id, body.runId)).returning();
      return Response.json({ run, decision });
    }
    return Response.json({ error: "unsupported action" }, { status: 400 });
  } catch (error) {
    return Response.json({ error: error instanceof Error ? error.message : "State unavailable" }, { status: 503 });
  }
}
