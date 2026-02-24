/**
 * MySQL database helpers for metal_prices table.
 * Uses WordPress database (same as DATABASE_URL or DB_* env vars).
 */

import mysql from "mysql2/promise";

export interface MetalRecord {
  date: string;
  price: number;
  source?: string;
}

function getConnectionConfig(): mysql.ConnectionOptions {
  const url = process.env.DATABASE_URL;
  if (url) {
    try {
      const parsed = new URL(url);
      return {
        host: parsed.hostname,
        port: parsed.port ? parseInt(parsed.port, 10) : 3306,
        user: decodeURIComponent(parsed.username),
        password: decodeURIComponent(parsed.password),
        database: parsed.pathname?.slice(1) || undefined,
      };
    } catch {
      throw new Error("Invalid DATABASE_URL format. Use mysql://user:pass@host:3306/dbname");
    }
  }
  const host = process.env.DB_HOST || process.env.WORDPRESS_DB_HOST || "localhost";
  const user = process.env.DB_USER || process.env.WORDPRESS_DB_USER;
  const password = process.env.DB_PASSWORD || process.env.WORDPRESS_DB_PASSWORD;
  const database = process.env.DB_NAME || process.env.WORDPRESS_DB_NAME;
  if (!user || !password || !database) {
    throw new Error(
      "Set DATABASE_URL or DB_HOST, DB_USER, DB_PASSWORD, DB_NAME (or WORDPRESS_DB_*)"
    );
  }
  return { host, user, password, database, port: 3306 };
}

export async function getConnection() {
  return mysql.createConnection(getConnectionConfig());
}

const CREATE_TABLE_SQL = `
  CREATE TABLE IF NOT EXISTS metal_prices (
    id INT AUTO_INCREMENT PRIMARY KEY,
    metal VARCHAR(20) NOT NULL,
    date DATE NOT NULL,
    price_usd DECIMAL(12,4) NOT NULL,
    price_gbp DECIMAL(12,4) NULL,
    source VARCHAR(100) NULL,
    granularity VARCHAR(10) NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uq_metal_date (metal, date)
  )
`;

export async function ensureMetalPricesTable(conn: mysql.Connection) {
  await conn.query(CREATE_TABLE_SQL);
}

export async function insertMetalRecords(
  conn: mysql.Connection,
  metal: string,
  records: MetalRecord[],
  source: string
): Promise<{ inserted: number; skipped: number }> {
  if (records.length === 0) return { inserted: 0, skipped: 0 };

  await ensureMetalPricesTable(conn);

  const BATCH_SIZE = 100;
  let inserted = 0;
  let skipped = 0;

  for (let i = 0; i < records.length; i += BATCH_SIZE) {
    const batch = records.slice(i, i + BATCH_SIZE);
    const values = batch.flatMap((r) => [metal, r.date, r.price, r.source ?? source, "daily"]);
    const placeholders = batch.map(() => "(?, ?, ?, ?, ?)").join(", ");
    const sql = `INSERT IGNORE INTO metal_prices (metal, date, price_usd, source, granularity) VALUES ${placeholders}`;
    const [result] = await conn.execute(sql, values);
    const aff = (result as mysql.ResultSetHeader).affectedRows;
    inserted += aff;
    skipped += batch.length - aff;
  }

  return { inserted, skipped };
}

export async function countMetalRecords(conn: mysql.Connection, metal: string): Promise<number> {
  const [rows] = await conn.query<mysql.RowDataPacket[]>(
    "SELECT COUNT(*) AS cnt FROM metal_prices WHERE metal = ?",
    [metal]
  );
  return rows[0]?.cnt ?? 0;
}
