<?php
/**
 * Plugin Name: PMW Metals Seed
 * Description: Creates metal_prices table and loads historical data. Gold: FreeGoldAPI. Silver/platinum/palladium: MetalPriceAPI Historical (base=USD, rates.USDXAG/USDXPT/USDXPD). Run once, then deactivate.
 * Version:     1.0.0
 * Author:      Markus Mikely
 */

if ( ! defined( 'ABSPATH' ) ) exit;

register_activation_hook( __FILE__, 'pmw_metals_seed_on_activate' );
add_action( 'admin_menu', 'pmw_metals_seed_admin_menu' );
add_action( 'admin_init', 'pmw_metals_seed_handle_action' );
add_action( 'rest_api_init', 'pmw_metals_seed_register_rest_routes' );
add_action( 'wp_ajax_pmw_metals_seed_validate_key', 'pmw_metals_seed_ajax_validate_key' );

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

/**
 * Run full historical seed. $source: 'free' = FreeGoldAPI + URL APIs; 'metalsdev' = Metals.dev timeseries for silver/pt/pd.
 */
function pmw_metals_seed_run( $source = 'free' ) {
	$results = [ 'gold' => [ 'inserted' => 0, 'skipped' => 0 ], 'silver' => [ 'inserted' => 0, 'skipped' => 0 ], 'platinum' => [ 'inserted' => 0, 'skipped' => 0 ], 'palladium' => [ 'inserted' => 0, 'skipped' => 0 ] ];

	$results['gold'] = pmw_metals_seed_load_gold();

	if ( $source === 'metalsdev' ) {
		$results['silver']   = pmw_metals_seed_load_metals_dev( 'silver' );
		$results['platinum']  = pmw_metals_seed_load_metals_dev( 'platinum' );
		$results['palladium'] = pmw_metals_seed_load_metals_dev( 'palladium' );
	} else {
		$key = defined( 'PMW_METALPRICEAPI_KEY' ) ? trim( (string) PMW_METALPRICEAPI_KEY ) : '';
		$has_key = $key !== '' && strpos( $key, '•' ) === false && strpos( $key, "\xE2\x80\xA2" ) === false;
		if ( $has_key ) {
			$hist = pmw_metals_seed_load_metalpriceapi_historical( 90 );
			$results['silver']   = $hist['silver'];
			$results['platinum'] = $hist['platinum'];
			$results['palladium']= $hist['palladium'];
		} else {
			$results['silver']   = [ 'error' => 'Set PMW_METALPRICEAPI_KEY in .env for silver/platinum/palladium', 'inserted' => 0, 'skipped' => 0 ];
			$results['platinum'] = [ 'error' => 'Set PMW_METALPRICEAPI_KEY in .env', 'inserted' => 0, 'skipped' => 0 ];
			$results['palladium']= [ 'error' => 'Set PMW_METALPRICEAPI_KEY in .env', 'inserted' => 0, 'skipped' => 0 ];
		}
	}

	$source_label = $source === 'metalsdev' ? 'Metals.dev' : 'Free APIs (FreeGoldAPI + MetalPriceAPI)';
	$results['_source'] = $source_label;
	update_option( 'pmw_metals_seed_last_run', $results );
	update_option( 'pmw_metals_seed_just_ran', true );
	return $results;
}

/**
 * Return MetalPriceAPI URL for a metal. Prefers PMW_METALPRICEAPI_KEY (builds URL in code);
 * falls back to full URL constant only if it does not contain the masked placeholder.
 * Returns empty string if no valid source.
 */
function pmw_metals_seed_get_metalpriceapi_url( $metal ) {
	$symbols = [ 'silver' => 'XAG', 'platinum' => 'XPT', 'palladium' => 'XPD' ];
	$symbol = $symbols[ $metal ] ?? '';
	if ( $symbol === '' ) {
		return '';
	}
	$key = defined( 'PMW_METALPRICEAPI_KEY' ) ? trim( (string) PMW_METALPRICEAPI_KEY ) : '';
	if ( $key !== '' && strpos( $key, '•' ) === false && strpos( $key, "\xE2\x80\xA2" ) === false ) {
		return 'https://api.metalpriceapi.com/v1/latest?api_key=' . $key . '&base=XAU&currencies=' . $symbol;
	}
	$const = [ 'silver' => 'PMW_SILVER_API_URL', 'platinum' => 'PMW_PLATINUM_API_URL', 'palladium' => 'PMW_PALLADIUM_API_URL' ][ $metal ];
	$url = defined( $const ) ? trim( (string) constant( $const ) ) : '';
	if ( $url === '' ) {
		return '';
	}
	if ( strpos( $url, '••••••••' ) !== false || strpos( $url, "\xE2\x80\xA2" ) !== false ) {
		return '';
	}
	return $url;
}

/**
 * Load silver, platinum, and palladium from MetalPriceAPI Historical Rates.
 * Uses base=USD and rates.USDXAG, rates.USDXPT, rates.USDXPD (USD per troy oz).
 * URL: https://api.metalpriceapi.com/v1/{YYYY-MM-DD}?api_key=KEY&base=USD&currencies=XAU,XAG,XPT,XPD
 * Fetches last N days (default 90). Throttles 1 request/sec to avoid rate limits.
 * Skips failed dates and continues so partial data is still inserted.
 */
