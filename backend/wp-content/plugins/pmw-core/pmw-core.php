<?php
/**
 * Plugin Name: PMW Core
 * Plugin URI:  https://preciousmarketwatch.com
 * Description: Core plugin for Precious Market Watch. Registers all custom post types, taxonomies, ACF field groups, and seeds default terms.
 * Version:     1.0.0
 * Author:      Markus Mikely
 * License:     GPL-2.0+
 */

if ( ! defined( 'ABSPATH' ) ) exit;

// ─────────────────────────────────────────────
// 1. CUSTOM POST TYPES
// ─────────────────────────────────────────────

add_action( 'init', 'pmw_register_post_types' );

function pmw_register_post_types() {

    // ── Market Insight ──────────────────────
    register_post_type( 'market-insight', [
        'labels' => [
            'name'               => 'Market Insights',
            'singular_name'      => 'Market Insight',
            'add_new_item'       => 'Add New Market Insight',
            'edit_item'          => 'Edit Market Insight',
            'new_item'           => 'New Market Insight',
            'view_item'          => 'View Market Insight',
            'search_items'       => 'Search Market Insights',
            'not_found'          => 'No Market Insights found',
        ],
        'public'              => true,
        'has_archive'         => true,
        'rewrite'             => [ 'slug' => 'market-insights' ],
        'supports'            => [ 'title', 'editor', 'excerpt', 'thumbnail', 'author', 'custom-fields' ],
        'menu_icon'           => 'dashicons-chart-line',
        'show_in_rest'        => true,
        // WPGraphQL
        'show_in_graphql'     => true,
        'graphql_single_name' => 'marketInsight',
        'graphql_plural_name' => 'marketInsights',
    ] );

    // ── Dealer ──────────────────────────────
    register_post_type( 'dealer', [
        'labels' => [
            'name'          => 'Dealers',
            'singular_name' => 'Dealer',
            'add_new_item'  => 'Add New Dealer',
            'edit_item'     => 'Edit Dealer',
        ],
        'public'              => true,
        'has_archive'         => true,
        'rewrite'             => [ 'slug' => 'dealers' ],
        'supports'            => [ 'title', 'editor', 'excerpt', 'thumbnail', 'custom-fields' ],
        'menu_icon'           => 'dashicons-store',
        'show_in_rest'        => true,
        'show_in_graphql'     => true,
        'graphql_single_name' => 'dealer',
        'graphql_plural_name' => 'dealers',
    ] );

    // ── Affiliate Product ───────────────────
    register_post_type( 'affiliate-product', [
        'labels' => [
            'name'          => 'Affiliate Products',
            'singular_name' => 'Affiliate Product',
            'add_new_item'  => 'Add New Affiliate Product',
            'edit_item'     => 'Edit Affiliate Product',
        ],
        'public'              => true,
        'has_archive'         => true,
        'rewrite'             => [ 'slug' => 'products' ],
        'supports'            => [ 'title', 'editor', 'excerpt', 'thumbnail', 'custom-fields' ],
        'menu_icon'           => 'dashicons-tag',
        'show_in_rest'        => true,
        'show_in_graphql'     => true,
        'graphql_single_name' => 'affiliateProduct',
        'graphql_plural_name' => 'affiliateProducts',
    ] );
}


// ─────────────────────────────────────────────
// 2. CUSTOM TAXONOMIES
// ─────────────────────────────────────────────

add_action( 'init', 'pmw_register_taxonomies' );

function pmw_register_taxonomies() {

    // ── Topic (for posts + market insights) ─
    register_taxonomy( 'pmw-topic', [ 'post', 'market-insight' ], [
        'labels' => [
            'name'          => 'Topics',
            'singular_name' => 'Topic',
            'search_items'  => 'Search Topics',
            'all_items'     => 'All Topics',
            'edit_item'     => 'Edit Topic',
            'add_new_item'  => 'Add New Topic',
        ],
        'hierarchical'    => true,
        'public'          => true,
        'rewrite'         => [ 'slug' => 'topic' ],
        'show_in_rest'    => true,
        'show_in_graphql' => true,
        'graphql_single_name' => 'topic',
        'graphql_plural_name' => 'topics',
    ] );

    // ── Metal Type (for all content types) ─
    register_taxonomy( 'pmw-metal-type', [ 'post', 'market-insight', 'dealer', 'affiliate-product' ], [
        'labels' => [
            'name'          => 'Metal Types',
            'singular_name' => 'Metal Type',
            'add_new_item'  => 'Add New Metal Type',
        ],
        'hierarchical'    => false,
        'public'          => true,
        'rewrite'         => [ 'slug' => 'metal' ],
        'show_in_rest'    => true,
        'show_in_graphql' => true,
        'graphql_single_name' => 'metalType',
        'graphql_plural_name' => 'metalTypes',
    ] );

    // ── Gemstone Type (for all content types) ─
    register_taxonomy( 'pmw-gemstone-type', [ 'post', 'market-insight', 'dealer', 'affiliate-product' ], [
        'labels' => [
            'name'          => 'Gemstone Types',
            'singular_name' => 'Gemstone Type',
            'add_new_item'  => 'Add New Gemstone Type',
        ],
        'hierarchical'    => false,
        'public'          => true,
        'rewrite'         => [ 'slug' => 'gemstone' ],
        'show_in_rest'    => true,
        'show_in_graphql' => true,
        'graphql_single_name' => 'gemstoneType',
        'graphql_plural_name' => 'gemstoneTypes',
    ] );

    // ── Dealer Category ──────────────────────
    register_taxonomy( 'pmw-dealer-category', [ 'dealer' ], [
        'labels' => [
            'name'          => 'Dealer Categories',
            'singular_name' => 'Dealer Category',
            'add_new_item'  => 'Add New Dealer Category',
        ],
        'hierarchical'    => true,
        'public'          => true,
        'rewrite'         => [ 'slug' => 'dealer-category' ],
        'show_in_rest'    => true,
        'show_in_graphql' => true,
        'graphql_single_name' => 'dealerCategory',
        'graphql_plural_name' => 'dealerCategories',
    ] );
}


