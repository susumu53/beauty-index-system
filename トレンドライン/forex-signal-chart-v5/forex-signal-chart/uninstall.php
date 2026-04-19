<?php
if(!defined('WP_UNINSTALL_PLUGIN'))exit;
global $wpdb;
$wpdb->query("DELETE FROM {$wpdb->options} WHERE option_name LIKE '_transient_fsc_%' OR option_name LIKE '_transient_timeout_fsc_%'");
foreach(['fsc_cache_ttl','fsc_default_symbol','fsc_default_tf','fsc_height','fsc_signals','fsc_refresh']as $k)delete_option($k);