function pmw_metals_seed_load_metalpriceapi_historical( $days = 90 ) {
	if ( function_exists( 'set_time_limit' ) ) {
		set_time_limit( max( 300, $days + 120 ) );
	}
	$key = defined( 'PMW_METALPRICEAPI_KEY' ) ? trim( (string) PMW_METALPRICEAPI_KEY ) : '';
	if ( $key === '' || strpos( $key, '•' ) !== false || strpos( $key, "\xE2\x80\xA2" ) !== false ) {
		return [
			'silver'   => [ 'error' => 'PMW_METALPRICEAPI_KEY not set', 'inserted' => 0, 'skipped' => 0 ],
			'platinum' => [ 'error' => 'PMW_METALPRICEAPI_KEY not set', 'inserted' => 0, 'skipped' => 0 ],
			'palladium'=> [ 'error' => 'PMW_METALPRICEAPI_KEY not set', 'inserted' => 0, 'skipped' => 0 ],
		];
	}

	$end_date   = gmdate( 'Y-m-d', strtotime( '-1 day' ) );
	$start_date = gmdate( 'Y-m-d', strtotime( $end_date . " -{$days} days" ) );
	$cutoff     = '1990-01-01';
	if ( $start_date < $cutoff ) {
		$start_date = $cutoff;
	}

	// Prefer USDXAG (USD per oz); fallback: 1/rates.XAG when base=USD (XAG = oz per 1 USD).
	$metal_config = [
		'silver'   => [ 'usd_key' => 'USDXAG', 'quote_key' => 'XAG' ],
		'platinum' => [ 'usd_key' => 'USDXPT', 'quote_key' => 'XPT' ],
		'palladium'=> [ 'usd_key' => 'USDXPD', 'quote_key' => 'XPD' ],
	];
	$records    = [ 'silver' => [], 'platinum' => [], 'palladium' => [] ];
	$source     = 'metalpriceapi_historical';
	$last_error = null;

	for ( $date = $start_date; $date <= $end_date; ) {
		$url = add_query_arg( [
			'api_key'    => $key,
			'base'       => 'USD',
			'currencies' => 'XAU,XAG,XPT,XPD,GBP',
		], 'https://api.metalpriceapi.com/v1/' . $date );

		$resp = wp_remote_get( $url, [ 'timeout' => 30 ] );
		if ( is_wp_error( $resp ) ) {
			$last_error = $resp->get_error_message() . ' (' . $date . ')';
			$date = gmdate( 'Y-m-d', strtotime( $date . ' +1 day' ) );
			sleep( 1 );
			continue;
		}
		if ( wp_remote_retrieve_response_code( $resp ) !== 200 ) {
			$last_error = 'HTTP ' . wp_remote_retrieve_response_code( $resp ) . ' (' . $date . ')';
			$date = gmdate( 'Y-m-d', strtotime( $date . ' +1 day' ) );
			sleep( 1 );
			continue;
		}

		$data = json_decode( wp_remote_retrieve_body( $resp ), true );
		if ( empty( $data['success'] ) || empty( $data['rates'] ) ) {
			$msg = isset( $data['error']['info'] ) ? $data['error']['info'] : ( isset( $data['message'] ) ? $data['message'] : 'Invalid response' );
			$last_error = $msg . ' (' . $date . ')';
			$date = gmdate( 'Y-m-d', strtotime( $date . ' +1 day' ) );
			sleep( 1 );
			continue;
		}

		$usd_to_gbp = 0.79;
		if ( ! empty( $data['rates']['GBP'] ) && (float) $data['rates']['GBP'] > 0 ) {
			$usd_to_gbp = (float) $data['rates']['GBP'];
		}

		foreach ( $metal_config as $metal => $cfg ) {
			$price_usd = null;
			if ( ! empty( $data['rates'][ $cfg['usd_key'] ] ) && (float) $data['rates'][ $cfg['usd_key'] ] > 0 ) {
				$price_usd = (float) $data['rates'][ $cfg['usd_key'] ];
			} elseif ( ! empty( $data['rates'][ $cfg['quote_key'] ] ) && (float) $data['rates'][ $cfg['quote_key'] ] > 0 ) {
				$price_usd = 1.0 / (float) $data['rates'][ $cfg['quote_key'] ];
			}
			if ( $price_usd !== null && $price_usd > 0 ) {
				$records[ $metal ][] = [
					'date'      => $date,
					'price'     => $price_usd,
					'price_gbp' => round( $price_usd * $usd_to_gbp, 4 ),
					'source'    => $source,
				];
			}
		}

		$date = gmdate( 'Y-m-d', strtotime( $date . ' +1 day' ) );
		sleep( 1 );
	}

	$results = [];
	foreach ( [ 'silver', 'platinum', 'palladium' ] as $metal ) {
		if ( ! empty( $records[ $metal ] ) ) {
			$results[ $metal ] = pmw_metals_seed_insert_records_with_gbp( $metal, $records[ $metal ], $source );
		} else {
			$results[ $metal ] = [
				'inserted' => 0,
				'skipped'  => 0,
				'error'    => $last_error ?: 'No rates returned for ' . $metal,
			];
		}
	}

	// Fallback: if no data from date range (e.g. API only allows "yesterday"), fetch yesterday once.
	$any_empty = ( empty( $records['silver'] ) || empty( $records['platinum'] ) || empty( $records['palladium'] ) );
	if ( $any_empty ) {
		$single = pmw_metals_seed_fetch_metalpriceapi_historical_single( 'yesterday' );
		if ( ! is_wp_error( $single ) && ! empty( $single ) ) {
			$yesterday = gmdate( 'Y-m-d', strtotime( '-1 day' ) );
			foreach ( $single as $metal => $prices ) {
				if ( empty( $records[ $metal ] ) ) {
					$inserted = pmw_metals_seed_insert_records_with_gbp( $metal, [
						[ 'date' => $yesterday, 'price' => $prices['price_usd'], 'price_gbp' => $prices['price_gbp'], 'source' => $source ],
					], $source );
					$results[ $metal ] = $inserted;
				}
			}
		}
	}

	return $results;
}

/**
 * Load MetalPriceAPI Historical for a single chunk (date range). Max ~10 days per chunk.
 * Uses sleep(0.25) for faster throughput. Returns [ silver, platinum, palladium ] results.
 */
function pmw_metals_seed_load_metalpriceapi_chunk( $start_date, $end_date ) {
	$key = defined( 'PMW_METALPRICEAPI_KEY' ) ? trim( (string) PMW_METALPRICEAPI_KEY ) : '';
	if ( $key === '' || strpos( $key, '•' ) !== false || strpos( $key, "\xE2\x80\xA2" ) !== false ) {
		return [
			'silver'   => [ 'error' => 'PMW_METALPRICEAPI_KEY not set', 'inserted' => 0, 'skipped' => 0 ],
			'platinum' => [ 'error' => 'PMW_METALPRICEAPI_KEY not set', 'inserted' => 0, 'skipped' => 0 ],
			'palladium'=> [ 'error' => 'PMW_METALPRICEAPI_KEY not set', 'inserted' => 0, 'skipped' => 0 ],
		];
	}

	$metal_config = [
		'silver'   => [ 'usd_key' => 'USDXAG', 'quote_key' => 'XAG' ],
		'platinum' => [ 'usd_key' => 'USDXPT', 'quote_key' => 'XPT' ],
		'palladium'=> [ 'usd_key' => 'USDXPD', 'quote_key' => 'XPD' ],
	];
	$records    = [ 'silver' => [], 'platinum' => [], 'palladium' => [] ];
	$source     = 'metalpriceapi_historical';
	$last_error = null;

	for ( $date = $start_date; $date <= $end_date; ) {
		$url = add_query_arg( [
			'api_key'    => $key,
			'base'       => 'USD',
			'currencies' => 'XAU,XAG,XPT,XPD,GBP',
		], 'https://api.metalpriceapi.com/v1/' . $date );

		$resp = wp_remote_get( $url, [ 'timeout' => 30 ] );
		if ( is_wp_error( $resp ) ) {
			$last_error = $resp->get_error_message() . ' (' . $date . ')';
			$date = gmdate( 'Y-m-d', strtotime( $date . ' +1 day' ) );
			usleep( 250000 );
			continue;
		}
		if ( wp_remote_retrieve_response_code( $resp ) !== 200 ) {
			$last_error = 'HTTP ' . wp_remote_retrieve_response_code( $resp ) . ' (' . $date . ')';
			$date = gmdate( 'Y-m-d', strtotime( $date . ' +1 day' ) );
			usleep( 250000 );
			continue;
		}

		$data = json_decode( wp_remote_retrieve_body( $resp ), true );
		if ( empty( $data['success'] ) || empty( $data['rates'] ) ) {
			$msg = isset( $data['error']['info'] ) ? $data['error']['info'] : ( isset( $data['message'] ) ? $data['message'] : 'Invalid response' );
			$last_error = $msg . ' (' . $date . ')';
			$date = gmdate( 'Y-m-d', strtotime( $date . ' +1 day' ) );
			usleep( 250000 );
			continue;
		}

		$usd_to_gbp = 0.79;
		if ( ! empty( $data['rates']['GBP'] ) && (float) $data['rates']['GBP'] > 0 ) {
			$usd_to_gbp = (float) $data['rates']['GBP'];
		}

		foreach ( $metal_config as $metal => $cfg ) {
			$price_usd = null;
			if ( ! empty( $data['rates'][ $cfg['usd_key'] ] ) && (float) $data['rates'][ $cfg['usd_key'] ] > 0 ) {
				$price_usd = (float) $data['rates'][ $cfg['usd_key'] ];
			} elseif ( ! empty( $data['rates'][ $cfg['quote_key'] ] ) && (float) $data['rates'][ $cfg['quote_key'] ] > 0 ) {
				$price_usd = 1.0 / (float) $data['rates'][ $cfg['quote_key'] ];
			}
			if ( $price_usd !== null && $price_usd > 0 ) {
				$records[ $metal ][] = [
					'date'      => $date,
					'price'     => $price_usd,
					'price_gbp' => round( $price_usd * $usd_to_gbp, 4 ),
					'source'    => $source,
				];
			}
		}

		$date = gmdate( 'Y-m-d', strtotime( $date . ' +1 day' ) );
		usleep( 250000 );
	}

	$results = [];
	foreach ( [ 'silver', 'platinum', 'palladium' ] as $metal ) {
		if ( ! empty( $records[ $metal ] ) ) {
			$results[ $metal ] = pmw_metals_seed_insert_records_with_gbp( $metal, $records[ $metal ], $source );
		} else {
			$results[ $metal ] = [
				'inserted' => 0,
				'skipped'  => 0,
				'error'    => $last_error ?: 'No rates returned for ' . $metal,
			];
		}
	}
	return $results;
}

