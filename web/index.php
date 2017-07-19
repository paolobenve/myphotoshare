<!DOCTYPE html>
<html lang="en">
<head>
	<meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
	<meta http-equiv="X-UA-Compatible" content="IE=edge" />
	<meta name="viewport" content="width=device-width, initial-scale=1">
	<meta name="fragment" content="!" />
	<meta name="medium" content="image" />
	<?php
		$jsonString = file_get_contents('options.json');
		$options = json_decode($jsonString, true);
	?>
	<title><?php if ($options['page_title']) echo $options['page_title']; ?></title>
	<link rel="icon" href="favicon.ico" type="image/x-icon"/>
	<link href="css/styles.min.css" rel="stylesheet" type="text/css" /> 
<!--
	<link href="css/000-controls.css" rel="stylesheet" type="text/css" />
	<link href="css/001-fonts.css" rel="stylesheet" type="text/css" />
	<link href="css/002-mobile.css" rel="stylesheet" type="text/css" />
	<link href="css/003-social.css" rel="stylesheet" type="text/css" />
-->
	<script type="text/javascript" src="js/scripts.min.js"></script> 
<!--
	<script type="text/javascript" src="js/000-jquery-1.12.4.js"></script>
	<script type="text/javascript" src="js/001-hashchange.js"></script>
	<script type="text/javascript" src="js/002-preloadimages.js"></script>
	<script type="text/javascript" src="js/003-mousewheel.js"></script>
	<script type="text/javascript" src="js/004-fullscreen.js"></script>
	<script type="text/javascript" src="js/005-modernizr.js"></script>
	<script type="text/javascript" src="js/008-social.js"></script>
	<script type="text/javascript" src="js/009-translations.js"></script>
	<script type="text/javascript" src="js/010-libphotofloat.js"></script>
	<script type="text/javascript" src="js/012-display.js"></script>
-->
	<?php
		function join_paths() {
			return preg_replace('~[/\\\]+~', DIRECTORY_SEPARATOR, implode(DIRECTORY_SEPARATOR, func_get_args()));
		}
		
		// put the <link rel=".."> tag in <head> for getting the image thumbnail when sharing
		if ($_GET['t']) {
			if ($_GET['t'] == 'a') {
				$i = 0;
				$srcImagePaths = array();
				$url = $_SERVER['REQUEST_SCHEME'] . '://' . $_SERVER['HTTP_HOST'] . $_SERVER['CONTEXT_PREFIX'] . '/';
				while (array_key_exists('s' . $i, $_GET)) {
					$srcImagePaths[] = $url . $_GET['s' . $i];
					$i ++;
				}
				$maxThumbnailNumber = count($srcImagePaths);
				// following code got from
				// https://stackoverflow.com/questions/30429383/combine-16-images-into-1-big-image-with-php#30429557
				// thanks to Adarsh Vardhan who wrote it!
				
				/*
				 * INIT BASE IMAGE FILLED WITH BACKGROUND COLOR
				 */
				 
				$tileWidth = $tileHeight = $options['album_thumb_size'];
				$numberOfTiles = intval(sqrt($maxThumbnailNumber));
				$pxBetweenTiles = $options['thumb_spacing'];
				$leftOffSet = $topOffSet = 1;
				 
				$mapWidth = $mapHeight = ($tileWidth + $pxBetweenTiles) * $numberOfTiles;
				$mapImage = imagecreatetruecolor($mapWidth, $mapHeight);
				$bgColor = imagecolorallocate($mapImage, 255, 255, 255);
				//~ $bgColor = imagecolorallocate($mapImage, 50, 40, 0);
				imagefill($mapImage, 0, 0, $bgColor);
				 
				/*
				 *  PUT SRC IMAGES ON BASE IMAGE
				 */
				 
				function indexToCoords($index)
				{
					global $tileWidth, $pxBetweenTiles, $leftOffSet, $topOffSet, $numberOfTiles;

					$x = ($index % $numberOfTiles) * ($tileWidth + $pxBetweenTiles) + $leftOffSet;
					$y = floor($index / $numberOfTiles) * ($tileWidth + $pxBetweenTiles) + $topOffSet;
					return Array($x, $y);
				}
				 
				foreach ($srcImagePaths as $index => $srcImagePath)
				{
					list ($x, $y) = indexToCoords($index);
					$tileImg = imagecreatefromjpeg($srcImagePath);

					imagecopy($mapImage, $tileImg, $x, $y, 0, 0, $tileWidth, $tileHeight);
					imagedestroy($tileImg);
				}
				
				$imageFile = join_paths("album", strval(rand()) . ".jpg");
				$absoluteImagePath = join_paths($options['cache_path'], $imageFile);
				$serverImagePath = join_paths($options['server_cache_path'], $imageFile);
				
				// save the image
				$result = imagejpeg($mapImage, $absoluteImagePath);
				$media = $serverImagePath;
				
			} else {
				$media = $_GET['s0'];
			}
			$pathInfo = pathinfo($_SERVER['PHP_SELF'])['dirname'];
			$mediaWithPath = '/' .$media;
			if ($pathInfo != '/')
				$mediaWithPath = $pathInfo .$mediaWithPath;
			$linkTag = '<link ';
			if ($_GET['t'] == 'i' || $_GET['t'] == 'a')
				$linkTag .= 'rel="image_src" ';
			else if ($_GET['t'] == 'v')
				$linkTag .= 'rel="video_src" ';
			$linkTag .= 'href="' . $mediaWithPath . '"';
			$linkTag .= '>';
			echo "$linkTag\n";
			
			// php generated composite images only are needed for the moment when the user share the album
			// delete files older than 1 hour
			$files = glob(join_paths(join_paths($options['cache_path'],"album"), "*"));
			$now   = time();
			foreach ($files as $file) {
				if (is_file($file)) {
					if ($now - filemtime($file) >= 60 * 60) { // 1 hour
						unlink($file);
						echo "<!-- removed file $file\n -->";
					}
				}
			}
		}
	?>
