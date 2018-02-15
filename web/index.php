<!DOCTYPE html>
<html lang="en">
<head>
	<meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
	<meta http-equiv="X-UA-Compatible" content="IE=edge" />
	<meta name="viewport" content="width=device-width, initial-scale=1">
	<meta name="fragment" content="!" />
	<meta name="medium" content="image" />
	<?php
		$jsonString = file_get_contents('cache/options.json');
		$options = json_decode($jsonString, true);

		// Check if an option is true or 1
		function is_option_set($option_name) {
			global $options;
			return strcasecmp($options[$option_name], "true") == 0 || $options[$option_name] == "1";
		}

		// Check if an option as a list contains a given value
		function has_option_value($option_name, $option_value) {
			global $options;
			return stripos($options[$option_name], $option_value) !== false;
		}
	?>
	<title><?php if ($options['page_title'])
			echo $options['page_title']; ?></title>
	<link rel="icon" href="favicon.ico" type="image/x-icon"/>

	<?php	if (strcasecmp($options['debug_css'], "false") == 0 || $options['debug_css'] == "0") { ?>
		<link href="css/styles.min.css" rel="stylesheet" type="text/css" />
	<?php	} else { ?>
		<link href="css/000-controls.css" rel="stylesheet" type="text/css" />
		<link href="css/001-fonts.css" rel="stylesheet" type="text/css" />
		<link href="css/002-mobile.css" rel="stylesheet" type="text/css" />
		<link href="css/003-social.css" rel="stylesheet" type="text/css" />
	<?php	}

			if (strcasecmp($options['debug_js'], "false") == 0 || $options['debug_js'] == "0") { ?>
		<script type="text/javascript" src="js/scripts.min.js"></script>
	<?php	} else {
			// Use system wide jQuery if available
			if (file_exists("/usr/share/javascript/jquery/jquery.js")) { ?>
		<script type="text/javascript" src="/javascript/jquery/jquery.js"></script>
	<?php	} else { ?>
		<script type="text/javascript" src="js/000-jquery-1.12.4.js"></script>
	<?php	}

		// jQuery-hashchange should be in Debian! ?>
		<script type="text/javascript" src="js/001-hashchange.js"></script>

		<script type="text/javascript" src="js/002-preloadimages.js"></script>

	<?php
			// Use system wide jQuery-mousewheel if available
			if (file_exists("/usr/share/javascript/jquery-mousewheel/jquery.mousewheel.js")) { ?>
		<script type="text/javascript" src="/javascript/jquery-mousewheel/jquery.mousewheel.js"></script>
	<?php	} else { ?>
		<script type="text/javascript" src="js/003-mousewheel.js"></script>
	<?php	}

			// Use system wide jQuery-fullscreen if available
			if (file_exists("/usr/share/javascript/jquery-fullscreen/jquery.fullscreen.js")) { ?>
		<script type="text/javascript" src="/javascript/jquery-fullscreen/jquery.fullscreen.js"></script>
	<?php	} else { ?>
		<script type="text/javascript" src="js/004-fullscreen.js"></script>
	<?php	}

			// Use system wide modernizr if available
			if (file_exists("/usr/share/javascript/modernizr/modernizr.min.js")) { ?>
		<script type="text/javascript" src="/javascript/modernizr/modernizr.min.js"></script>
	<?php	} else { ?>
		<script type="text/javascript" src="js/005-modernizr.js"></script>
	<?php	} ?>

		<script type="text/javascript" src="js/006-latinize.js"></script>
		<script type="text/javascript" src="js/008-social.js"></script>
		<script type="text/javascript" src="js/009-translations.js"></script>
		<script type="text/javascript" src="js/010-libphotofloat.js"></script>
		<script type="text/javascript" src="js/012-display.js"></script>
	<?php } ?>

	<?php
		//~ ini_set('display_errors', 1);
		//~ error_reporting(E_ALL);
		// from http://skills2earn.blogspot.it/2012/01/how-to-check-if-file-exists-on.html , solution # 3
		function url_exist($url) {
			if (@fopen($url,"r"))
				return true;
			else
				return false;
		}

		// put the <link rel=".."> tag in <head> for letting facebook/google+ load the image/video when sharing
		if (isset($_GET['m']) && $_GET['m']) {
			// Prevent directory traversal security vulnerability
			$realPath = realpath($_GET['m']);
			if (strpos($realPath, realpath('cache')) === 0  && url_exist($realPath)) {
				$linkTag = '<link rel="';
				$videoEnd = ".mp4";
				if (substr($_GET['m'], - strlen($videoEnd)) === strlen($videoEnd))
					// video
					$linkTag .= 'video_src';
				else
					// image
					$linkTag .= 'image_src';
				$linkTag .= '" href="' . $_GET['m'] . '"';
				$linkTag .= '>';
				echo "$linkTag\n";
			}
		}
	?>

	<?php if ($options['piwik_server'] && $options['piwik_id']) { ?>
		<!-- Piwik -->
		<script type="text/javascript">
			var _paq = _paq || [];
			_paq.push(['trackPageView']);
			_paq.push(['enableLinkTracking']);
			(function() {
				var u="<?php echo $options['piwik_server']; ?>";
				_paq.push(['setTrackerUrl', u+'piwik.php']);
				_paq.push(['setSiteId', '<?php echo $options['piwik_id']; ?>']);
				var d=document, g=d.createElement('script'), s=d.getElementsByTagName('script')[0];
				g.type='text/javascript'; g.async=true; g.defer=true; g.src=u+'piwik.js'; s.parentNode.insertBefore(g,s);
			})();
			// from https://piwik.org/blog/2017/02/how-to-track-single-page-websites-using-piwik-analytics/
			$(document).ready(function() {
				$(window).hashchange(function() {
					_paq.push(['setCustomUrl', '/' + window.location.hash]);
					_paq.push(['setDocumentTitle', PhotoFloat.cleanHash(location.hash)]);
					_paq.push(['trackPageView']);
				});
			});
		</script>
		<noscript><p><img src="<?php echo $options['piwik_server'] . 'piwik.php?idsite=' . $options['piwik_id']; ?>" style="border:0;" alt="" /></p></noscript>
		<!-- End Piwik Code -->
	<?php } ?>

	<?php if (isset($options['google_analytics_id']) && $options['google_analytics_id']) { ?>
		<!-- google analytics -->
		<script type="text/javascript">
			// from https://git.zx2c4.com/PhotoFloat/tree/web/js/999-googletracker.js
			window._gaq = window._gaq || [];
			window._gaq.push(['_setAccount', '<?php echo $options['google_analytics_id']; ?>']);
			var ga = document.createElement('script');
			ga.type = 'text/javascript';
			ga.async = true;
			ga.src = ('https:' == document.location.protocol ? 'https://ssl' : 'http://www') + '.google-analytics.com/ga.js';
			var s = document.getElementsByTagName('script')[0];
			s.parentNode.insertBefore(ga, s);
			$(document).ready(function() {
				$(window).hashchange(function() {
					window._gaq = window._gaq || [];
					window._gaq.push(['_trackPageview']);
					window._gaq.push(['_trackPageview', PhotoFloat.cleanHash(location.hash)]);
				});
			});
		</script>
		<!-- End google analytics code -->
	<?php } ?>