/**
 * Fetch silver, platinum, palladium for a single date from MetalPriceAPI Historical.
 * Returns [ 'silver' => [usd, gbp], 'platinum' => [...], 'palladium' => [...] ] or WP_Error.
 * $date: YYYY-MM-DD or 'yesterday'.
 */
function pmw_metals_seed_fetch_metalpriceapi_historical_single( $date = 'yesterday' ) {
	$key = defined( 'PMW_METALPRICEAPI_KEY' ) ? trim( (string) PMW_METALPRICEAPI_KEY ) : '';
	if ( $key === '' || strpos( $key, '•' ) !== false || strpos( $key, "\xE2\x80\xA2" ) !== false ) {
		return new WP_Error( 'no_key', 'PMW_METALPRICEAPI_KEY not set' );
	}
	$url = add_query_arg( [
		'api_key'    => $key,
		'base'       => 'USD',
		'currencies' => 'XAU,XAG,XPT,XPD,GBP',
	], 'https://api.metalpriceapi.com/v1/' . $date );

	$resp = wp_remote_get( $url, [ 'timeout' => 15 ] );
	if ( is_wp_error( $resp ) ) {
		return $resp;
	}
	if ( wp_remote_retrieve_response_code( $resp ) !== 200 ) {
		return new WP_Error( 'metalpriceapi_http', 'HTTP ' . wp_remote_retrieve_response_code( $resp ) );
	}

	$data = json_decode( wp_remote_retrieve_body( $resp ), true );
	if ( empty( $data['success'] ) || empty( $data['rates'] ) ) {
		$msg = $data['error']['info'] ?? ( $data['message'] ?? 'Invalid MetalPriceAPI response' );
		return new WP_Error( 'metalpriceapi_parse', $msg );
	}

	$usd_to_gbp = 0.79;
	if ( ! empty( $data['rates']['GBP'] ) && (float) $data['rates']['GBP'] > 0 ) {
		$usd_to_gbp = (float) $data['rates']['GBP'];
	}

	$result = [];
	foreach ( [ 'silver' => 'USDXAG', 'platinum' => 'USDXPT', 'palladium' => 'USDXPD' ] as $metal => $rate_key ) {
		$usd = isset( $data['rates'][ $rate_key ] ) ? (float) $data['rates'][ $rate_key ] : null;
		if ( $usd !== null && $usd > 0 ) {
			$result[ $metal ] = [
				'price_usd' => round( $usd, 4 ),
				'price_gbp' => round( $usd * $usd_to_gbp, 4 ),
			];
		}
	}
	return $result;
}

/**
 * Load silver, platinum, or palladium from Metals.dev timeseries API.
 * Paginates 30 days per request (API limit). GBP from currencies when available, else 0.79 approximation.
 */
