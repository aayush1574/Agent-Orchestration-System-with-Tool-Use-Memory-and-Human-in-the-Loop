import { desc, eq } from "drizzle-orm";
import { z } from "zod";
import { getDb } from "@/db";
import { decisions, runs } from "@/db/schema";

const MAX_BODY_BYTES = 16_384;
const noStoreHeaders = { "cache-control": "no-store" };
const requestSchema = z.discriminatedUnion("action", [
  z.object({ action: z.literal("start"), task: z.string().trim().min(10).max(10_000) }).strict(),
  z.object({ action: z.literal("approve"), runId: z.number().int().positive(), note: z.string().trim().max(2_000).optional() }).strict(),
]);

function json(body: unknown, status = 200) {
  return Response.json(body, { status, headers: noStoreHeaders });
}

export async function GET() {
  try {
    const rows = await getDb().select().from(runs).orderBy(desc(runs.createdAt)).limit(20);
    return json({ runs: rows });
  } catch (error) {
    console.error("Failed to load runs", error);
    return json({ error: "Persistence is temporarily unavailable" }, 503);
  }
}

export async function POST(request: Request) {
  const contentLength = Number(request.headers.get("content-length") ?? "0");
  if (contentLength > MAX_BODY_BYTES) return json({ error: "Request body is too large" }, 413);

  let payload: unknown;
  try {
    payload = await request.json();
  } catch {
    return json({ error: "Request body must be valid JSON" }, 400);
  }

  const parsed = requestSchema.safeParse(payload);
  if (!parsed.success) return json({ error: "Invalid request", issues: parsed.error.issues.map(issue => ({ path: issue.path.join("."), message: issue.message })) }, 400);

  try {
    const db = getDb();
    if (parsed.data.action === "start") {
      const [run] = await db.insert(runs).values({ task: parsed.data.task, status: "running", progress: 10 }).returning();
      return json({ run }, 201);
    }

    const [existing] = await db.select({ id: runs.id, status: runs.status }).from(runs).where(eq(runs.id, parsed.data.runId)).limit(1);
    if (!existing) return json({ error: "Run not found" }, 404);
    if (existing.status === "complete") return json({ error: "Run is already complete" }, 409);

    const now = new Date().toISOString();
    const [[run], [decision]] = await db.batch([
      db.update(runs).set({ status: "complete", progress: 100, updatedAt: now }).where(eq(runs.id, parsed.data.runId)).returning(),
      db.insert(decisions).values({ runId: parsed.data.runId, decision: "approved", note: parsed.data.note ?? "" }).returning(),
    ]);
    return json({ run, decision });
  } catch (error) {
    console.error("Failed to mutate run", error);
    return json({ error: "Persistence is temporarily unavailable" }, 503);
  }
}
