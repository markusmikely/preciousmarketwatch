#!/usr/bin/env npx tsx
/**
 * Load Historical Palladium Price Data (One-Time Migration)
 *
 * Fetches palladium data from configured API, filters to 1990+, inserts into metal_prices (WordPress DB).
 * Idempotent: uses INSERT IGNORE.
 *
 * Run: npm run load-palladium
 * Requires: PALLADIUM_API_URL (returns [{date, price, source?}]) and DATABASE_URL or DB_*
 *
 * Note: Set PALLADIUM_API_URL to an API that returns the same format as FreeGoldAPI.
 */

const API_URL = process.env.PALLADIUM_API_URL;
const CUTOFF = "1990-01-01";
const METAL = "palladium";

interface ApiRecord {
  date: string;
  price: number;
  source?: string;
}

async function fetchData(): Promise<ApiRecord[]> {
  if (!API_URL) {
    console.log(`[${METAL}] PALLADIUM_API_URL not set — skipping`);
    process.exit(0);
  }
  const res = await fetch(API_URL);
  if (!res.ok) throw new Error(`API failed: ${res.status} ${res.statusText}`);
  const data = (await res.json()) as ApiRecord[] | { data?: ApiRecord[] };
  const arr = Array.isArray(data) ? data : (data as { data?: ApiRecord[] }).data;
  if (!Array.isArray(arr)) throw new Error("API did not return an array of {date, price}");
  return arr.filter((r) => r.date >= CUTOFF && r.date && typeof r.price === "number");
}

async function run() {
  console.log(`[${METAL}] Loading...`);
  const records = await fetchData();
  console.log(`[${METAL}] Fetched ${records.length} records from 1990+`);

  if (records.length === 0) {
    console.warn(`[${METAL}] No records to insert`);
    return;
  }

  const { getConnection, insertMetalRecords, countMetalRecords } = await import("./lib/db.js");
  const conn = await getConnection();

  try {
    const { inserted, skipped } = await insertMetalRecords(conn, METAL, records, "palladium_api");
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
