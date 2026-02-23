<?php
/**
 * Plugin Name: PMW Seed Data
 * Description: One-time seed plugin for Precious Market Watch. Creates all dealers,
 *              affiliate products, and homepage settings. DEACTIVATE AND DELETE after running.
 * Version:     1.0.0
 * Author:      Markus Mikely
 */

if ( ! defined( 'ABSPATH' ) ) exit;

register_activation_hook( __FILE__, 'pmw_seed_all' );

function pmw_seed_all() {
    pmw_seed_dealers();
    pmw_seed_homepage();
}

// ─────────────────────────────────────────────────────────────
// DEALERS
// ─────────────────────────────────────────────────────────────

function pmw_seed_dealers() {

    $dealers = [
        [
            'name'             => 'Money Metals Exchange',
            'description'      => 'One of the most trusted online dealers for gold, silver, platinum and palladium bullion. Known for competitive pricing, transparent fees and a 30-day affiliate cookie window via AWIN.',
            'rating'           => 4.0,
            'review_link'      => '',
            'affiliate_link'   => '',
            'commission'       => '~$16 per sale (flat fee)',
            'network'          => 'AWIN',
            'metals'           => [ 'Gold', 'Silver', 'Platinum', 'Palladium' ],
            'gemstones'        => [],
            'attributes'       => [ 'Banners', 'Text Links', '30-day cookie' ],
            'category'         => 'Bullion Dealer',
            'featured'         => false,
        ],
        [
            'name'             => 'GoldenCrest Metals',
            'description'      => 'Premium precious metals dealer offering some of the highest affiliate commissions in the industry — up to 13% on premiums. Managed through Everflow.',
            'rating'           => 5.0,
            'review_link'      => '',
            'affiliate_link'   => '',
            'commission'       => '3–13% on premiums',
            'network'          => 'Everflow',
            'metals'           => [ 'Gold', 'Silver', 'Platinum', 'Palladium' ],
            'gemstones'        => [],
            'attributes'       => [ 'High commission', 'Everflow network' ],
            'category'         => 'Bullion Dealer',
            'featured'         => true,
        ],
        [
            'name'             => 'Augusta Precious Metals',
            'description'      => 'Specialist in gold and silver IRAs. Offers one of the most lucrative affiliate structures in the space — $200 per qualified lead plus up to 10% commission on sales.',
            'rating'           => 4.0,
            'review_link'      => '',
            'affiliate_link'   => '',
            'commission'       => '8–10% + $200 per qualified lead',
            'network'          => 'Direct',
            'metals'           => [ 'Gold', 'Silver' ],
            'gemstones'        => [],
            'attributes'       => [ 'IRA specialist', '$200 lead bonus', 'High AOV' ],
            'category'         => 'Bullion Dealer',
            'featured'         => true,
        ],
        [
            'name'             => 'Hatton Garden Metals',
            'description'      => 'UK-based precious metals dealer based in London\'s famous jewellery quarter. Free to join affiliate scheme, ideal for UK-focused audiences.',
            'rating'           => 3.0,
            'review_link'      => '',
            'affiliate_link'   => '',
            'commission'       => 'Varies',
            'network'          => 'Direct',
            'metals'           => [ 'Gold', 'Silver' ],
            'gemstones'        => [],
            'attributes'       => [ 'UK-based', 'Free to join' ],
            'category'         => 'Bullion Dealer',
            'featured'         => false,
        ],
        [
            'name'             => 'GoldRepublic',
            'description'      => 'European precious metals platform offering up to 25% commission and an industry-leading 60-day cookie window. Strong choice for international audiences.',
            'rating'           => 4.0,
            'review_link'      => '',
            'affiliate_link'   => '',
            'commission'       => 'Up to 25%',
            'network'          => 'Direct',
            'metals'           => [ 'Gold', 'Silver', 'Platinum' ],
            'gemstones'        => [],
            'attributes'       => [ '25% commission', '60-day cookie', 'European' ],
            'category'         => 'Bullion Dealer',
            'featured'         => false,
        ],
        [
            'name'             => 'BGASC',
            'description'      => 'Buy Gold and Silver Coins — a reputable US bullion dealer with a solid range of coins and bars across all four precious metals. Managed via ShareASale.',
            'rating'           => 4.0,
            'review_link'      => '',
            'affiliate_link'   => '',
            'commission'       => 'Up to $25 per sale',
            'network'          => 'ShareASale',
            'metals'           => [ 'Gold', 'Silver', 'Platinum', 'Palladium' ],
            'gemstones'        => [],
            'attributes'       => [ 'ShareASale', 'Flat fee per sale' ],
            'category'         => 'Bullion Dealer',
            'featured'         => false,
        ],
        [
            'name'             => 'Allurez',
            'description'      => 'Fine jewellery retailer specialising in diamonds, gemstones and designer pieces. Weekly promotional materials and banner ads available via ShareASale.',
            'rating'           => 4.0,
            'review_link'      => '',
            'affiliate_link'   => '',
            'commission'       => '~8%',
            'network'          => 'ShareASale',
            'metals'           => [],
            'gemstones'        => [ 'Diamond', 'Gemstones' ],
            'attributes'       => [ 'Weekly promotions', 'Banner ads', 'ShareASale' ],
            'category'         => 'Jeweler',
            'featured'         => false,
        ],
        [
            'name'             => 'Blue Nile',
            'description'      => 'The world\'s largest online diamond retailer. Exceptional brand recognition, high average order values and a trusted name for engagement rings and fine jewellery.',
            'rating'           => 4.0,
            'review_link'      => '',
            'affiliate_link'   => '',
            'commission'       => '~5%',
            'network'          => 'Impact',
            'metals'           => [],
            'gemstones'        => [ 'Diamond', 'Gemstones' ],
            'attributes'       => [ 'Largest online jeweler', 'High AOV', 'Impact network' ],
            'category'         => 'Jeweler',
            'featured'         => true,
        ],
        [
            'name'             => 'Gemvara',
            'description'      => 'Custom jewellery platform letting customers design their own pieces from a wide range of gemstones and precious metals. Managed through CJ Affiliate / Impact.',
            'rating'           => 4.0,
            'review_link'      => '',
            'affiliate_link'   => '',
            'commission'       => '2–6%',
            'network'          => 'CJ / Impact',
            'metals'           => [],
            'gemstones'        => [ 'Gemstones' ],
            'attributes'       => [ 'Custom jewelry', 'CJ Affiliate' ],
            'category'         => 'Jeweler',
            'featured'         => false,
        ],
        [
            'name'             => 'Clean Origin',
            'description'      => 'Ethical lab-grown diamond specialist with a 90-day cookie window. Growing demand for sustainable diamonds makes this a strong long-term affiliate choice.',
            'rating'           => 4.0,
            'review_link'      => '',
            'affiliate_link'   => '',
            'commission'       => '~5%',
            'network'          => 'ShareASale',
            'metals'           => [],
            'gemstones'        => [ 'Diamond' ],
            'attributes'       => [ 'Lab-grown', 'Ethical', '90-day cookie', 'ShareASale' ],
            'category'         => 'Jeweler',
            'featured'         => false,
        ],
        [
            'name'             => 'Angara',
            'description'      => 'Specialist in coloured gemstone jewellery — sapphires, rubies, emeralds and diamonds. 10% commission via LinkShare/Rakuten with strong visual product assets.',
            'rating'           => 4.0,
            'review_link'      => '',
            'affiliate_link'   => '',
            'commission'       => '10%',
            'network'          => 'Rakuten / LinkShare',
            'metals'           => [],
            'gemstones'        => [ 'Sapphire', 'Ruby', 'Emerald', 'Diamond' ],
            'attributes'       => [ '10% commission', 'Rakuten network', 'Coloured gems' ],
            'category'         => 'Jeweler',
            'featured'         => false,
        ],
        [
            'name'             => 'James Allen',
            'description'      => 'Premium online diamond and gemstone retailer famous for 360° diamond viewing technology. High average order values make even a 5% commission highly rewarding.',
            'rating'           => 4.0,
            'review_link'      => '',
            'affiliate_link'   => '',
            'commission'       => '~5%',
            'network'          => 'Post Affiliate Pro',
            'metals'           => [],
            'gemstones'        => [ 'Diamond', 'Gemstones' ],
            'attributes'       => [ '360° imagery', 'High AOV', 'Post Affiliate Pro' ],
            'category'         => 'Jeweler',
            'featured'         => true,
        ],
        [
            'name'             => 'Ritani',
            'description'      => 'Hybrid online/in-store diamond jeweller offering a unique try-before-you-buy experience. Lower commission rate but strong brand for US audiences via Rakuten.',
            'rating'           => 3.0,
            'review_link'      => '',
            'affiliate_link'   => '',
            'commission'       => '~1%',
            'network'          => 'Rakuten',
            'metals'           => [],
            'gemstones'        => [ 'Diamond', 'Gemstones' ],
            'attributes'       => [ 'In-store option', 'Rakuten network' ],
            'category'         => 'Jeweler',
            'featured'         => false,
        ],
    ];

    foreach ( $dealers as $dealer ) {

        // Skip if already exists
        $existing = get_posts( [
            'post_type'  => 'dealer',
            'title'      => $dealer['name'],
            'post_status' => 'any',
            'numberposts' => 1,
        ] );
        if ( ! empty( $existing ) ) continue;

        $post_id = wp_insert_post( [
            'post_title'   => $dealer['name'],
            'post_content' => $dealer['description'],
            'post_type'    => 'dealer',
            'post_status'  => 'publish',
        ] );

        if ( is_wp_error( $post_id ) ) continue;

        // ACF fields
        update_field( 'short_description',  $dealer['description'],    $post_id );
        update_field( 'rating',             $dealer['rating'],         $post_id );
        update_field( 'review_link',        $dealer['review_link'],    $post_id );
        update_field( 'affiliate_link',     $dealer['affiliate_link'], $post_id );
        update_field( 'featured',           $dealer['featured'],       $post_id );

        // Store commission + network as post meta for later use
        update_post_meta( $post_id, 'pmw_commission',      $dealer['commission'] );
        update_post_meta( $post_id, 'pmw_network',         $dealer['network'] );
        update_post_meta( $post_id, 'pmw_signed_up',       false );

        // Taxonomy: dealer category
        if ( ! empty( $dealer['category'] ) ) {
            wp_set_object_terms( $post_id, $dealer['category'], 'pmw-dealer-category' );
        }

        // Taxonomy: metal types
        if ( ! empty( $dealer['metals'] ) ) {
            wp_set_object_terms( $post_id, $dealer['metals'], 'pmw-metal-type' );
        }

        // Taxonomy: gemstone types
        if ( ! empty( $dealer['gemstones'] ) ) {
            wp_set_object_terms( $post_id, $dealer['gemstones'], 'pmw-gemstone-type' );
        }
    }
}

// ─────────────────────────────────────────────────────────────
// HOMEPAGE SETTINGS
// ─────────────────────────────────────────────────────────────

function pmw_seed_homepage() {

    // Find or create the homepage page
    $homepage = get_posts( [
        'post_type'   => 'page',
        'title'       => 'Home',
        'post_status' => 'publish',
        'numberposts' => 1,
    ] );

    if ( empty( $homepage ) ) {
        $page_id = wp_insert_post( [
            'post_title'   => 'Home',
            'post_type'    => 'page',
            'post_status'  => 'publish',
            'post_content' => '',
        ] );
    } else {
        $page_id = $homepage[0]->ID;
    }

    // Set as front page
    update_option( 'show_on_front', 'page' );
    update_option( 'page_on_front', $page_id );

    // Seed ACF homepage hero fields
    update_field( 'hero', [
        'title'            => 'Trusted Insights for Precious Metals & Gemstones',
        'subtitle'         => 'Your authoritative source for gold, silver, platinum, diamonds, and fine gemstones. Expert analysis, market data, and investment guidance from industry specialists.',
        'background_image' => null,
    ], $page_id );

    update_field( 'newsletter', [
        'email' => '',
    ], $page_id );
}
