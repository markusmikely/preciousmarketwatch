<?php
// Parse .env file manually — no Composer dependency needed on shared hosting
$envFile = __DIR__ . '/.env';
if (file_exists($envFile)) {
    foreach (file($envFile, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES) as $line) {
        if (strpos(trim($line), '#') === 0) continue;
        if (strpos($line, '=') === false) continue;
        [$key, $val] = array_map('trim', explode('=', $line, 2));
        $_ENV[$key] = $val;
    }
}

define('DB_NAME',     $_ENV['DB_NAME']     ?? '');
define('DB_USER',     $_ENV['DB_USER']     ?? '');
define('DB_PASSWORD', $_ENV['DB_PASSWORD'] ?? '');
define('DB_HOST',     $_ENV['DB_HOST']     ?? 'localhost');

// Metal price APIs (pmw-metals-seed plugin).
define('PMW_FREEGOLDAPI_URL',    $_ENV['PMW_FREEGOLDAPI_URL']    ?? 'https://freegoldapi.com/data/latest.json');
define('PMW_METALS_DEV_API_KEY', $_ENV['PMW_METALS_DEV_API_KEY'] ?? $_ENV['METALS_DEV_API_KEY'] ?? '');
define('PMW_METALPRICEAPI_KEY',  $_ENV['PMW_METALPRICEAPI_KEY']  ?? '');
define('PMW_SILVER_API_URL',     $_ENV['PMW_SILVER_API_URL']     ?? '');
define('PMW_PLATINUM_API_URL',   $_ENV['PMW_PLATINUM_API_URL']   ?? '');
define('PMW_PALLADIUM_API_URL',  $_ENV['PMW_PALLADIUM_API_URL']  ?? '');
define('PMW_CRON_SECRET',        $_ENV['PMW_CRON_SECRET']        ?? '');

// Newsletter (Mailchimp) — use PMW_* or legacy MAILCHIMP_* from .env
if (!defined('PMW_MAILCHIMP_API_KEY')) {
    define('PMW_MAILCHIMP_API_KEY', $_ENV['PMW_MAILCHIMP_API_KEY'] ?? $_ENV['MAILCHIMP_API_KEY'] ?? '');
}
if (!defined('PMW_MAILCHIMP_LIST_ID')) {
    define('PMW_MAILCHIMP_LIST_ID', $_ENV['PMW_MAILCHIMP_LIST_ID'] ?? $_ENV['MAILCHIMP_AUDIENCE_ID'] ?? '');
}



if (isset($_SERVER['HTTP_X_FORWARDED_PROTO']) && $_SERVER['HTTP_X_FORWARDED_PROTO'] == 'https') {
    $_SERVER['HTTPS'] = 'on';
}

// The actual folder where WP is installed (for Admin assets)
define('WP_SITEURL', 'https://www.preciousmarketwatch.com/wp');

// This is where your REACT app lives (The Root)
define('WP_HOME', 'https://www.preciousmarketwatch.com/wp');
// This forces the administration area to use SSL
define('FORCE_SSL_ADMIN', true);

$table_prefix = 'wp_';

if (!defined('ABSPATH')) {
    define('ABSPATH', __DIR__ . '/');
}

require_once ABSPATH . 'wp-settings.php';