</head>
<body>
	<?php
		if ($_GET)
			// redirect to same page without parameter
			echo "
	<script>
		$(document).ready(
			function() {
				window.location.href = location.origin + location.pathname + location.hash;
			});
	</script>
";
	?>
	<div id="social">
	<?php if (!has_option_value('social', 'none')) { ?>
		<div class="ssk-group ssk-rounded ssk-sticky ssk-left ssk-center <?php switch(strtolower($options['social_size'])) { case "small": echo " ssk-xs"; break; case "large": echo " ssk-lg"; break; default: echo " ssk-sm"; } if (!is_option_set('social_color')) { echo(" ssk-grayscale"); } ?>">
		<?php if (has_option_value('social', 'facebook')) { ?>
			<a href="" class="ssk ssk-facebook"></a>
		<?php } if (has_option_value('social', 'whatsapp')) { ?>
			<a href="" class="ssk ssk-whatsapp"></a>
		<?php } if (has_option_value('social', 'twitter')) { ?>
			<a href="" class="ssk ssk-twitter"></a>
		<?php } if (has_option_value('social', 'google')) { ?>
			<a href="" class="ssk ssk-google-plus"></a>
		<?php } if (has_option_value('social', 'linkedin')) { ?>
			<a href="" class="ssk ssk-linkedin"></a>
		<?php } if (has_option_value('social', 'pinterest')) { ?>
			<a href="" class="ssk ssk-pinterest"></a>
		<?php } if (has_option_value('social', 'tumblr')) { ?>
			<a href="" class="ssk ssk-tumblr"></a>
		<?php } if (has_option_value('social', 'vk')) { ?>
			<a href="" class="ssk ssk-vk"></a>
		<?php } if (has_option_value('social', 'buffer')) { ?>
			<a href="" class="ssk ssk-buffer"></a>
		<?php } if (has_option_value('social', 'email')) { ?>
			<a href="" class="ssk ssk-email"></a>
		<?php } ?>
		</div>
	<?php } ?>
	</div>

	<div id="title-container">
		<div id="buttons-container">
		</div>
		<div id="title">
			<span id="title-string"></span>
		</div>
	</div>
	<div id="media-view">
		<div id="media-box">
			<a id="next-media">
				<div id="media-box-inner" ></div>
			</a>
			<div id="media-bar">
				<div id="links">
					<a id="metadata-show" href="javascript:void(0)"></a>
					<a id="metadata-hide" style="display:none;" href="javascript:void(0)"></a> |
					<a id="original-link"></a> |
					<a id="download-link"></a> <a id="menu-map-divider">|</a>
					<a id="menu-map-link"></a>
					<a id="fullscreen" href="javascript:void(0)">
						<span id="fullscreen-divider"> | </span>
						<span id="enter-fullscreen"></span>
						<span id="exit-fullscreen"></span>
					</a>
				</div>
				<div id="metadata"></div>
			</div>
		</div>

		<a id="prev">&lsaquo;</a>
		<a id="next">&rsaquo;</a>
	</div>
	<div id="album-view">
		<div id="subalbums"></div>
		<div id="thumbs">
			<div id="loading"></div>
		</div>
		<div id="error-too-many-images"></div>
		<div id="powered-by">
			<span id="powered-by-string">Powered by</span>
			<a href="https://github.com/paolobenve/myphotoshare" target="_blank">MyPhotoShare</a>
		</div>
	</div>

	<ul id="right-menu">
		<li id="menu-icon"> ☰ </li>
		<li class="search">
			<form>
				<input type="text" id="search-field" />
				<img id="search-button" src="img/ic_search_black_48dp_2x.png" />
			</form>
		</li>
		<li id="no-results" class="search hidden"></li>
		<li id="inside-words" class="search active"></li>
		<li id="any-word" class="search active"></li>
		<li id="case-sensitive" class="search active"></li>
		<li id="accent-sensitive" class="search active"></li>
		<li id="regex-word" class="search active"></li>
		<li class="day-gps-folders-view caption"></li>
		<li id="folders-view" class="day-gps-folders-view"></li>
		<li id="by-date-view" class="day-gps-folders-view"></li>
		<li id="by-gps-view" class="day-gps-folders-view"></li>
		<li class="sort album-sort caption"></li>
		<li class='sort album-sort by-date'></li>
		<li class='sort album-sort by-name'></li>
		<li class='sort album-sort sort-reverse active'></li>
		<li class="sort media-sort caption"></li>
		<li class='sort media-sort by-date'></li>
		<li class='sort media-sort by-name'></li>
		<li class='sort media-sort sort-reverse active'></li>
		<li class='ui caption'></li>
		<li class='ui slide active'></li>
		<li class='ui spaced active'></li>
		<li class='ui album-names active'></li>
		<li class='ui media-count active'></li>
		<li class='ui media-names active'></li>
		<li class='ui square-album-thumbnails active'></li>
		<li class='ui square-media-thumbnails active'></li>
	</ul>

	<div id="error-overlay"></div>
	<div id="error-options-file"></div>
	<div id="error-text-folder"></div>
	<div id="error-root-folder"></div>
	<div id="error-text-image"></div>
	<div id="auth-text"><form id="auth-form"><input id="password" type="password" /><input type="submit" value="Login" /></form></div>
</body>
</html>
