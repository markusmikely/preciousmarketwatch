<?php
/**
 * Plugin Name: PMW Bridge
 * Plugin URI:  https://preciousmarketwatch.com
 * Description: WebSocket client for real-time connection between WordPress Mission Control and the LangGraph agent engine.
 * Version:     1.0.0
 * Author:      Markus Mikely
 * License:     GPL-2.0+
 */

if ( ! defined( 'ABSPATH' ) ) exit;

define( 'PMW_BRIDGE_VERSION', '1.0.0' );

// Bridge WebSocket URL — set in wp-config.php or .env
if ( ! defined( 'PMW_BRIDGE_WS_URL' ) ) {
    define( 'PMW_BRIDGE_WS_URL', 'ws://localhost:8000/ws' );
}

add_action( 'admin_enqueue_scripts', 'pmw_bridge_enqueue_ws_client', 20 );

function pmw_bridge_enqueue_ws_client( $hook ) {
    if ( $hook !== 'index.php' ) {
        return;
    }
    if ( ! current_user_can( 'edit_posts' ) ) {
        return;
    }

    $asset_url = plugin_dir_url( __FILE__ ) . 'assets/ws-client.js';
    wp_enqueue_script(
        'pmw-bridge-ws',
        $asset_url,
        [],
        PMW_BRIDGE_VERSION,
        true
    );
    wp_localize_script( 'pmw-bridge-ws', 'PMW_BRIDGE', [
        'ws_url'   => PMW_BRIDGE_WS_URL,
        'nonce'    => wp_create_nonce( 'pmw_bridge' ),
        'agent_id' => get_current_user_id(),
    ] );
}
