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
add_action( 'rest_api_init', 'pmw_metals_seed_register_rest_routes' );

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
		'silver'    => pmw_metals_seed_load_metals_dev( 'silver' ),
		'platinum'  => pmw_metals_seed_load_metals_dev( 'platinum' ),
		'palladium' => pmw_metals_seed_load_metals_dev( 'palladium' ),
	];

	// Fallback: optional URL-based loaders when Metals.dev key not set
	$metals_dev_key = defined( 'PMW_METALS_DEV_API_KEY' ) ? PMW_METALS_DEV_API_KEY : '';
	if ( empty( $metals_dev_key ) ) {
		if ( defined( 'PMW_SILVER_API_URL' ) && PMW_SILVER_API_URL ) {
			$results['silver'] = pmw_metals_seed_load_from_url( 'silver', PMW_SILVER_API_URL );
		}
		if ( defined( 'PMW_PLATINUM_API_URL' ) && PMW_PLATINUM_API_URL ) {
			$results['platinum'] = pmw_metals_seed_load_from_url( 'platinum', PMW_PLATINUM_API_URL );
		}
		if ( defined( 'PMW_PALLADIUM_API_URL' ) && PMW_PALLADIUM_API_URL ) {
			$results['palladium'] = pmw_metals_seed_load_from_url( 'palladium', PMW_PALLADIUM_API_URL );
		}
	}

	update_option( 'pmw_metals_seed_last_run', $results );
	update_option( 'pmw_metals_seed_just_ran', true );
}

/**
 * Load silver, platinum, or palladium from Metals.dev timeseries API.
 * Paginates 30 days per request (API limit). GBP from currencies when available, else 0.79 approximation.
 */
function pmw_metals_seed_load_metals_dev( $metal ) {
	$key = defined( 'PMW_METALS_DEV_API_KEY' ) ? PMW_METALS_DEV_API_KEY : '';
	if ( empty( $key ) ) {
		return [ 'skipped' => true, 'message' => 'PMW_METALS_DEV_API_KEY not set', 'inserted' => 0, 'skipped' => 0 ];
	}

	$cutoff   = '1990-01-01';
	$end_date = gmdate( 'Y-m-d', strtotime( '-1 day' ) );
	$records  = [];
	$source   = 'metalsdev';
	$gbp_note = ' (GBP approx 0.79 when FX unavailable)';

	$start = $cutoff;
	while ( $start <= $end_date ) {
		$end = gmdate( 'Y-m-d', min( strtotime( $start . ' +29 days' ), strtotime( $end_date ) ) );
		$url = add_query_arg( [
			'api_key'    => $key,
			'start_date' => $start,
			'end_date'   => $end,
		], 'https://api.metals.dev/v1/timeseries' );

		$resp = wp_remote_get( $url, [ 'timeout' => 30 ] );
		if ( is_wp_error( $resp ) ) {
			return [ 'error' => $resp->get_error_message(), 'inserted' => 0, 'skipped' => 0 ];
		}
		if ( wp_remote_retrieve_response_code( $resp ) !== 200 ) {
			return [ 'error' => 'Metals.dev HTTP ' . wp_remote_retrieve_response_code( $resp ), 'inserted' => 0, 'skipped' => 0 ];
		}

		$data = json_decode( wp_remote_retrieve_body( $resp ), true );
		if ( empty( $data['status'] ) || $data['status'] !== 'success' || empty( $data['rates'] ) ) {
			$msg = isset( $data['error_message'] ) ? $data['error_message'] : 'Invalid Metals.dev response';
			return [ 'error' => $msg, 'inserted' => 0, 'skipped' => 0 ];
		}

		foreach ( $data['rates'] as $date => $row ) {
			if ( $date < $cutoff ) continue;
			$m = isset( $row['metals'][ $metal ] ) ? (float) $row['metals'][ $metal ] : null;
			if ( $m === null || $m <= 0 ) continue;

			if ( ! empty( $row['currencies']['GBP'] ) && (float) $row['currencies']['GBP'] > 0 ) {
				$gbp   = $m / (float) $row['currencies']['GBP'];
				$src   = $source;
			} else {
				$gbp   = $m * 0.79;
				$src   = $source . $gbp_note;
			}
			$records[] = [
				'date'      => $date,
				'price'     => $m,
				'price_gbp' => $gbp,
				'source'    => $src,
			];
		}

		$start = gmdate( 'Y-m-d', strtotime( $end . ' +1 day' ) );
		if ( $start > $end_date ) break;
	}

	return pmw_metals_seed_insert_records_with_gbp( $metal, $records, $source );
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
	$with_gbp = array_map( function ( $r ) {
		$r['price_gbp'] = null;
		return $r;
	}, $records );
	return pmw_metals_seed_insert_records_with_gbp( $metal, $with_gbp, $source );
}

