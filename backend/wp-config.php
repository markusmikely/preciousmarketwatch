<?php
/**
 * The base configuration for WordPress
 *
 * The wp-config.php creation script uses this file during the installation.
 * You don't have to use the web site, you can copy this file to "wp-config.php"
 * and fill in the values.
 *
 * This file contains the following configurations:
 *
 * * Database settings
 * * Secret keys
 * * Database table prefix
 * * Localized language
 * * ABSPATH
 *
 * @link https://wordpress.org/support/article/editing-wp-config-php/
 *
 * @package WordPress
 */

// ** Database settings - You can get this info from your web host ** //
/** The name of the database for WordPress */
define( 'DB_NAME', 'pmw_db' );

/** Database username */
define( 'DB_USER', 'root' );

/** Database password */
define( 'DB_PASSWORD', 'root' );

/** Database hostname */
define( 'DB_HOST', '127.0.0.1:8889' );

/** Database charset to use in creating database tables. */
define( 'DB_CHARSET', 'utf8' );

/** The database collate type. Don't change this if in doubt. */
define( 'DB_COLLATE', '' );

/**#@+
 * Authentication unique keys and salts.
 *
 * Change these to different unique phrases! You can generate these using
 * the {@link https://api.wordpress.org/secret-key/1.1/salt/ WordPress.org secret-key service}.
 *
 * You can change these at any point in time to invalidate all existing cookies.
 * This will force all users to have to log in again.
 *
 * @since 2.6.0
 */
define( 'AUTH_KEY',          'O:/_,SvlsrAuU+$D|AbV2gmpZ#*G1*Ahfj+2M;*z|x*vV{<ExCYj}eH_i[%/7w<L' );
define( 'SECURE_AUTH_KEY',   '5W BxdV^P6rKfxR._p{j3ZxN,~@TvV<w<sVj$Q`iAx5107}EBjylv%gwDD|i/Gp4' );
define( 'LOGGED_IN_KEY',     '#6m61Da<2D37@OBWC3Te>Eb;CUUy RMX>:9jL<mpl=uH],]09,B1MX.1S_vo8Uf%' );
define( 'NONCE_KEY',         'fceO)D$n~~Z:9er$b@,Xf;BeY=m,hV0%e)}A[}ZLTI&Z(nJ03l!A0q@M7pj!N5w|' );
define( 'AUTH_SALT',         'b+5E{pid]-Iaag-I.o^RSyfWbT4Yk!{N%XiJYYMyG(^fT`qVtY/q6GS*o0*2wf(j' );
define( 'SECURE_AUTH_SALT',  'q0@Z;bwn0^!oYm-_}vI_TLI!e}wV5;[AQzhYJL[4e^eFYNT7FlOW.:h90I~po|H%' );
define( 'LOGGED_IN_SALT',    '(&.UniClT |)ye[lq^,^V$2-?gczVTNDV~~&OPTDV8dL6|OJy+s2sfq](1a(8}Cm' );
define( 'NONCE_SALT',        'p6fZ@UK@&@@.>:q%:DYe@,oDYU:30kn|Zad:`vQ|/9F~kL& |2cFqU<To)s{;![G' );
define( 'WP_CACHE_KEY_SALT', '1Jb(^8fy:mnIh;?M}VY`Znv:X-!<<sOLQJw%P)WR08Z/&v=GY-7eD=OUKYcxKG{G' );


/**#@-*/

/**
 * WordPress database table prefix.
 *
 * You can have multiple installations in one database if you give each
 * a unique prefix. Only numbers, letters, and underscores please!
 */
$table_prefix = 'wp_';

/* Add any custom values between this line and the "stop editing" line. */



/**
 * For developers: WordPress debugging mode.
 *
 * Change this to true to enable the display of notices during development.
 * It is strongly recommended that plugin and theme developers use WP_DEBUG
 * in their development environments.
 *
 * For information on other constants that can be used for debugging,
 * visit the documentation.
 *
 * @link https://wordpress.org/support/article/debugging-in-wordpress/
 */
if ( ! defined( 'WP_DEBUG' ) ) {
	define( 'WP_DEBUG', false );
}

/* That's all, stop editing! Happy publishing. */

/** Absolute path to the WordPress directory. */
if ( ! defined( 'ABSPATH' ) ) {
	define( 'ABSPATH', __DIR__ . '/' );
}

/** Sets up WordPress vars and included files. */
require_once ABSPATH . 'wp-settings.php';
