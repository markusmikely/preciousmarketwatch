<?php
/**
 * Plugin Name: PMW Metals Seed
 * Description: One-time migration: creates metal_prices table and loads historical gold (FreeGoldAPI), optionally silver/platinum/palladium. Run once, then deactivate.
 * Version:     1.0.0
 * Author:      Markus Mikely
 */

if ( ! defined( 'ABSPATH' ) ) exit;

register_activation_hook( __FILE__, 'pmw_metals_seed_on_activate' );
add_action( 'admin_menu', 'pmw_metals_seed_admin_menu' );
add_action( 'admin_init', 'pmw_metals_seed_handle_action' );

function pmw_metals_seed_on_activate() {
	pmw_metals_seed_create_table();
	pmw_metals_seed_run();
}

function pmw_metals_seed_create_table() {
	global $wpdb;
	$table = $wpdb->prefix . 'metal_prices';
	$charset = $wpdb->get_charset_collate();

	$sql = "CREATE TABLE IF NOT EXISTS $table (
		id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
		metal VARCHAR(20) NOT NULL,
		date DATE NOT NULL,
		price_usd DECIMAL(12,4) NOT NULL,
		price_gbp DECIMAL(12,4) NULL,
		source VARCHAR(100) NULL,
		granularity VARCHAR(10) NULL,
		created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
		PRIMARY KEY (id),
		UNIQUE KEY uq_metal_date (metal, date)
	) $charset;";

	require_once ABSPATH . 'wp-admin/includes/upgrade.php';
	dbDelta( $sql );
}

function pmw_metals_seed_run() {
	$results = [
		'gold'      => pmw_metals_seed_load_gold(),
		'silver'    => pmw_metals_seed_load_from_url( 'silver', defined( 'PMW_SILVER_API_URL' ) ? PMW_SILVER_API_URL : '' ),
		'platinum'  => pmw_metals_seed_load_from_url( 'platinum', defined( 'PMW_PLATINUM_API_URL' ) ? PMW_PLATINUM_API_URL : '' ),
		'palladium' => pmw_metals_seed_load_from_url( 'palladium', defined( 'PMW_PALLADIUM_API_URL' ) ? PMW_PALLADIUM_API_URL : '' ),
	];

	update_option( 'pmw_metals_seed_last_run', $results );
	update_option( 'pmw_metals_seed_just_ran', true );
}

function pmw_metals_seed_load_gold() {
	$url = defined( 'PMW_FREEGOLDAPI_URL' ) ? PMW_FREEGOLDAPI_URL : 'https://freegoldapi.com/data/latest.json';
	$resp = wp_remote_get( $url, [ 'timeout' => 30 ] );

	if ( is_wp_error( $resp ) ) {
		return [ 'error' => $resp->get_error_message(), 'inserted' => 0, 'skipped' => 0 ];
	}

	$code = wp_remote_retrieve_response_code( $resp );
	if ( $code !== 200 ) {
		return [ 'error' => "HTTP $code", 'inserted' => 0, 'skipped' => 0 ];
	}

	$body = wp_remote_retrieve_body( $resp );
	$data = json_decode( $body, true );
	if ( ! is_array( $data ) ) {
		return [ 'error' => 'Invalid JSON', 'inserted' => 0, 'skipped' => 0 ];
	}

	$cutoff = '1990-01-01';
	$records = [];
	foreach ( $data as $row ) {
		if ( ! empty( $row['date'] ) && $row['date'] >= $cutoff && isset( $row['price'] ) && is_numeric( $row['price'] ) ) {
			$records[] = [
				'date'   => $row['date'],
				'price'  => (float) $row['price'],
				'source' => $row['source'] ?? 'freegoldapi',
			];
		}
	}

	return pmw_metals_seed_insert_records( 'gold', $records, 'freegoldapi' );
}

function pmw_metals_seed_load_from_url( $metal, $url ) {
	if ( empty( $url ) ) {
		return [ 'skipped' => true, 'message' => 'No API URL configured', 'inserted' => 0, 'skipped' => 0 ];
	}

	$resp = wp_remote_get( $url, [ 'timeout' => 30 ] );

	if ( is_wp_error( $resp ) ) {
		return [ 'error' => $resp->get_error_message(), 'inserted' => 0, 'skipped' => 0 ];
	}

	$code = wp_remote_retrieve_response_code( $resp );
	if ( $code !== 200 ) {
		return [ 'error' => "HTTP $code", 'inserted' => 0, 'skipped' => 0 ];
	}

	$body = wp_remote_retrieve_body( $resp );
	$data = json_decode( $body, true );

	$records = [];
	if ( is_array( $data ) ) {
		$arr = $data;
	} elseif ( isset( $data['data'] ) && is_array( $data['data'] ) ) {
		$arr = $data['data'];
	} else {
		return [ 'error' => 'Invalid JSON format (expected array or {data: [...]})', 'inserted' => 0, 'skipped' => 0 ];
	}

	$cutoff = '1990-01-01';
	foreach ( $arr as $row ) {
		if ( ! empty( $row['date'] ) && $row['date'] >= $cutoff && isset( $row['price'] ) && is_numeric( $row['price'] ) ) {
			$records[] = [
				'date'   => $row['date'],
				'price'  => (float) $row['price'],
				'source' => $row['source'] ?? $metal . '_api',
			];
		}
	}

	return pmw_metals_seed_insert_records( $metal, $records, $metal . '_api' );
}

