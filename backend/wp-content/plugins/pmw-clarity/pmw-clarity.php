<?php
/**
 * Plugin Name: PMW Clarity
 * Description: Adds a link to the Microsoft Clarity dashboard in the WordPress admin. Tracking is handled by the frontend (React) with consent; this plugin does not inject the Clarity script.
 * Version:     1.0.0
 * Author:      Precious Market Watch
 * License:     GPL-2.0+
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

const PMW_CLARITY_OPTION_ID = 'pmw_clarity_project_id';
const PMW_CLARITY_DEFAULT_ID = 'vmezs6szy4';

add_action( 'admin_menu', 'pmw_clarity_admin_menu' );
add_action( 'admin_init', 'pmw_clarity_register_setting' );

function pmw_clarity_admin_menu() {
	add_options_page(
		__( 'Microsoft Clarity', 'pmw-clarity' ),
		__( 'Clarity', 'pmw-clarity' ),
		'manage_options',
		'pmw-clarity',
		'pmw_clarity_options_page'
	);
}

function pmw_clarity_register_setting() {
	register_setting( 'pmw_clarity_options', PMW_CLARITY_OPTION_ID, [
		'type'              => 'string',
		'sanitize_callback' => 'sanitize_text_field',
	] );
}

function pmw_clarity_get_project_id() {
	$id = get_option( PMW_CLARITY_OPTION_ID, '' );
	return $id !== '' ? $id : PMW_CLARITY_DEFAULT_ID;
}

function pmw_clarity_dashboard_url() {
	return 'https://clarity.microsoft.com/projects/view/' . pmw_clarity_get_project_id();
}

function pmw_clarity_options_page() {
	$project_id = pmw_clarity_get_project_id();
	$dashboard_url = pmw_clarity_dashboard_url();
	?>
	<div class="wrap">
		<h1><?php esc_html_e( 'Microsoft Clarity', 'pmw-clarity' ); ?></h1>
		<p><?php esc_html_e( 'View your Clarity dashboard (heatmaps, session recordings) for this site. Tracking is implemented in the frontend application with cookie consent; this plugin does not inject the Clarity script.', 'pmw-clarity' ); ?></p>

		<form method="post" action="options.php">
			<?php settings_fields( 'pmw_clarity_options' ); ?>
			<table class="form-table">
				<tr>
					<th scope="row"><label for="<?php echo esc_attr( PMW_CLARITY_OPTION_ID ); ?>"><?php esc_html_e( 'Project ID', 'pmw-clarity' ); ?></label></th>
					<td>
						<input type="text" id="<?php echo esc_attr( PMW_CLARITY_OPTION_ID ); ?>" name="<?php echo esc_attr( PMW_CLARITY_OPTION_ID ); ?>" value="<?php echo esc_attr( $project_id ); ?>" class="regular-text" />
						<p class="description"><?php esc_html_e( 'Your Clarity project ID (e.g. vmezs6szy4). Used only for the dashboard link below.', 'pmw-clarity' ); ?></p>
					</td>
				</tr>
			</table>
			<?php submit_button(); ?>
		</form>

		<p>
			<a href="<?php echo esc_url( $dashboard_url ); ?>" target="_blank" rel="noopener noreferrer" class="button button-primary">
				<?php esc_html_e( 'Open Clarity dashboard', 'pmw-clarity' ); ?> →
			</a>
		</p>
	</div>
	<?php
}