function pmw_metals_seed_insert_records_with_gbp( $metal, $records, $source ) {
	global $wpdb;
	$table = $wpdb->prefix . 'metal_prices';

	if ( empty( $records ) ) {
		return [ 'inserted' => 0, 'skipped' => 0, 'message' => 'No records to insert' ];
	}

	$inserted = 0;
	$batch    = 100;

	for ( $i = 0; $i < count( $records ); $i += $batch ) {
		$chunk        = array_slice( $records, $i, $batch );
		$values       = [];
		$placeholders = [];

		foreach ( $chunk as $r ) {
			$has_gbp = isset( $r['price_gbp'] ) && $r['price_gbp'] !== null && $r['price_gbp'] !== '';
			if ( $has_gbp ) {
				$placeholders[] = '(%s, %s, %f, %f, %s, %s)';
				$values[]      = $metal;
				$values[]      = $r['date'];
				$values[]      = (float) $r['price'];
				$values[]      = (float) $r['price_gbp'];
				$values[]      = $r['source'] ?? $source;
				$values[]      = 'daily';
			} else {
				$placeholders[] = '(%s, %s, %f, NULL, %s, %s)';
				$values[]      = $metal;
				$values[]      = $r['date'];
				$values[]      = (float) $r['price'];
				$values[]      = $r['source'] ?? $source;
				$values[]      = 'daily';
			}
		}

		$sql      = "INSERT IGNORE INTO $table (metal, date, price_usd, price_gbp, source, granularity) VALUES " . implode( ', ', $placeholders );
		$affected = $wpdb->query( $wpdb->prepare( $sql, array_values( $values ) ) );
		if ( $affected !== false ) {
			$inserted += $affected;
		}
	}

	$skipped = count( $records ) - $inserted;
	return [ 'inserted' => $inserted, 'skipped' => $skipped ];
}

function pmw_metals_seed_admin_menu() {
	$hook = add_management_page(
		'PMW Metals Seed',
		'Metals Seed',
		'manage_options',
		'pmw-metals-seed',
		'pmw_metals_seed_admin_page'
	);
	add_action( "load-{$hook}", 'pmw_metals_seed_admin_scripts' );
}

function pmw_metals_seed_admin_scripts() {
	wp_enqueue_script(
		'chartjs',
		'https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js',
		[],
		'4.4.1',
		true
	);
}