// ─────────────────────────────────────────────
// 3. SEED DEFAULT TERMS (runs once on activation)
// ─────────────────────────────────────────────

register_activation_hook( __FILE__, 'pmw_seed_terms' );

function pmw_seed_terms() {

    $topics = [
        'Precious Metals',
        'Gemstones',
        'Jewelry Investment',
        'Market Insights',
        'Buying Guides',
        'Investment Strategy',
        'Industry News',
    ];
    foreach ( $topics as $term ) {
        if ( ! term_exists( $term, 'pmw-topic' ) ) {
            wp_insert_term( $term, 'pmw-topic' );
        }
    }

    $metals = [ 'Gold', 'Silver', 'Platinum', 'Palladium' ];
    foreach ( $metals as $term ) {
        if ( ! term_exists( $term, 'pmw-metal-type' ) ) {
            wp_insert_term( $term, 'pmw-metal-type' );
        }
    }

    $gemstones = [ 'Diamond', 'Ruby', 'Sapphire', 'Emerald' ];
    foreach ( $gemstones as $term ) {
        if ( ! term_exists( $term, 'pmw-gemstone-type' ) ) {
            wp_insert_term( $term, 'pmw-gemstone-type' );
        }
    }

    $dealer_cats = [ 'Bullion Dealer', 'Jeweler', 'Online Marketplace', 'Auction House' ];
    foreach ( $dealer_cats as $term ) {
        if ( ! term_exists( $term, 'pmw-dealer-category' ) ) {
            wp_insert_term( $term, 'pmw-dealer-category' );
        }
    }
}


// ─────────────────────────────────────────────
// 4. ACF FIELD GROUPS
// ─────────────────────────────────────────────

add_action( 'acf/init', 'pmw_register_acf_fields' );