function pmw_metals_seed_load_metals_dev( $metal ) {
	$key = defined( 'PMW_METALS_DEV_API_KEY' ) ? PMW_METALS_DEV_API_KEY : '';
	if ( empty( $key ) ) {
		return [ 'message' => 'PMW_METALS_DEV_API_KEY not set', 'inserted' => 0, 'skipped' => 0 ];
	}

	// Metals.dev timeseries may not have data before ~2020 for silver/platinum/palladium.
	$cutoff   = '2020-01-01';
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
		if ( empty( $data['status'] ) || $data['status'] !== 'success' ) {
			$code = isset( $data['error_code'] ) ? (int) $data['error_code'] : 0;
			$msg  = isset( $data['error_message'] ) ? trim( (string) $data['error_message'] ) : 'Invalid Metals.dev response';
			if ( $code ) {
				$msg = $msg . ' (code ' . $code . ')';
			}
			return [ 'error' => $msg, 'inserted' => 0, 'skipped' => 0 ];
		}
		if ( empty( $data['rates'] ) || ! is_array( $data['rates'] ) ) {
			return [ 'error' => 'Metals.dev returned no rates (check date range: max 30 days, end_date cannot be today)', 'inserted' => 0, 'skipped' => 0 ];
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
	$url = is_string( $url ) ? trim( $url ) : '';
	if ( $url === '' ) {
		return [ 'message' => 'No API URL configured', 'inserted' => 0, 'skipped' => 0 ];
	}
	// Do not use a URL that contains the masked placeholder (admin display only)
	if ( strpos( $url, '••••••••' ) !== false || strpos( $url, "\xE2\x80\xA2" ) !== false ) {
		return [ 'error' => 'API URL contains masked key. Set the real api_key in .env (not the •••••••• placeholder).', 'inserted' => 0, 'skipped' => 0 ];
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
	wp_enqueue_script( 'jquery' );
}

/**
 * AJAX: validate Metals.dev API key (lightweight /v1/latest call) .
 */
function pmw_metals_seed_ajax_validate_key() {
	if ( ! current_user_can( 'manage_options' ) ) {
		wp_send_json( [ 'valid' => false, 'error' => 'Unauthorized' ] );
	}
	$key = defined( 'PMW_METALS_DEV_API_KEY' ) ? PMW_METALS_DEV_API_KEY : '';
	if ( empty( $key ) ) {
		wp_send_json( [ 'valid' => false, 'error' => 'API key not set' ] );
	}
	$url  = add_query_arg( [ 'api_key' => $key, 'currency' => 'USD', 'unit' => 'toz' ], 'https://api.metals.dev/v1/latest' );
	$resp = wp_remote_get( $url, [ 'timeout' => 10 ] );
	if ( is_wp_error( $resp ) ) {
		wp_send_json( [ 'valid' => false, 'error' => $resp->get_error_message() ] );
	}
	$code = wp_remote_retrieve_response_code( $resp );
	if ( $code !== 200 ) {
		wp_send_json( [ 'valid' => false, 'error' => 'HTTP ' . $code ] );
	}
	$data = json_decode( wp_remote_retrieve_body( $resp ), true );
	if ( empty( $data['metals'] ) || ! is_array( $data['metals'] ) ) {
		$msg = isset( $data['error_message'] ) ? $data['error_message'] : 'Invalid response';
		wp_send_json( [ 'valid' => false, 'error' => $msg ] );
	}
	wp_send_json( [ 'valid' => true ] );
}

function pmw_metals_seed_env_url_status( $const_name, $default_url = '' ) {
	$url = defined( $const_name ) ? constant( $const_name ) : '';
	$url = is_string( $url ) ? trim( $url ) : '';
	if ( $url === '' && $default_url !== '' ) {
		$url = trim( $default_url );
	}
	if ( $url === '' ) {
		return [ 'set' => false, 'display' => '' ];
	}
	// Non-URL constant (e.g. API key): show masked if it looks like a key
	if ( strpos( $url, '://' ) === false ) {
		return [ 'set' => true, 'display' => '••••••••' ];
	}
	$parsed = wp_parse_url( $url );
	$query  = [];
	if ( ! empty( $parsed['query'] ) ) {
		parse_str( $parsed['query'], $query );
	}
	// Mask only for display; the real URL (with real api_key) is never stored or used from here
	if ( isset( $query['api_key'] ) ) {
		$query['api_key'] = '••••••••';
	}
	$display = ( $parsed['scheme'] ?? '' ) . '://' . ( $parsed['host'] ?? '' ) . ( $parsed['path'] ?? '' );
	if ( ! empty( $query ) ) {
		$display .= '?' . http_build_query( $query );
	}
	return [ 'set' => true, 'display' => $display ];
}

function pmw_metals_seed_admin_page() {
	if ( ! current_user_can( 'manage_options' ) ) return;

	global $wpdb;
	$table = $wpdb->prefix . 'metal_prices';
	$last  = get_option( 'pmw_metals_seed_last_run', [] );
	$last_source = isset( $last['_source'] ) ? $last['_source'] : '';
	$free_apis_ready = true;
	$env_status = [
		'PMW_FREEGOLDAPI_URL'   => pmw_metals_seed_env_url_status( 'PMW_FREEGOLDAPI_URL', 'https://freegoldapi.com/data/latest.json' ),
		'PMW_METALPRICEAPI_KEY' => pmw_metals_seed_env_url_status( 'PMW_METALPRICEAPI_KEY' ),
		'PMW_SILVER_API_URL'   => pmw_metals_seed_env_url_status( 'PMW_SILVER_API_URL' ),
		'PMW_PLATINUM_API_URL' => pmw_metals_seed_env_url_status( 'PMW_PLATINUM_API_URL' ),
		'PMW_PALLADIUM_API_URL'=> pmw_metals_seed_env_url_status( 'PMW_PALLADIUM_API_URL' ),
	];
	// Free APIs ready if gold URL is set and we have a valid source for silver/pt/pd (key or unmasked URLs)
	if ( ! $env_status['PMW_FREEGOLDAPI_URL']['set'] ) {
		$free_apis_ready = false;
	} elseif ( pmw_metals_seed_get_metalpriceapi_url( 'silver' ) === '' || pmw_metals_seed_get_metalpriceapi_url( 'platinum' ) === '' || pmw_metals_seed_get_metalpriceapi_url( 'palladium' ) === '' ) {
		$free_apis_ready = false;
	}
	// For display: if key is set, show it (masked); for URL constants show "✓ set" or "✗ not set"
	$metalprice_key_set = defined( 'PMW_METALPRICEAPI_KEY' ) && trim( (string) PMW_METALPRICEAPI_KEY ) !== '' && strpos( (string) PMW_METALPRICEAPI_KEY, '•' ) === false && strpos( (string) PMW_METALPRICEAPI_KEY, "\xE2\x80\xA2" ) === false;
	$env_status['PMW_METALPRICEAPI_KEY'] = $metalprice_key_set ? [ 'set' => true, 'display' => '••••••••' ] : pmw_metals_seed_env_url_status( 'PMW_METALPRICEAPI_KEY' );
	$metals_dev_key_set = defined( 'PMW_METALS_DEV_API_KEY' ) && trim( (string) PMW_METALS_DEV_API_KEY ) !== '';
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

	$notice = get_transient( 'pmw_metals_seed_notice' );
	if ( $notice && ! empty( $notice['message'] ) ) {
		delete_transient( 'pmw_metals_seed_notice' );
	}
	?>
	<div class="wrap">
		<h1>PMW Metals Seed</h1>
		<p>Creates <code>metal_prices</code> table and loads historical data. Choose a source below, then run a full seed or a one-off daily update.</p>

		<?php if ( $notice && ! empty( $notice['message'] ) ) : ?>
			<div class="notice notice-<?php echo esc_attr( $notice['type'] ); ?> is-dismissible"><p><?php echo esc_html( $notice['message'] ); ?></p></div>
		<?php endif; ?>

		<form method="post" action="" id="pmw-metals-seed-form">
			<?php wp_nonce_field( 'pmw_metals_seed_run', 'pmw_metals_seed_nonce' ); ?>

			<div class="pmw-source-selector" style="max-width: 640px; margin: 1em 0; padding: 1em; border: 1px solid #c3c4c7; background: #fff;">
				<h3 style="margin-top: 0;">Source for full seed</h3>

				<p>
					<label>
						<input type="radio" name="pmw_seed_source_choice" value="free" <?php echo $free_apis_ready ? 'checked ' : 'disabled '; ?> />
						<strong>Free APIs (FreeGoldAPI + MetalPriceAPI)</strong>
					</label>
					<span id="pmw-free-badge"></span>
				</p>
				<p class="description" style="margin-left: 1.5em;">Uses your configured environment variables. No API key required.</p>
			 <ul class="description" style="margin-left: 1.5em; list-style: none;">
					<?php foreach ( $env_status as $name => $s ) : ?>
						<li><?php echo esc_html( $name ); ?> <?php echo $s['set'] ? '✓ set' : '<span style="color:red">✗ not set</span>'; ?>
							<?php if ( $s['set'] && $s['display'] ) : ?> <code style="font-size: 11px;"><?php echo esc_html( $s['display'] ); ?></code><?php endif; ?>
						</li>
					<?php endforeach; ?>
				</ul>
				<p class="description" style="margin-left: 1.5em; color: #646970;">Display shows masked key (••••••••); API requests use the real value from your .env file.</p>
				<?php if ( ! $free_apis_ready ) : ?>
					<p class="description" style="margin-left: 1.5em; color: #d63638;">Configure missing URLs in .env to enable.</p>
				<?php endif; ?>

				<p style="margin-top: 1.2em;">
					<label>
						<input type="radio" name="pmw_seed_source_choice" value="metalsdev" <?php echo ( $metals_dev_key_set && ! $free_apis_ready ) ? 'checked ' : ''; echo $metals_dev_key_set ? '' : 'disabled '; ?> />
						<strong>Metals.dev (full historical timeseries)</strong>
					</label>
					<?php if ( ! $metals_dev_key_set ) : ?>
						<span class="notice notice-info inline" style="margin-left: 8px; padding: 2px 8px;">API key not set</span>
					<?php else : ?>
						<span id="pmw-metalsdev-badge"></span>
					<?php endif; ?>
				</p>
				<p class="description" style="margin-left: 1.5em;">Fetches daily data from 2020-01-01 via Metals.dev API. Slower — use once for initial historical backfill.</p>
				<?php if ( ! $metals_dev_key_set ) : ?>
					<p class="description" style="margin-left: 1.5em; color: #646970;">Set <code>PMW_METALS_DEV_API_KEY</code> in .env or wp-config.php to enable.</p>
				<?php endif; ?>
			</div>

			<p>
				<button type="submit" name="pmw_seed_source" value="1" class="button button-primary" id="pmw-seed-btn">Run Seed Now</button>
				<button type="submit" name="pmw_daily_update" value="1" class="button button-secondary" id="pmw-daily-btn" title="Always uses free API sources. Same as the daily cron job.">Run Daily Update Now</button>
			</p>
			<div id="pmw-seed-progress" style="display:none; margin: 1em 0; padding: 1em; background: #f0f0f1; border-radius: 4px; max-width: 500px;">
				<p><strong>Running seed in chunks…</strong></p>
				<p id="pmw-seed-progress-text">Starting…</p>
				<div style="background: #fff; height: 8px; border-radius: 4px; overflow: hidden; margin-top: 8px;">
					<div id="pmw-seed-progress-bar" style="background: #2271b1; height: 100%; width: 0%; transition: width 0.2s;"></div>
				</div>
			</div>
			<p class="description">Run Daily Update Now always uses free API sources (same as the daily cron job). Free APIs seed runs in chunks to avoid timeout.</p>
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

		<?php
		$last_metals = array_diff_key( $last, [ '_source' => 1 ] );
		if ( ! empty( $last_metals ) ) :
		?>
		<h2>Last run</h2>
		<table class="widefat striped">
			<thead><tr><th>Metal</th><th>Result</th><?php if ( $last_source ) : ?><th>Source</th><?php endif; ?></tr></thead>
			<tbody>
			<?php
			foreach ( $last_metals as $metal => $r ) :
				if ( ! is_array( $r ) ) continue;
			?>
				<tr>
					<td><?php echo esc_html( ucfirst( $metal ) ); ?></td>
					<td>
						<?php
						if ( ! empty( $r['error'] ) ) {
							echo '<span style="color:red">Error: ' . esc_html( $r['error'] ) . '</span>';
						} elseif ( ! empty( $r['message'] ) ) {
							echo esc_html( $r['message'] );
						} else {
							echo 'Inserted: ' . (int) ( $r['inserted'] ?? 0 ) . ', Skipped: ' . (int) ( $r['skipped'] ?? 0 );
						}
						?>
					</td>
					<?php if ( $last_source ) : ?><td><?php echo esc_html( $last_source ); ?></td><?php endif; ?>
				</tr>
			<?php endforeach; ?>
			</tbody>
		</table>
		<?php endif; ?>

		<h2>Configuration</h2>
		<p>Set in <code>.env</code> or wp-config: <code>PMW_FREEGOLDAPI_URL</code> for gold (may have gaps — API dependent); <code>PMW_METALPRICEAPI_KEY</code> for silver/platinum/palladium (Historical API, chunked to avoid timeout); <code>PMW_METALS_DEV_API_KEY</code> for Metals.dev (timeseries from 2020).</p>

		<?php if ( $metals_dev_key_set ) : ?>
		<script>
		(function() {
			var ajaxUrl = <?php echo wp_json_encode( admin_url( 'admin-ajax.php' ) ); ?>;
			var nonce = <?php echo wp_json_encode( wp_create_nonce( 'pmw_metals_seed_validate' ) ); ?>;
			var badgeEl = document.getElementById('pmw-metalsdev-badge');
			var seedBtn = document.getElementById('pmw-seed-btn');
			var form = document.getElementById('pmw-metals-seed-form');
			var metalsDevValid = null;

			function setBadge(valid, error) {
				if (!badgeEl) return;
				if (valid === true) {
					badgeEl.innerHTML = '<span style="color: #00a32a; margin-left: 6px;">✓ Key valid</span>';
					badgeEl.style.color = '';
				} else if (valid === false) {
					badgeEl.innerHTML = '<span style="color: #d63638; margin-left: 6px;">✗ Key invalid — ' + (error || 'Unknown error') + '</span>';
					badgeEl.style.color = '#d63638';
				} else {
					badgeEl.innerHTML = '<span style="color: #646970; margin-left: 6px;">Checking…</span>';
				}
			}

			function validateKey(cb) {
				setBadge(null);
				jQuery.post(ajaxUrl, { action: 'pmw_metals_seed_validate_key', _wpnonce: nonce }, function(data) {
					metalsDevValid = data.valid === true;
					setBadge(data.valid, data.error || '');
					if (cb) cb(data);
				}).fail(function() {
					metalsDevValid = false;
					setBadge(false, 'Request failed');
					if (cb) cb({ valid: false, error: 'Request failed' });
				});
			}

			function updateSeedButtonState() {
				var choice = form && form.querySelector('input[name="pmw_seed_source_choice"]:checked');
				if (!seedBtn) return;
				if (choice && choice.value === 'metalsdev' && metalsDevValid === false) {
					seedBtn.disabled = true;
				} else {
					seedBtn.disabled = false;
				}
			}

			if (badgeEl && form) {
				validateKey(updateSeedButtonState);
				form.addEventListener('change', function() {
					var choice = form.querySelector('input[name="pmw_seed_source_choice"]:checked');
					if (choice && choice.value === 'metalsdev') {
						validateKey(updateSeedButtonState);
					} else {
						updateSeedButtonState();
					}
				});
			}
		})();
		</script>
		<?php endif; ?>

		<?php if ( $free_apis_ready ) : ?>
		<script>
		(function() {
			var form = document.getElementById('pmw-metals-seed-form');
			var seedBtn = document.getElementById('pmw-seed-btn');
			var progressDiv = document.getElementById('pmw-seed-progress');
			var progressText = document.getElementById('pmw-seed-progress-text');
			var progressBar = document.getElementById('pmw-seed-progress-bar');
			var restUrl = <?php echo wp_json_encode( rest_url( 'pmw/v1/seed-step' ) ); ?>;
			var restNonce = <?php echo wp_json_encode( wp_create_nonce( 'wp_rest' ) ); ?>;

			function postStep(body) {
				return fetch(restUrl, {
					method: 'POST',
					headers: {
						'Content-Type': 'application/json',
						'X-WP-Nonce': restNonce
					},
					body: JSON.stringify(body),
					credentials: 'same-origin'
				}).then(function(r) {
					if (!r.ok) throw new Error('Request failed: ' + r.status);
					return r.json();
				});
			}

			form.addEventListener('submit', function(e) {
				var btn = document.activeElement;
				if (!btn || btn.name !== 'pmw_seed_source' || btn.value !== '1') return;
				var choice = form.querySelector('input[name="pmw_seed_source_choice"]:checked');
				if (!choice || choice.value !== 'free') return;

				e.preventDefault();
				seedBtn.disabled = true;
				progressDiv.style.display = 'block';
				progressText.textContent = 'Gold…';
				progressBar.style.width = '5%';

				postStep({ step: 'gold' }).then(function(res) {
					progressText.textContent = 'Gold done. MetalPriceAPI chunks…';
					progressBar.style.width = '10%';

					var endDate = new Date();
					endDate.setDate(endDate.getDate() - 1);
					var startDate = new Date(endDate);
					startDate.setDate(startDate.getDate() - 90);
					var chunkDays = 10;
					var chunks = [];
					var s = new Date(startDate);
					while (s <= endDate) {
						var e = new Date(s);
						e.setDate(e.getDate() + chunkDays - 1);
						if (e > endDate) e = new Date(endDate);
						chunks.push({
							start: s.toISOString().slice(0, 10),
							end: e.toISOString().slice(0, 10)
						});
						s.setDate(s.getDate() + chunkDays);
					}

					var total = chunks.length;
					var done = 0;
					function runChunk(i) {
						if (i >= total) {
							progressBar.style.width = '100%';
							progressText.textContent = 'Done. Reloading…';
							location.reload();
							return;
						}
						var c = chunks[i];
						progressText.textContent = 'MetalPriceAPI chunk ' + (i + 1) + '/' + total + ' (' + c.start + ' … ' + c.end + ')';
						progressBar.style.width = (10 + (80 * (i + 1) / total)) + '%';

						return postStep({
							step: 'metalpriceapi_chunk',
							start_date: c.start,
							end_date: c.end,
							is_last: i === total - 1
						}).then(function() {
							return runChunk(i + 1);
						});
					}
					return runChunk(0);
				}).catch(function(err) {
					progressText.textContent = 'Error: ' + (err.message || 'Unknown');
					seedBtn.disabled = false;
				});
			});
		})();
		</script>
		<?php endif; ?>
	</div>
	<?php
}

/**
 * METAL-03 — Daily price update cron endpoint.
 * POST /wp-json/pmw/v1/cron/price-update
 * Auth: Authorization: Bearer {PMW_CRON_SECRET}
 *
 * Sources:
 *   Gold:      PMW_FREEGOLDAPI_URL  (FreeGoldAPI — free, no key)
 *   Silver:    PMW_SILVER_API_URL   (MetalPriceAPI, base=XAU, currencies=XAG[,GBP])
 *   Platinum:  PMW_PLATINUM_API_URL (MetalPriceAPI, base=XAU, currencies=XPT[,GBP])
 *   Palladium: PMW_PALLADIUM_API_URL(MetalPriceAPI, base=XAU, currencies=XPD[,GBP])
 *
 * MetalPriceAPI response (base=XAU): rates["XAG"] = oz silver per oz gold.
 *   price_usd = gold_usd_price / rates["XAG"]  (i.e. silver spot in USD)
 *   If rates["GBP"] is present: price_gbp = gold_gbp_price / rates["XAG"]
 *     where gold_gbp_price = rates["GBP"]  (GBP per oz gold, since base=XAU).
 */
function pmw_metals_seed_register_rest_routes() {
	register_rest_route( 'pmw/v1', '/cron/price-update', [
		'methods'             => 'POST',
		'callback'            => 'pmw_metals_seed_cron_price_update',
		'permission_callback' => 'pmw_metals_seed_cron_permission',
	] );

	register_rest_route( 'pmw/v1', '/seed-step', [
		'methods'             => 'POST',
		'callback'            => 'pmw_metals_seed_rest_seed_step',
		'permission_callback' => function () { return current_user_can( 'manage_options' ); },
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

/**
 * REST POST /pmw/v1/seed-step — chunked seed flow for Free APIs (avoids timeout).
 * Body: { step: 'gold' | 'metalpriceapi_chunk' | 'finalize', start_date?, end_date?, is_last? }
 */
function pmw_metals_seed_rest_seed_step( $request ) {
	$params = $request->get_json_params() ?: $request->get_params();
	$step   = isset( $params['step'] ) ? sanitize_text_field( $params['step'] ) : '';
	$start  = isset( $params['start_date'] ) ? sanitize_text_field( $params['start_date'] ) : '';
	$end    = isset( $params['end_date'] ) ? sanitize_text_field( $params['end_date'] ) : '';
	$is_last = ! empty( $params['is_last'] );

	if ( $step === 'gold' ) {
		pmw_metals_seed_create_table();
		$gold = pmw_metals_seed_load_gold();
		$partial = [
			'gold'     => $gold,
			'silver'   => [ 'inserted' => 0, 'skipped' => 0 ],
			'platinum' => [ 'inserted' => 0, 'skipped' => 0 ],
			'palladium'=> [ 'inserted' => 0, 'skipped' => 0 ],
			'_source'  => 'Free APIs (FreeGoldAPI + MetalPriceAPI)',
		];
		set_transient( 'pmw_metals_seed_partial', $partial, 600 );
		return rest_ensure_response( [ 'gold' => $gold ] );
	}

	if ( $step === 'metalpriceapi_chunk' && $start && $end ) {
		$chunk = pmw_metals_seed_load_metalpriceapi_chunk( $start, $end );
		$partial = get_transient( 'pmw_metals_seed_partial' );
		if ( ! is_array( $partial ) ) {
			$partial = [ 'gold' => [ 'inserted' => 0, 'skipped' => 0 ], 'silver' => [ 'inserted' => 0, 'skipped' => 0 ], 'platinum' => [ 'inserted' => 0, 'skipped' => 0 ], 'palladium' => [ 'inserted' => 0, 'skipped' => 0 ], '_source' => 'Free APIs (FreeGoldAPI + MetalPriceAPI)' ];
		}
		foreach ( [ 'silver', 'platinum', 'palladium' ] as $metal ) {
			if ( isset( $chunk[ $metal ]['inserted'] ) ) {
				$partial[ $metal ]['inserted'] = ( $partial[ $metal ]['inserted'] ?? 0 ) + (int) $chunk[ $metal ]['inserted'];
				$partial[ $metal ]['skipped']  = ( $partial[ $metal ]['skipped'] ?? 0 ) + (int) ( $chunk[ $metal ]['skipped'] ?? 0 );
			}
			if ( ! empty( $chunk[ $metal ]['error'] ) ) {
				$partial[ $metal ]['error'] = $chunk[ $metal ]['error'];
			}
		}
		set_transient( 'pmw_metals_seed_partial', $partial, 600 );
		if ( $is_last ) {
			update_option( 'pmw_metals_seed_last_run', $partial );
			update_option( 'pmw_metals_seed_just_ran', true );
			delete_transient( 'pmw_metals_seed_partial' );
		}
		return rest_ensure_response( [ 'chunk' => $chunk, 'partial' => $partial ] );
	}

	if ( $step === 'finalize' ) {
		$partial = get_transient( 'pmw_metals_seed_partial' );
		if ( is_array( $partial ) ) {
			update_option( 'pmw_metals_seed_last_run', $partial );
			update_option( 'pmw_metals_seed_just_ran', true );
			delete_transient( 'pmw_metals_seed_partial' );
		}
		return rest_ensure_response( [ 'done' => true ] );
	}

	return new WP_Error( 'invalid_step', 'Invalid step or missing params', [ 'status' => 400 ] );
}

/**
 * Fetch today's gold spot price in USD from FreeGoldAPI.
 * Returns float on success, or WP_Error on failure.
 */
function pmw_metals_seed_fetch_gold_usd() {
	$url  = defined( 'PMW_FREEGOLDAPI_URL' ) ? PMW_FREEGOLDAPI_URL : 'https://freegoldapi.com/data/latest.json';
	$resp = wp_remote_get( $url, [ 'timeout' => 15 ] );

	if ( is_wp_error( $resp ) ) {
		return $resp;
	}
	if ( wp_remote_retrieve_response_code( $resp ) !== 200 ) {
		return new WP_Error( 'freegoldapi_http', 'FreeGoldAPI HTTP ' . wp_remote_retrieve_response_code( $resp ) );
	}

	$data = json_decode( wp_remote_retrieve_body( $resp ), true );
	if ( ! is_array( $data ) ) {
		return new WP_Error( 'freegoldapi_parse', 'FreeGoldAPI: invalid JSON' );
	}

	// The API returns an array of records sorted newest-first (or we find the latest).
	$latest_price = null;
	$latest_date  = null;
	foreach ( $data as $row ) {
		if ( isset( $row['price'] ) && is_numeric( $row['price'] ) && ! empty( $row['date'] ) ) {
			if ( $latest_date === null || $row['date'] > $latest_date ) {
				$latest_date  = $row['date'];
				$latest_price = (float) $row['price'];
			}
		}
	}

	if ( $latest_price === null || $latest_price <= 0 ) {
		return new WP_Error( 'freegoldapi_no_price', 'FreeGoldAPI: no valid price found' );
	}

	return $latest_price;
}

/**
 * Fetch a non-gold metal price via MetalPriceAPI.
 *
 * URL format (from env): base=XAU, currencies=XAG|XPT|XPD[,GBP]
 * Appends GBP to the currencies param if not already present so we get
 * GBP conversion in a single request.
 *
 * Returns array [ 'price_usd' => float, 'price_gbp' => float ] or WP_Error.
 *
 * @param string $api_url  The full URL from PMW_SILVER_API_URL etc.
 * @param string $symbol   One of: XAG, XPT, XPD
 * @param float  $gold_usd Current gold spot price in USD (used for conversion).
 */
function pmw_metals_seed_fetch_metalpriceapi( $api_url, $symbol, $gold_usd ) {
	$api_url = trim( $api_url );
	if ( strpos( $api_url, '••••••••' ) !== false || strpos( $api_url, "\xE2\x80\xA2" ) !== false ) {
		return new WP_Error( 'metalpriceapi_masked_key', 'API URL contains masked key. Set the real api_key in .env (not the •••••••• placeholder).' );
	}

	// Ensure GBP is included in the currencies param so we can derive GBP price.
	$parsed = wp_parse_url( $api_url );
	$query  = [];
	if ( ! empty( $parsed['query'] ) ) {
		parse_str( $parsed['query'], $query );
	}
	$currencies = isset( $query['currencies'] ) ? explode( ',', $query['currencies'] ) : [ $symbol ];
	if ( ! in_array( 'GBP', $currencies, true ) ) {
		$currencies[] = 'GBP';
	}
	$query['currencies'] = implode( ',', $currencies );

	// Rebuild URL with updated currencies param.
	$scheme   = $parsed['scheme'] ?? 'https';
	$host     = $parsed['host']   ?? '';
	$path     = $parsed['path']   ?? '';
	$base_url = $scheme . '://' . $host . $path;
	$url      = add_query_arg( $query, $base_url );

	$resp = wp_remote_get( $url, [ 'timeout' => 15 ] );
	if ( is_wp_error( $resp ) ) {
		return $resp;
	}
	if ( wp_remote_retrieve_response_code( $resp ) !== 200 ) {
		return new WP_Error( 'metalpriceapi_http', 'MetalPriceAPI HTTP ' . wp_remote_retrieve_response_code( $resp ) . ' for ' . $symbol );
	}

	$data = json_decode( wp_remote_retrieve_body( $resp ), true );

	// Expect: { "success": true, "base": "XAU", "rates": { "XAG": 88.5, "GBP": 2750.0, ... } }
	if ( empty( $data['success'] ) || empty( $data['rates'] ) ) {
		$msg = $data['error']['info'] ?? ( $data['message'] ?? 'Invalid MetalPriceAPI response for ' . $symbol );
		return new WP_Error( 'metalpriceapi_parse', $msg );
	}

	// rates[symbol] = how many units of symbol equal 1 XAU (1 oz gold).
	// e.g. rates["XAG"] = 88.5 means 1 oz gold = 88.5 oz silver.
	// Therefore: silver_usd = gold_usd / 88.5
	$ratio = isset( $data['rates'][ $symbol ] ) ? (float) $data['rates'][ $symbol ] : 0;
	if ( $ratio <= 0 ) {
		return new WP_Error( 'metalpriceapi_ratio', 'MetalPriceAPI: zero or missing ratio for ' . $symbol );
	}

	$price_usd = $gold_usd / $ratio;

	// rates["GBP"] = GBP per 1 oz gold (since base=XAU).
	// Therefore: metal_gbp = rates["GBP"] / ratio
	$price_gbp = null;
	if ( ! empty( $data['rates']['GBP'] ) && (float) $data['rates']['GBP'] > 0 ) {
		$gold_gbp  = (float) $data['rates']['GBP'];
		$price_gbp = round( $gold_gbp / $ratio, 4 );
	} else {
		// Fallback: apply approximate USD→GBP rate of 0.79.
		$price_gbp = round( $price_usd * 0.79, 4 );
	}

	return [
		'price_usd' => round( $price_usd, 4 ),
		'price_gbp' => $price_gbp,
	];
}

function pmw_metals_seed_cron_price_update( $request ) {
	global $wpdb;
	$table   = $wpdb->prefix . 'metal_prices';
	$today   = gmdate( 'Y-m-d' );
	$results = [];
	$errors  = [];

	// -------------------------------------------------------------------------
	// 1. Gold — FreeGoldAPI (free, no key required)
	// -------------------------------------------------------------------------
	$gold_usd = pmw_metals_seed_fetch_gold_usd();
	if ( is_wp_error( $gold_usd ) ) {
		$errors['gold'] = $gold_usd->get_error_message();
	} else {
		// Derive GBP via a lightweight FX call (fallback to 0.79 if unavailable).
		$usd_to_gbp = 0.79;
		$fx_resp    = wp_remote_get( 'https://api.exchangerate-api.com/v4/latest/USD', [ 'timeout' => 10 ] );
		if ( ! is_wp_error( $fx_resp ) && wp_remote_retrieve_response_code( $fx_resp ) === 200 ) {
			$fx = json_decode( wp_remote_retrieve_body( $fx_resp ), true );
			if ( ! empty( $fx['rates']['GBP'] ) ) {
				$usd_to_gbp = (float) $fx['rates']['GBP'];
			}
		}

		$gold_gbp = round( $gold_usd * $usd_to_gbp, 4 );
		$wpdb->replace( $table, [
			'metal'       => 'gold',
			'date'        => $today,
			'price_usd'   => $gold_usd,
			'price_gbp'   => $gold_gbp,
			'source'      => 'freegoldapi',
			'granularity' => 'daily',
		], [ '%s', '%s', '%f', '%f', '%s', '%s' ] );
		$results['gold'] = [ 'usd' => $gold_usd, 'gbp' => $gold_gbp ];
	}

	// -------------------------------------------------------------------------
	// 2. Silver, Platinum, Palladium — MetalPriceAPI Historical (base=USD)
	//    Uses Historical API for yesterday; no gold cross-rate needed.
	// -------------------------------------------------------------------------
	$yesterday = gmdate( 'Y-m-d', strtotime( '-1 day' ) );
	$hist      = pmw_metals_seed_fetch_metalpriceapi_historical_single( 'yesterday' );
	if ( is_wp_error( $hist ) ) {
		foreach ( [ 'silver', 'platinum', 'palladium' ] as $metal ) {
			$errors[ $metal ] = $hist->get_error_message();
		}
	} elseif ( ! empty( $hist ) ) {
		foreach ( $hist as $metal => $prices ) {
			$wpdb->replace( $table, [
				'metal'       => $metal,
				'date'        => $yesterday,
				'price_usd'   => $prices['price_usd'],
				'price_gbp'   => $prices['price_gbp'],
				'source'      => 'metalpriceapi_historical',
				'granularity' => 'daily',
			], [ '%s', '%s', '%f', '%f', '%s', '%s' ] );
			$results[ $metal ] = [ 'usd' => $prices['price_usd'], 'gbp' => $prices['price_gbp'] ];
		}
		foreach ( [ 'silver', 'platinum', 'palladium' ] as $metal ) {
			if ( empty( $results[ $metal ] ) ) {
				$errors[ $metal ] = 'No rate returned for ' . $metal;
			}
		}
	}

	// -------------------------------------------------------------------------
	// 3. Update ACF market_data fields & bust caches (unchanged).
	// -------------------------------------------------------------------------
	if ( ! empty( $results ) ) {
		pmw_metals_seed_update_market_data_acf_v2( $results );
	}

	if ( function_exists( 'pmw_invalidate_prices_history_cache' ) ) {
		pmw_invalidate_prices_history_cache();
	}

	$success = empty( $errors );
	$status  = $success ? 200 : ( empty( $results ) ? 502 : 207 ); // 207 = partial success

	return new WP_REST_Response( [
		'success'    => $success,
		'date'       => $today,
		'metals'     => $results,
		'errors'     => $errors,
		'logged_at'  => gmdate( 'c' ),
	], $status );
}

/**
 * Updated ACF helper — works from the normalised $results array returned by the
 * new cron handler: [ 'gold' => ['usd'=>…,'gbp'=>…], 'silver' => […], … ]
 */
function pmw_metals_seed_update_market_data_acf_v2( $results ) {
	if ( ! function_exists( 'update_field' ) ) return;

	foreach ( [ 'gold', 'silver', 'platinum', 'palladium' ] as $m ) {
		if ( empty( $results[ $m ] ) ) continue;
		update_field( $m . '_price_usd', $results[ $m ]['usd'],        'market_data' );
		update_field( $m . '_price_gbp', $results[ $m ]['gbp'],        'market_data' );
		// change_24h is no longer available from these free APIs — set to 0 / leave unchanged.
		update_field( $m . '_change_24h', 0,                           'market_data' );
	}
	update_field( 'last_updated', gmdate( 'c' ), 'market_data' );
}

/**
 * Legacy ACF helper kept for backwards compatibility (used by original seed run).
 */
function pmw_metals_seed_update_market_data_acf( $metals_data, $usd_gbp ) {
	if ( ! function_exists( 'update_field' ) ) return;

	$opts = [ 'gold', 'silver', 'platinum', 'palladium' ];
	foreach ( $opts as $m ) {
		$usd    = isset( $metals_data['metals'][ $m ] ) ? (float) $metals_data['metals'][ $m ] : 0;
		$gbp    = $usd * $usd_gbp;
		$change = ! empty( $metals_data['metals'][ $m . '_change_percent' ] )
				  ? (float) $metals_data['metals'][ $m . '_change_percent' ]
				  : 0;
		update_field( $m . '_price_usd', $usd,                  'market_data' );
		update_field( $m . '_price_gbp', round( $gbp, 4 ),      'market_data' );
		update_field( $m . '_change_24h', $change,              'market_data' );
	}
	update_field( 'last_updated', gmdate( 'c' ), 'market_data' );
}

function pmw_metals_seed_handle_action() {
	if ( ! current_user_can( 'manage_options' ) ) return;
	if ( ! isset( $_POST['pmw_metals_seed_nonce'] ) || ! wp_verify_nonce( $_POST['pmw_metals_seed_nonce'], 'pmw_metals_seed_run' ) ) return;

	pmw_metals_seed_create_table();

	$notice = [ 'type' => 'info', 'message' => '' ];

	if ( ! empty( $_POST['pmw_seed_source'] ) ) {
		$choice = isset( $_POST['pmw_seed_source_choice'] ) ? sanitize_text_field( $_POST['pmw_seed_source_choice'] ) : 'free';
		if ( ! in_array( $choice, [ 'free', 'metalsdev' ], true ) ) {
			$choice = 'free';
		}
		$results = pmw_metals_seed_run( $choice );
		$source_label = $results['_source'] ?? $choice;
		unset( $results['_source'] );
		$errors = array_filter( $results, function ( $r ) { return ! empty( $r['error'] ); } );
		$inserted_total = array_sum( array_column( $results, 'inserted' ) );
		if ( empty( $errors ) ) {
			$notice = [ 'type' => 'success', 'message' => sprintf( 'Seed complete. %d records inserted across 4 metals using %s.', $inserted_total, $source_label ) ];
		} elseif ( count( $errors ) < 4 ) {
			$parts = [];
			foreach ( $errors as $metal => $r ) {
				$parts[] = ucfirst( $metal ) . ': ' . ( $r['error'] ?? 'error' );
			}
			$notice = [ 'type' => 'warning', 'message' => 'Seed completed with errors. ' . implode( ' ', $parts ) . ' Check the Last Run table below.' ];
		} else {
			$notice = [ 'type' => 'error', 'message' => 'Seed failed. See details in the Last Run table below.' ];
		}
	} elseif ( ! empty( $_POST['pmw_daily_update'] ) ) {
		$req = new WP_REST_Request( 'POST' );
		$resp = pmw_metals_seed_cron_price_update( $req );
		$data = $resp->get_data();
		$last_run = [ '_source' => 'Free APIs (daily)' ];
		foreach ( [ 'gold', 'silver', 'platinum', 'palladium' ] as $m ) {
			if ( ! empty( $data['errors'][ $m ] ) ) {
				$last_run[ $m ] = [ 'error' => $data['errors'][ $m ], 'inserted' => 0, 'skipped' => 0 ];
			} else {
				$last_run[ $m ] = [ 'inserted' => 1, 'skipped' => 0 ];
			}
		}
		update_option( 'pmw_metals_seed_last_run', $last_run );
		if ( ! empty( $data['success'] ) && empty( $data['errors'] ) ) {
			$notice = [ 'type' => 'success', 'message' => 'Daily update complete. All 4 metals updated using free APIs.' ];
		} elseif ( ! empty( $data['metals'] ) ) {
			$notice = [ 'type' => 'warning', 'message' => 'Daily update completed with some errors. Check the Last Run table below.' ];
		} else {
			$notice = [ 'type' => 'error', 'message' => 'Daily update failed. See details below.' ];
		}
	} else {
		return;
	}

	set_transient( 'pmw_metals_seed_notice', $notice, 30 );
	wp_safe_redirect( add_query_arg( [ 'page' => 'pmw-metals-seed' ], admin_url( 'tools.php' ) ) );
	exit;
}