function pmw_metals_seed_admin_page() {
	if ( ! current_user_can( 'manage_options' ) ) return;

	global $wpdb;
	$table = $wpdb->prefix . 'metal_prices';
	$last = get_option( 'pmw_metals_seed_last_run', [] );
	$counts = [];
	$latest = [];
	foreach ( [ 'gold', 'silver', 'platinum', 'palladium' ] as $m ) {
		$counts[ $m ] = (int) $wpdb->get_var( $wpdb->prepare( "SELECT COUNT(*) FROM $table WHERE metal = %s", $m ) );
		$row = $wpdb->get_row( $wpdb->prepare(
			"SELECT date, price_usd, price_gbp FROM $table WHERE metal = %s ORDER BY date DESC LIMIT 1",
			$m
		), ARRAY_A );
		$latest[ $m ] = $row;
	}

	$rows = $wpdb->get_results(
		"SELECT metal, date, price_usd FROM $table WHERE date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY) ORDER BY date ASC",
		ARRAY_A
	);
	$by_metal = [ 'gold' => [], 'silver' => [], 'platinum' => [], 'palladium' => [] ];
	$all_dates = [];
	foreach ( $rows as $r ) {
		$all_dates[ $r['date'] ] = true;
		$by_metal[ $r['metal'] ][ $r['date'] ] = (float) $r['price_usd'];
	}
	$labels = array_keys( $all_dates );
	sort( $labels );
	$chart_datasets = [];
	$colors = [ 'gold' => [ '#d4a84b', 'rgba(212,168,75,0.1)' ], 'silver' => [ '#94a3b8', 'rgba(148,163,184,0.1)' ], 'platinum' => [ '#0d9488', 'rgba(13,148,136,0.1)' ], 'palladium' => [ '#ea580c', 'rgba(234,88,12,0.1)' ] ];
	foreach ( [ 'gold', 'silver', 'platinum', 'palladium' ] as $m ) {
		$chart_datasets[] = [
			'label' => ucfirst( $m ),
			'data'  => array_map( function ( $d ) use ( $by_metal, $m ) { return $by_metal[ $m ][ $d ] ?? null; }, $labels ),
			'borderColor' => $colors[ $m ][0],
			'backgroundColor' => $colors[ $m ][1],
			'fill' => true,
			'tension' => 0.2,
		];
	}
	?>
	<div class="wrap">
		<h1>PMW Metals Seed</h1>
		<p>Creates <code>metal_prices</code> table and loads historical data. Gold: FreeGoldAPI. Silver, platinum, palladium: Metals.dev (set <code>PMW_METALS_DEV_API_KEY</code> in .env).</p>

		<form method="post" action="">
			<?php wp_nonce_field( 'pmw_metals_seed_run', 'pmw_metals_seed_nonce' ); ?>
			<p>
				<button type="submit" name="pmw_metals_seed" class="button button-primary">Seed / Re-run Now</button>
			</p>
		</form>

		<h2>Current prices (latest in database)</h2>
		<table class="widefat striped" style="max-width: 600px;">
			<thead><tr><th>Metal</th><th>Date</th><th>USD</th><th>GBP</th></tr></thead>
			<tbody>
			<?php foreach ( [ 'gold', 'silver', 'platinum', 'palladium' ] as $m ) : $r = $latest[ $m ] ?? null; ?>
				<tr>
					<td><strong><?php echo esc_html( ucfirst( $m ) ); ?></strong></td>
					<td><?php echo $r ? esc_html( $r['date'] ) : '—'; ?></td>
					<td><?php echo $r ? '$' . esc_html( number_format( (float) $r['price_usd'], 2 ) ) : '—'; ?></td>
					<td><?php echo ( $r && $r['price_gbp'] ) ? '£' . esc_html( number_format( (float) $r['price_gbp'], 2 ) ) : '—'; ?></td>
				</tr>
			<?php endforeach; ?>
			</tbody>
		</table>
		<p class="description">Also shown on <a href="<?php echo esc_url( admin_url( 'admin.php?page=market_data' ) ); ?>">Market Data</a> (updated by daily cron).</p>

		<h2>30-day price chart</h2>
		<div style="max-width: 800px; height: 300px;">
			<canvas id="pmw-metals-chart"></canvas>
		</div>
		<script>
		document.addEventListener('DOMContentLoaded', function() {
			if (typeof Chart === 'undefined') return;
			var ctx = document.getElementById('pmw-metals-chart');
			if (!ctx) return;
			var labels = <?php echo wp_json_encode( $labels ); ?>;
			var datasets = <?php echo wp_json_encode( $chart_datasets ); ?>;
			if (labels.length === 0) { ctx.parentNode.innerHTML = '<p>No data to display. Run Seed first.</p>'; return; }
			new Chart(ctx, {
				type: 'line',
				data: { labels: labels, datasets: datasets },
				options: { responsive: true, maintainAspectRatio: false, scales: { y: { beginAtZero: false } } }
			});
		});
		</script>

		<h2>Record counts</h2>
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

		<h2>Configuration</h2>
		<p>Set in <code>.env</code> or wp-config: <code>PMW_METALS_DEV_API_KEY</code> for silver/platinum/palladium from Metals.dev. Optional fallback URLs: <code>PMW_SILVER_API_URL</code>, <code>PMW_PLATINUM_API_URL</code>, <code>PMW_PALLADIUM_API_URL</code>.</p>
	</div>
	<?php
}

/**
 * METAL-03 — Daily price update cron endpoint.
 * POST /wp-json/pmw/v1/cron/price-update
 * Auth: Authorization: Bearer {PMW_CRON_SECRET}
 */
function pmw_metals_seed_register_rest_routes() {
	register_rest_route( 'pmw/v1', '/cron/price-update', [
		'methods'             => 'POST',
		'callback'            => 'pmw_metals_seed_cron_price_update',
		'permission_callback' => 'pmw_metals_seed_cron_permission',
	] );
}

function pmw_metals_seed_cron_permission( $request ) {
	$secret = defined( 'PMW_CRON_SECRET' ) ? PMW_CRON_SECRET : '';
	if ( empty( $secret ) ) {
		return new WP_Error( 'no_secret', 'CRON_SECRET not configured', [ 'status' => 500 ] );
	}
	$auth = $request->get_header( 'Authorization' );
	$token = preg_replace( '/^Bearer\s+/i', '', $auth ?? '' );
	if ( $token !== $secret ) {
		return new WP_Error( 'unauthorized', 'Invalid or missing token', [ 'status' => 401 ] );
	}
	return true;
}

