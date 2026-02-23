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

//define('WP_CONTENT_DIR', dirname(__FILE__) . '/wp-content');
//define('WP_CONTENT_URL', 'https://www.preciousmarketwatch.com/wp/wp-content');

if (isset($_SERVER['HTTP_X_FORWARDED_PROTO']) && $_SERVER['HTTP_X_FORWARDED_PROTO'] == 'https') {
    $_SERVER['HTTPS'] = 'on';
}

//define('WP_HOME',    $_ENV['WP_HOME']    ?? '');
//define('WP_SITEURL', $_ENV['WP_SITEURL'] ?? '');


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
// Enable Debugging
define( 'WP_DEBUG', true );

// Log errors to /wp-content/debug.log
define( 'WP_DEBUG_LOG', true );

// Do not show errors directly on the screen (keeps the site looking "clean" while you fix it)
define( 'WP_DEBUG_DISPLAY', false );
@ini_set( 'display_errors', 0 );
require_once ABSPATH . 'wp-settings.php';