function pmw_register_acf_fields() {

    if ( ! function_exists( 'acf_add_local_field_group' ) ) return;

    // ── Dealer Fields ────────────────────────
    acf_add_local_field_group( [
        'key'    => 'group_dealer_fields',
        'title'  => 'Dealer Details',
        'fields' => [
            [
                'key'              => 'field_dealer_short_description',
                'label'            => 'Short Description',
                'name'             => 'short_description',
                'type'             => 'textarea',
                'rows'             => 3,
                'show_in_graphql'  => 1,
                'graphql_field_name' => 'shortDescription',
            ],
            [
                'key'              => 'field_dealer_rating',
                'label'            => 'Rating',
                'name'             => 'rating',
                'type'             => 'number',
                'min'              => 0,
                'max'              => 5,
                'step'             => 0.1,
                'show_in_graphql'  => 1,
                'graphql_field_name' => 'rating',
            ],
            [
                'key'              => 'field_dealer_review_link',
                'label'            => 'Review Link',
                'name'             => 'review_link',
                'type'             => 'url',
                'show_in_graphql'  => 1,
                'graphql_field_name' => 'reviewLink',
            ],
            [
                'key'              => 'field_dealer_affiliate_link',
                'label'            => 'Affiliate Link',
                'name'             => 'affiliate_link',
                'type'             => 'url',
                'show_in_graphql'  => 1,
                'graphql_field_name' => 'affiliateLink',
            ],
            [
                'key'              => 'field_dealer_logo',
                'label'            => 'Logo',
                'name'             => 'logo',
                'type'             => 'image',
                'return_format'    => 'array',
                'show_in_graphql'  => 1,
                'graphql_field_name' => 'logo',
            ],
            [
                'key'              => 'field_dealer_featured',
                'label'            => 'Featured',
                'name'             => 'featured',
                'type'             => 'true_false',
                'ui'               => 1,
                'show_in_graphql'  => 1,
                'graphql_field_name' => 'featured',
            ],
        ],
        'location' => [
            [ [ 'param' => 'post_type', 'operator' => '==', 'value' => 'dealer' ] ],
        ],
        'show_in_graphql'     => 1,
        'graphql_field_name'  => 'dealers',
    ] );

    // ── Affiliate Product Fields ─────────────
    acf_add_local_field_group( [
        'key'    => 'group_affiliate_product_fields',
        'title'  => 'Product Details',
        'fields' => [
            [
                'key'   => 'field_product_price',
                'label' => 'Price',
                'name'  => 'price',
                'type'  => 'text',
                'show_in_graphql' => 1,
            ],
            [
                'key'              => 'field_product_original_price',
                'label'            => 'Original Price',
                'name'             => 'original_price',
                'type'             => 'text',
                'show_in_graphql'  => 1,
                'graphql_field_name' => 'originalPrice',
            ],
            [
                'key'              => 'field_product_affiliate_link',
                'label'            => 'Affiliate Link',
                'name'             => 'affiliate_link',
                'type'             => 'url',
                'show_in_graphql'  => 1,
                'graphql_field_name' => 'affiliateLink',
            ],
            [
                'key'              => 'field_product_dealer_name',
                'label'            => 'Dealer Name',
                'name'             => 'dealer_name',
                'type'             => 'text',
                'show_in_graphql'  => 1,
                'graphql_field_name' => 'dealerName',
            ],
            [
                'key'   => 'field_product_badge',
                'label' => 'Badge (e.g. Best Seller)',
                'name'  => 'badge',
                'type'  => 'text',
                'show_in_graphql' => 1,
            ],
            [
                'key'   => 'field_product_features',
                'label' => 'Features',
                'name'  => 'features',
                'type'  => 'textarea',
                'instructions' => 'One feature per line (e.g. IRA Eligible)',
                'show_in_graphql' => 1,
            ],
        ],
        'location' => [
            [ [ 'param' => 'post_type', 'operator' => '==', 'value' => 'affiliate-product' ] ],
        ],
        'show_in_graphql'    => 1,
        'graphql_field_name' => 'productDetails',
    ] );

    // ── Market Insight Fields ────────────────
    acf_add_local_field_group( [
        'key'    => 'group_market_insight_fields',
        'title'  => 'Article Meta',
        'fields' => [
            [
                'key'              => 'field_insight_read_time',
                'label'            => 'Read Time',
                'name'             => 'read_time',
                'type'             => 'text',
                'placeholder'      => '5 min read',
                'show_in_graphql'  => 1,
                'graphql_field_name' => 'readTime',
            ],
            [
                'key'   => 'field_insight_sponsored',
                'label' => 'Sponsored',
                'name'  => 'sponsored',
                'type'  => 'true_false',
                'ui'    => 1,
                'show_in_graphql' => 1,
            ],
        ],
        'location' => [
            [ [ 'param' => 'post_type', 'operator' => '==', 'value' => 'market-insight' ] ],
            [ [ 'param' => 'post_type', 'operator' => '==', 'value' => 'post' ] ],
        ],
        'show_in_graphql'    => 1,
        'graphql_field_name' => 'articleMeta',
    ] );

    // ── Homepage Settings ────────────────────
    acf_add_local_field_group( [
        'key'    => 'group_homepage_settings',
        'title'  => 'Homepage Settings',
        'fields' => [
            [
                'key'   => 'field_homepage_hero',
                'label' => 'Hero',
                'name'  => 'hero',
                'type'  => 'group',
                'show_in_graphql' => 1,
                'sub_fields' => [
                    [
                        'key'   => 'field_hero_title',
                        'label' => 'Title',
                        'name'  => 'title',
                        'type'  => 'text',
                        'show_in_graphql' => 1,
                    ],
                    [
                        'key'   => 'field_hero_subtitle',
                        'label' => 'Subtitle',
                        'name'  => 'subtitle',
                        'type'  => 'textarea',
                        'rows'  => 2,
                        'show_in_graphql' => 1,
                    ],
                    [
                        'key'              => 'field_hero_background_image',
                        'label'            => 'Background Image',
                        'name'             => 'background_image',
                        'type'             => 'image',
                        'return_format'    => 'array',
                        'show_in_graphql'  => 1,
                        'graphql_field_name' => 'backgroundImage',
                    ],
                ],
            ],
            [
                'key'   => 'field_homepage_newsletter',
                'label' => 'Newsletter',
                'name'  => 'newsletter',
                'type'  => 'group',
                'show_in_graphql' => 1,
                'sub_fields' => [
                    [
                        'key'   => 'field_newsletter_email',
                        'label' => 'Signup Email (Mailchimp etc.)',
                        'name'  => 'email',
                        'type'  => 'email',
                        'show_in_graphql' => 1,
                    ],
                ],
            ],
        ],
        'location' => [
            [ [ 'param' => 'page_type', 'operator' => '==', 'value' => 'front_page' ] ],
        ],
        'show_in_graphql'    => 1,
        'graphql_field_name' => 'homepageSettings',
    ] );
}
