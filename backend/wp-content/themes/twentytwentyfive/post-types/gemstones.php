<?php
/**
 * Custom post type
 *
 * @package twentytwentyfive
 */

/**
 * Registers the `gemstones` post type.
 */
function twentytwentyfive_init() {
	register_post_type(
		'gemstones',
		array(
			'labels'                => array(
				'name'                  => __( 'Gemstones', 'twentytwentyfive' ),
				'singular_name'         => __( 'Gemstones', 'twentytwentyfive' ),
				'all_items'             => __( 'All Gemstones', 'twentytwentyfive' ),
				'archives'              => __( 'Gemstones Archives', 'twentytwentyfive' ),
				'attributes'            => __( 'Gemstones Attributes', 'twentytwentyfive' ),
				'insert_into_item'      => __( 'Insert into gemstones', 'twentytwentyfive' ),
				'uploaded_to_this_item' => __( 'Uploaded to this gemstones', 'twentytwentyfive' ),
				'featured_image'        => _x( 'Featured Image', 'gemstones', 'twentytwentyfive' ),
				'set_featured_image'    => _x( 'Set featured image', 'gemstones', 'twentytwentyfive' ),
				'remove_featured_image' => _x( 'Remove featured image', 'gemstones', 'twentytwentyfive' ),
				'use_featured_image'    => _x( 'Use as featured image', 'gemstones', 'twentytwentyfive' ),
				'filter_items_list'     => __( 'Filter gemstones list', 'twentytwentyfive' ),
				'items_list_navigation' => __( 'Gemstones list navigation', 'twentytwentyfive' ),
				'items_list'            => __( 'Gemstones list', 'twentytwentyfive' ),
				'new_item'              => __( 'New Gemstones', 'twentytwentyfive' ),
				'add_new'               => __( 'Add New', 'twentytwentyfive' ),
				'add_new_item'          => __( 'Add New Gemstones', 'twentytwentyfive' ),
				'edit_item'             => __( 'Edit Gemstones', 'twentytwentyfive' ),
				'view_item'             => __( 'View Gemstones', 'twentytwentyfive' ),
				'view_items'            => __( 'View Gemstones', 'twentytwentyfive' ),
				'search_items'          => __( 'Search gemstones', 'twentytwentyfive' ),
				'not_found'             => __( 'No gemstones found', 'twentytwentyfive' ),
				'not_found_in_trash'    => __( 'No gemstones found in trash', 'twentytwentyfive' ),
				'parent_item_colon'     => __( 'Parent Gemstones:', 'twentytwentyfive' ),
				'menu_name'             => __( 'Gemstones', 'twentytwentyfive' ),
			),
			'public'                => true,
			'hierarchical'          => false,
			'show_ui'               => true,
			'show_in_nav_menus'     => true,
			'supports'              => array( 'title', 'editor' ),
			'has_archive'           => true,
			'rewrite'               => true,
			'query_var'             => true,
			'menu_position'         => null,
			'menu_icon'             => 'dashicons-admin-post',
			'show_in_rest'          => true,
			'rest_base'             => 'gemstones',
			'rest_controller_class' => 'WP_REST_Posts_Controller',
		)
	);
}

add_action( 'init', 'twentytwentyfive_init' );

/**
 * Sets the post updated messages for the `gemstones` post type.
 *
 * @param  array $messages Post updated messages.
 * @return array Messages for the `gemstones` post type.
 */
