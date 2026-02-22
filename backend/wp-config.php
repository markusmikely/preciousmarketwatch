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

define('WP_CONTENT_DIR', __DIR__ . '/wp-content');
define('WP_CONTENT_URL', ($_ENV['WP_HOME'] ?? '') . '/wp-content');
define('WP_HOME',    $_ENV['WP_HOME']    ?? '');
define('WP_SITEURL', $_ENV['WP_SITEURL'] ?? '');

$table_prefix = 'wp_';

if (!defined('ABSPATH')) {
    define('ABSPATH', __DIR__ . '/');
}

require_once ABSPATH . 'wp-settings.php';
