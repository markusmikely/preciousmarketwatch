-- METAL-01: metal_prices table (MySQL / WordPress)
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
);