function pmw_metals_seed_insert_records( $metal, $records, $source ) {
	global $wpdb;
	$table = $wpdb->prefix . 'metal_prices';

	if ( empty( $records ) ) {
		return [ 'inserted' => 0, 'skipped' => 0, 'message' => 'No records to insert' ];
	}

	$inserted = 0;
	$batch = 100;

	for ( $i = 0; $i < count( $records ); $i += $batch ) {
		$chunk = array_slice( $records, $i, $batch );
		$values = [];
		$placeholders = [];

		foreach ( $chunk as $r ) {
			$placeholders[] = '(%s, %s, %f, %s, %s)';
			$values[] = $metal;
			$values[] = $r['date'];
			$values[] = $r['price'];
			$values[] = $r['source'] ?? $source;
			$values[] = 'daily';
		}

		$sql = "INSERT IGNORE INTO $table (metal, date, price_usd, source, granularity) VALUES " . implode( ', ', $placeholders );
		$affected = $wpdb->query( $wpdb->prepare( $sql, array_values( $values ) ) );
		if ( $affected !== false ) {
			$inserted += $affected;
		}
	}

	$skipped = count( $records ) - $inserted;
	return [ 'inserted' => $inserted, 'skipped' => $skipped ];
}

function pmw_metals_seed_admin_menu() {
	add_management_page(
		'PMW Metals Seed',
		'Metals Seed',
		'manage_options',
		'pmw-metals-seed',
		'pmw_metals_seed_admin_page'
	);
}

function pmw_metals_seed_admin_page() {
	if ( ! current_user_can( 'manage_options' ) ) return;

	$last = get_option( 'pmw_metals_seed_last_run', [] );
	$table = $GLOBALS['wpdb']->prefix . 'metal_prices';
	$counts = [];
	foreach ( [ 'gold', 'silver', 'platinum', 'palladium' ] as $m ) {
		$counts[ $m ] = (int) $GLOBALS['wpdb']->get_var( $GLOBALS['wpdb']->prepare( "SELECT COUNT(*) FROM $table WHERE metal = %s", $m ) );
	}
	?>
	<div class="wrap">
		<h1>PMW Metals Seed</h1>
		<p>Creates <code>metal_prices</code> table and loads historical data. Gold uses FreeGoldAPI (free). Silver, platinum, palladium require API URLs in wp-config.php.</p>

		<form method="post" action="">
			<?php wp_nonce_field( 'pmw_metals_seed_run', 'pmw_metals_seed_nonce' ); ?>
			<p>
				<button type="submit" name="pmw_metals_seed" class="button button-primary">Seed / Re-run Now</button>
			</p>
		</form>

		<h2>Current counts</h2>
		<ul>
			<?php foreach ( $counts as $metal => $n ) : ?>
				<li><strong><?php echo esc_html( ucfirst( $metal ) ); ?></strong>: <?php echo (int) $n; ?> records</li>
			<?php endforeach; ?>
		</ul>

		<?php if ( ! empty( $last ) ) : ?>
		<h2>Last run</h2>
		<table class="widefat striped">
			<thead><tr><th>Metal</th><th>Result</th></tr></thead>
			<tbody>
			<?php foreach ( $last as $metal => $r ) : ?>
				<tr>
					<td><?php echo esc_html( ucfirst( $metal ) ); ?></td>
					<td>
						<?php
						if ( ! empty( $r['error'] ) ) {
							echo '<span style="color:red">Error: ' . esc_html( $r['error'] ) . '</span>';
						} elseif ( ! empty( $r['skipped'] ) && ! empty( $r['message'] ) ) {
							echo esc_html( $r['message'] );
						} else {
							echo 'Inserted: ' . (int) ( $r['inserted'] ?? 0 ) . ', Skipped: ' . (int) ( $r['skipped'] ?? 0 );
						}
						?>
					</td>
				</tr>
			<?php endforeach; ?>
			</tbody>
		</table>
		<?php endif; ?>

		<h2>Optional: Silver, Platinum, Palladium</h2>
		<p>Add to <code>wp-config.php</code> to load additional metals (URL must return JSON array of <code>{date, price, source?}</code>):</p>
		<pre>define('PMW_SILVER_API_URL', 'https://...');
define('PMW_PLATINUM_API_URL', 'https://...');
define('PMW_PALLADIUM_API_URL', 'https://...');</pre>
	</div>
	<?php
}

function pmw_metals_seed_handle_action() {
	if ( ! isset( $_POST['pmw_metals_seed'] ) || ! current_user_can( 'manage_options' ) ) return;
	if ( ! wp_verify_nonce( $_POST['pmw_metals_seed_nonce'] ?? '', 'pmw_metals_seed_run' ) ) return;

	pmw_metals_seed_create_table();
	pmw_metals_seed_run();

	wp_safe_redirect( add_query_arg( [ 'page' => 'pmw-metals-seed' ], admin_url( 'tools.php' ) ) );
	exit;
}