function pmw_metals_seed_cron_price_update( $request ) {
	$key = defined( 'PMW_METALS_DEV_API_KEY' ) ? PMW_METALS_DEV_API_KEY : '';
	if ( empty( $key ) ) {
		return new WP_REST_Response( [ 'success' => false, 'error' => 'PMW_METALS_DEV_API_KEY not set' ], 500 );
	}

	$url = add_query_arg( [ 'api_key' => $key, 'currency' => 'USD', 'unit' => 'toz' ], 'https://api.metals.dev/v1/latest' );
	$resp = wp_remote_get( $url, [ 'timeout' => 15 ] );
	if ( is_wp_error( $resp ) ) {
		return new WP_REST_Response( [ 'success' => false, 'error' => $resp->get_error_message() ], 502 );
	}
	if ( wp_remote_retrieve_response_code( $resp ) !== 200 ) {
		return new WP_REST_Response( [ 'success' => false, 'error' => 'Metals.dev HTTP ' . wp_remote_retrieve_response_code( $resp ) ], 502 );
	}

	$data = json_decode( wp_remote_retrieve_body( $resp ), true );
	if ( empty( $data['metals'] ) ) {
		return new WP_REST_Response( [ 'success' => false, 'error' => 'Invalid Metals.dev response' ], 502 );
	}

	$usd_gbp = 0.79;
	$fx_resp = wp_remote_get( 'https://api.exchangerate-api.com/v4/latest/USD', [ 'timeout' => 10 ] );
	if ( ! is_wp_error( $fx_resp ) && wp_remote_retrieve_response_code( $fx_resp ) === 200 ) {
		$fx = json_decode( wp_remote_retrieve_body( $fx_resp ), true );
		if ( ! empty( $fx['rates']['GBP'] ) ) {
			$usd_gbp = 1 / (float) $fx['rates']['GBP'];
		}
	}

	$today = gmdate( 'Y-m-d' );
	$metals_map = [ 'gold' => 'gold', 'silver' => 'silver', 'platinum' => 'platinum', 'palladium' => 'palladium' ];
	$results = [];
	global $wpdb;
	$table = $wpdb->prefix . 'metal_prices';

	foreach ( $metals_map as $slug => $metal ) {
		$price_usd = isset( $data['metals'][ $metal ] ) ? (float) $data['metals'][ $metal ] : null;
		if ( $price_usd === null || $price_usd <= 0 ) continue;

		$price_gbp = round( $price_usd * $usd_gbp, 4 );
		$wpdb->replace( $table, [
			'metal'       => $metal,
			'date'        => $today,
			'price_usd'   => $price_usd,
			'price_gbp'   => $price_gbp,
			'source'      => 'metalsdev',
			'granularity' => 'daily',
		], [ '%s', '%s', '%f', '%f', '%s', '%s' ] );
		$results[ $metal ] = [ 'usd' => $price_usd, 'gbp' => $price_gbp ];
	}

	pmw_metals_seed_update_market_data_acf( $data, $usd_gbp );

	return new WP_REST_Response( [
		'success' => true,
		'date'    => $today,
		'metals'  => $results,
		'logged_at' => gmdate( 'c' ),
	], 200 );
}

function pmw_metals_seed_update_market_data_acf( $metals_data, $usd_gbp ) {
	if ( ! function_exists( 'update_field' ) ) return;

	$metals_map = [ 'gold' => 'gold', 'silver' => 'silver', 'platinum' => 'platinum', 'palladium' => 'palladium' ];
	$opts = [ 'gold', 'silver', 'platinum', 'palladium' ];
	foreach ( $opts as $m ) {
		$usd = isset( $metals_data['metals'][ $m ] ) ? (float) $metals_data['metals'][ $m ] : 0;
		$gbp = $usd * $usd_gbp;
		$change = 0;
		if ( ! empty( $metals_data['metals'][ $m . '_change_percent' ] ) ) {
			$change = (float) $metals_data['metals'][ $m . '_change_percent' ];
		}
		update_field( $m . '_price_usd', $usd, 'market_data' );
		update_field( $m . '_price_gbp', round( $gbp, 4 ), 'market_data' );
		update_field( $m . '_change_24h', $change, 'market_data' );
	}
	update_field( 'last_updated', gmdate( 'c' ), 'market_data' );
}

function pmw_metals_seed_handle_action() {
	if ( ! isset( $_POST['pmw_metals_seed'] ) || ! current_user_can( 'manage_options' ) ) return;
	if ( ! wp_verify_nonce( $_POST['pmw_metals_seed_nonce'] ?? '', 'pmw_metals_seed_run' ) ) return;

	pmw_metals_seed_create_table();
	pmw_metals_seed_run();

	wp_safe_redirect( add_query_arg( [ 'page' => 'pmw-metals-seed' ], admin_url( 'tools.php' ) ) );
	exit;
}