</head>
<body>
	<?php
		if ($_GET)
			// redirect to parameters-less page
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
		<div class="ssk-group ssk-rounded ssk-sticky ssk-left ssk-center ssk-count">
			<a href="" class="ssk ssk-facebook"></a>
			<a href="" class="ssk ssk-twitter"></a>
			<a href="" class="ssk ssk-google-plus"></a>
			<a href="" class="ssk ssk-email"></a>
		</div>
	</div>
	<div id="title-container">
		<div id="buttons-container">
			<a id="day-folders-view-link" href="javascript:void(0)">
				<div id="day-folders-view-container">
					<span id="day-view"></span>
					<span id="folders-view"></span>
				</div>
			</a>
		</div>
		<div id="title">
			<span id="title-string"></span>
			<a id="album-sort-arrows"></a>
			<a id="media-sort-arrows"></a>
		</div>
	</div>
	<div id="media-view">
		<div id="media-box">
			<div id="photo-box">
				<a class="next-media">
					<div id="photo-box-inner" ></div>
				</a>
				<div id="photo-bar">
					<div class="links">
						<a class="metadata-show" href="javascript:void(0)"></a>
						<a class="metadata-hide" style="display:none;" href="javascript:void(0)"></a> |
						<a class="original-link" target="_blank"></a>
						<span class="fullscreen-divider"> | </span>
						<a class="fullscreen" href="javascript:void(0)">
							<span class="enter-fullscreen"></span>
							<span class="exit-fullscreen"></span>
						</a>
					</div>
					<div class="metadata"></div>
				</div>
			</div>
			<div id="video-box">
				<a class="next-media">
					<div id="video-box-inner"></div>
				</a>
				<div id="video-bar">
					<div class="links">
						<a class="metadata-show" href="javascript:void(0)"></a>
						<a class="metadata-hide" style="display:none;" href="javascript:void(0)"></a> |
						<a class="original-link" target="_blank"></a>
						<span class="fullscreen-divider"> | </span>
						<a class="fullscreen" href="javascript:void(0)">
							<span class="enter-fullscreen"></span>
							<span class="exit-fullscreen"></span>
						</a>
					</div>
					<div class="metadata"></div>
				</div>
			</div>
		</div>
		
		<a id="back">&lsaquo;</a>
		<a id="next">&rsaquo;</a>
	</div>
	<div id="album-view">
		<div id="subalbums"></div>
		<div id="thumbs">
			<div id="loading"></div>
		</div>
		<div id="powered-by">
			<span id="powered-by-string"></span>
			<a href="https://github.com/paolobenve/photofloat" target="_blank">PhotoFloat</a>
		</div>
	</div>

	<div id="error-overlay"></div>
	<div id="error-options-file"></div>
	<div id="error-text-folder"></div>
	<div id="error-text-image"></div>
	<div id="auth-text"><form id="auth-form"><input id="password" type="password" /><input type="submit" value="Login" /></form></div>
</body>
</html>
