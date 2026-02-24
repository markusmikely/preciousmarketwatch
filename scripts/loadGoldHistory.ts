#!/usr/bin/env npx tsx
/**
 * METAL-01 — Load Historical Gold Price Data (One-Time Migration)
 *
 * Fetches gold data from FreeGoldAPI, filters to 1990+, inserts into metal_prices (WordPress DB).
 * Idempotent: uses INSERT IGNORE.
 *
 * Run: npm run load-gold
 * Requires: DATABASE_URL or DB_* (WordPress) env vars
 */

const API_URL = process.env.FREEGOLDAPI_URL || "https://freegoldapi.com/data/latest.json";
const CUTOFF = "1990-01-01";
const METAL = "gold";

interface ApiRecord {
  date: string;
  price: number;
  source?: string;
}

async function fetchData(): Promise<ApiRecord[]> {
  const res = await fetch(API_URL);
  if (!res.ok) throw new Error(`API failed: ${res.status} ${res.statusText}`);
  const data = (await res.json()) as ApiRecord[];
  if (!Array.isArray(data)) throw new Error("API did not return an array");
  return data.filter((r) => r.date >= CUTOFF && r.date && typeof r.price === "number");
}

async function run() {
  console.log(`[${METAL}] Loading from FreeGoldAPI...`);
  const records = await fetchData();
  console.log(`[${METAL}] Fetched ${records.length} records from 1990+`);

  if (records.length === 0) {
    console.warn(`[${METAL}] No records to insert`);
    return;
  }

  const { getConnection, insertMetalRecords, countMetalRecords } = await import("./lib/db.js");
  const conn = await getConnection();

  try {
    const { inserted, skipped } = await insertMetalRecords(conn, METAL, records, "freegoldapi");
    console.log(`[${METAL}] Done. Inserted: ${inserted}, Skipped: ${skipped}`);
    const total = await countMetalRecords(conn, METAL);
    console.log(`[${METAL}] Total records: ${total}`);
  } finally {
    await conn.end();
  }
}

run().catch((err) => {
  console.error(`[${METAL}] Error:`, err.message);
  process.exit(1);
});