function twentytwentyfive_updated_messages( $messages ) {
	global $post;

	$permalink = get_permalink( $post );

	$messages['gemstones'] = array(
		0  => '', // Unused. Messages start at index 1.
		/* translators: %s: post permalink */
		1  => sprintf( __( 'Gemstones updated. <a target="_blank" href="%s">View gemstones</a>', 'twentytwentyfive' ), esc_url( $permalink ) ),
		2  => __( 'Custom field updated.', 'twentytwentyfive' ),
		3  => __( 'Custom field deleted.', 'twentytwentyfive' ),
		4  => __( 'Gemstones updated.', 'twentytwentyfive' ),
		/* translators: %s: date and time of the revision */
		5  => isset( $_GET['revision'] ) ? sprintf( __( 'Gemstones restored to revision from %s', 'twentytwentyfive' ), wp_post_revision_title( (int) $_GET['revision'], false ) ) : false, // phpcs:ignore WordPress.Security.NonceVerification.Recommended
		/* translators: %s: post permalink */
		6  => sprintf( __( 'Gemstones published. <a href="%s">View gemstones</a>', 'twentytwentyfive' ), esc_url( $permalink ) ),
		7  => __( 'Gemstones saved.', 'twentytwentyfive' ),
		/* translators: %s: post permalink */
		8  => sprintf( __( 'Gemstones submitted. <a target="_blank" href="%s">Preview gemstones</a>', 'twentytwentyfive' ), esc_url( add_query_arg( 'preview', 'true', $permalink ) ) ),
		/* translators: 1: Publish box date format, see https://secure.php.net/date 2: Post permalink */
		9  => sprintf( __( 'Gemstones scheduled for: <strong>%1$s</strong>. <a target="_blank" href="%2$s">Preview gemstones</a>', 'twentytwentyfive' ), date_i18n( __( 'M j, Y @ G:i', 'twentytwentyfive' ), strtotime( $post->post_date ) ), esc_url( $permalink ) ),
		/* translators: %s: post permalink */
		10 => sprintf( __( 'Gemstones draft updated. <a target="_blank" href="%s">Preview gemstones</a>', 'twentytwentyfive' ), esc_url( add_query_arg( 'preview', 'true', $permalink ) ) ),
	);

	return $messages;
}

add_filter( 'post_updated_messages', 'twentytwentyfive_updated_messages' );

/**
 * Sets the bulk post updated messages for the `gemstones` post type.
 *
 * @param  array $bulk_messages Arrays of messages, each keyed by the corresponding post type. Messages are
 *                              keyed with 'updated', 'locked', 'deleted', 'trashed', and 'untrashed'.
 * @param  int[] $bulk_counts   Array of item counts for each message, used to build internationalized strings.
 * @return array Bulk messages for the `gemstones` post type.
 */
function twentytwentyfive_bulk_updated_messages( $bulk_messages, $bulk_counts ) {
	global $post;

	$bulk_messages['gemstones'] = array(
		/* translators: %s: Number of gemstones. */
		'updated'   => _n( '%s gemstones updated.', '%s gemstones updated.', $bulk_counts['updated'], 'twentytwentyfive' ),
		'locked'    => ( 1 === $bulk_counts['locked'] ) ? __( '1 gemstones not updated, somebody is editing it.', 'twentytwentyfive' ) :
						/* translators: %s: Number of gemstones. */
						_n( '%s gemstones not updated, somebody is editing it.', '%s gemstones not updated, somebody is editing them.', $bulk_counts['locked'], 'twentytwentyfive' ),
		/* translators: %s: Number of gemstones. */
		'deleted'   => _n( '%s gemstones permanently deleted.', '%s gemstones permanently deleted.', $bulk_counts['deleted'], 'twentytwentyfive' ),
		/* translators: %s: Number of gemstones. */
		'trashed'   => _n( '%s gemstones moved to the Trash.', '%s gemstones moved to the Trash.', $bulk_counts['trashed'], 'twentytwentyfive' ),
		/* translators: %s: Number of gemstones. */
		'untrashed' => _n( '%s gemstones restored from the Trash.', '%s gemstones restored from the Trash.', $bulk_counts['untrashed'], 'twentytwentyfive' ),
	);

	return $bulk_messages;
}

add_filter( 'bulk_post_updated_messages', 'twentytwentyfive_bulk_updated_messages', 10, 2 );
