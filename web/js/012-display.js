var Options = {};
var isMobile = {
	Android: function() {
		return navigator.userAgent.match(/Android/i);
	},
	BlackBerry: function() {
		return navigator.userAgent.match(/BlackBerry/i);
	},
	iOS: function() {
		return navigator.userAgent.match(/iPhone|iPad|iPod/i);
	},
	Opera: function() {
		return navigator.userAgent.match(/Opera Mini/i);
	},
	Windows: function() {
		return navigator.userAgent.match(/IEMobile/i);
	},
	any: function() {
		return (isMobile.Android() || isMobile.BlackBerry() || isMobile.iOS() || isMobile.Opera() || isMobile.Windows());
	}
};
// this variable permits to take into account the real mobile device pixels when deciding the size of reduced size image which is going to be loaded
var screenRatio = window.devicePixelRatio || 1;

$(document).ready(function() {

	/*
	 * The display is not yet object oriented. It's procedural code
	 * broken off into functions. It makes use of libphotofloat's
	 * PhotoFloat class for the network and management logic.
	 *
	 * All of this could potentially be object oriented, but presently
	 * it should be pretty readable and sufficient. The only thing to
	 * perhaps change in the future would be to consolidate calls to
	 * jQuery selectors. And perhaps it'd be nice to move variable
	 * declarations to the top, to stress that JavaScript scope is
	 * for an entire function and always hoisted.
	 *
	 * None of the globals here polutes the global scope, as everything
	 * is enclosed in an anonymous function.
	 *
	 */

	/* Globals */

	var currentAlbum = null;
	var currentMedia = null;
	var currentMediaIndex = -1;
	var previousAlbum = null;
	var previousMedia = null;
	var nextMedia = null;
	var photoFloat = new PhotoFloat();
	var maxSize;
	var fullScreenStatus = false;
	var photoSrc, videoSrc;
	var language;
	var numSubAlbumsReady;
	var fromEscKey = false;
	var firstEscKey = true;
	var nextLink = "", prevLink = "", upLink = "", mediaLink = "", savedLink = "";
	var searchCacheBase = '', searchSubAlbum = '';

	/* Displays */

	function _t(id) {
		language = getLanguage();
		if (translations[language][id])
			return translations[language][id];
		else
			return translations.en[id];
	}

	function translate() {
		var selector, keyLanguage;

		language = getLanguage();
		for (var key in translations.en) {
			if (translations[language].hasOwnProperty(key) || translations.en.hasOwnProperty(key)) {
				keyLanguage = language;
				if (! translations[language].hasOwnProperty(key))
					keyLanguage = 'en';

				if (key == '#title-string' && document.title.substr(0, 5) != "<?php")
					// don't set page title, php has already set it
					continue;
				selector = $(key);
				if (selector.length) {
					selector.html(translations[keyLanguage][key]);
				}
			}
		}
	}

	function getLanguage() {
		language = "en";
		if (Options.language && translations[Options.language] !== undefined)
			language = Options.language;
		else {
			var userLang = navigator.language || navigator.userLanguage || navigator.browserLanguage || navigator.systemLanguage;
			userLang = userLang.split('-')[0];
			if (translations[userLang] !== undefined)
				language = userLang;
		}
		return language;
	}

	// adapted from https://stackoverflow.com/questions/15084675/how-to-implement-swipe-gestures-for-mobile-devices#answer-27115070
	function detectSwipe(el,callback) {
		var swipe_det, ele, min_x, min_y, max_x, max_y, direc;
		var touchStart, touchMove, touchEnd;
		touchStart = function(e) {
			var t = e.touches[0];
			swipe_det.sX = t.screenX;
			swipe_det.sY = t.screenY;
		};
		touchMove = function(e) {
			e.preventDefault();
			var t = e.touches[0];
			swipe_det.eX = t.screenX;
			swipe_det.eY = t.screenY;
		};
		touchEnd = function(e) {
			//horizontal detection
			if (
				(swipe_det.eX - min_x > swipe_det.sX || swipe_det.eX + min_x < swipe_det.sX) &&
				swipe_det.eY < swipe_det.sY + max_y &&
				swipe_det.sY > swipe_det.eY - max_y &&
				swipe_det.eX > 0
			) {
				if(swipe_det.eX > swipe_det.sX)
					direc = "r";
				else
					direc = "l";
			}
			//vertical detection
			else if (
				(swipe_det.eY - min_y > swipe_det.sY || swipe_det.eY + min_y < swipe_det.sY) &&
				swipe_det.eX < swipe_det.sX + max_x &&
				swipe_det.sX > swipe_det.eX - max_x &&
				swipe_det.eY > 0
			) {
				if(swipe_det.eY > swipe_det.sY)
					direc = "d";
				else
					direc = "u";
			}

			if (direc !== "") {
				if(typeof callback == 'function')
					callback(el,direc);
			}
			direc = "";
			swipe_det.sX = 0;
			swipe_det.eX = 0;
		};
		swipe_det = {};
		swipe_det.sX = 0; swipe_det.eX = 0;
		min_x = 30;  //min x swipe for horizontal swipe
		max_x = 30;  //max x difference for vertical swipe
		min_y = 50;  //min y swipe for vertical swipe
		max_y = 60;  //max y difference for horizontal swipe
		direc = "";
		ele = document.getElementById(el);
		ele.addEventListener('touchstart', touchStart, false);
		ele.addEventListener('touchmove', touchMove, false);
		ele.addEventListener('touchend', touchEnd, false);
	}

	function swipe(el,d) {
		if (d == "r") {
			swipeRight(prevLink);
		} else if (d == "l") {
			swipeLeft(nextLink);
		} else if (d == "d") {
			if (upLink) {
				fromEscKey = true;
				swipeDown(upLink);
			}
		} else if (d == "u") {
			if (currentMedia === null)
				swipeUp(mediaLink);
			else
				swipeLeft(nextLink);
		}
	}

	function swipeRight(dest) {
		if (dest) {
			$("#media-box-inner").stop().animate({
				right: "-=" + window.innerWidth,
			}, 300, function() {
				window.location.href = dest;
				$("#media-box-inner").css('right', "");
			});
		}
	}
	function swipeLeft(dest) {
		if (dest) {
			$("#media-box-inner").stop().animate({
				left: "-=" + window.innerWidth,
			}, 300, function() {
				window.location.href = dest;
				$("#media-box-inner").css('left', "");
			});
		}
	}

	function swipeUp(dest) {
		if (dest) {
			$("#media-box-inner").stop().animate({
				top: "-=" + window.innerHeight,
			}, 300, function() {
				window.location.href = dest;
				$("#media-box-inner").css('top', "");
			});
		}
	}
	function swipeDown(dest) {
		if (dest) {
			$("#media-box-inner").stop().animate({
				top: "+=" + window.innerHeight,
			}, 300, function() {
				window.location.href = dest;
				$("#media-box-inner").css('top', "");
			});
		}
	}

	function socialButtons() {
		var url, hash, myShareUrl = "";
		var mediaParameter;
		var folders, myShareText, myShareTextAdd;

		if (! isMobile.any()) {
			$(".ssk-whatsapp").hide();
		} else {
			// with touchscreens luminosity on hover cannot be used
			$(".album-button-and-caption").css("opacity", 1);
			$(".thumb-container").css("opacity", 1);
			$(".album-button-random-media-link").css("opacity", 1);
		}

		url = location.protocol + "//" + location.host;
		folders = location.pathname;
		folders = folders.substring(0, folders.lastIndexOf('/'));
		url += folders;
		if (currentMedia === null || currentAlbum !== null && ! currentAlbum.subalbums.length && currentAlbum.media.length == 1) {
			mediaParameter = PhotoFloat.pathJoin([
				Options.server_cache_path,
				Options.cache_album_subdir,
				currentAlbum.cacheBase
				]) + ".jpg";
		} else {
			var reducedSizesIndex = 1;
			if (Options.reduced_sizes.length == 1)
				reducedSizesIndex = 0;
			var prefix = removeFolderMarker(currentMedia.foldersCacheBase);
			if (prefix)
				prefix += Options.cache_folder_separator;
			if (currentMedia.mediaType == "video") {
				mediaParameter = PhotoFloat.pathJoin([
					Options.server_cache_path,
					currentMedia.cacheSubdir,
				]) + prefix + currentMedia.cacheBase + Options.cache_folder_separator + "transcoded_" + Options.video_transcode_bitrate + "_" + Options.video_crf + ".mp4";
			} else if (currentMedia.mediaType == "photo") {
				mediaParameter = PhotoFloat.pathJoin([
					Options.server_cache_path,
					currentMedia.cacheSubdir,
					prefix + currentMedia.cacheBase
				]) + Options.cache_folder_separator + Options.reduced_sizes[reducedSizesIndex] + ".jpg";
			}
		}

		myShareUrl = url + '?';
		myShareUrl += 'm=' + mediaParameter;
		hash = location.hash;
		if (hash)
			myShareUrl += '#' + hash.substring(1);

		myShareText = Options.page_title;
		myShareTextAdd = currentAlbum.physicalPath;
		if (myShareTextAdd)
			myShareText += ": " + myShareTextAdd.substring(myShareTextAdd.lastIndexOf('/') + 1);

		jQuery.removeData(".ssk");
		$('.ssk').attr('data-text', myShareText);
		$('.ssk-facebook').attr('data-url', myShareUrl);
		$('.ssk-whatsapp').attr('data-url', location.href);
		$('.ssk-twitter').attr('data-url', location.href);
		$('.ssk-google-plus').attr('data-url', myShareUrl);
		$('.ssk-email').attr('data-url', location.href);

		// initialize social buttons (http://socialsharekit.com/)
		SocialShareKit.init({
		});
		if (! Modernizr.flexbox && bottomSocialButtons()) {
			var numSocial = 5;
			var socialWidth = Math.floor(window.innerWidth / numSocial);
			$('.ssk').width(socialWidth * 2 + "px");
		}
	}

	function removeFolderMarker(cacheBase) {
		if (PhotoFloat.isFolderCacheBase(cacheBase)) {
			cacheBase = cacheBase.substring(Options.folders_string.length);
			if (cacheBase.length > 0)
				cacheBase = cacheBase.substring(1);
		}
		return cacheBase;
	}

	function updateMenu() {
		var albumOrMedia;
		// add the correct classes to the menu sort buttons
		if (currentMedia !== null) {
			// showing a media, nothing to sort
			$("#right-menu li.sort").addClass("hidden");
		} else if (currentAlbum !== null) {
			if (currentAlbum.subalbums.length <= 1) {
				// no subalbums or one subalbum
				$("ul#right-menu li.album-sort").addClass("hidden");
			} else {
				$("ul#right-menu li.album-sort").removeClass("hidden");
			}

			if (currentAlbum.media.length <= 1 || currentAlbum.media.length > Options.big_virtual_folders_threshold) {
				// no media or one media or too many media
				$("ul#right-menu li.media-sort").addClass("hidden");
			} else {
				$("ul#right-menu li.media-sort").removeClass("hidden");
			}

			var modes = ["album", "media"];
			for (var i in modes) {
				if (modes.hasOwnProperty(i)) {
					albumOrMedia = modes[i];
					if (currentAlbum[albumOrMedia + "NameSort"]) {
						$("ul#right-menu li." + albumOrMedia + "-sort.by-name").removeClass("active").addClass("selected");
						$("ul#right-menu li." + albumOrMedia + "-sort.by-date").addClass("active").removeClass("selected");
					} else {
						$("ul#right-menu li." + albumOrMedia + "-sort.by-date").removeClass("active").addClass("selected");
						$("ul#right-menu li." + albumOrMedia + "-sort.by-name").addClass("active").removeClass("selected");
					}

					if (
						currentAlbum[albumOrMedia + "NameSort"] && currentAlbum[albumOrMedia + "NameReverseSort"] ||
					 	! currentAlbum[albumOrMedia + "NameSort"] && currentAlbum[albumOrMedia + "DateReverseSort"]
					) {
						$("#right-menu li." + albumOrMedia + "-sort.sort-reverse").addClass("selected");
					} else {
						$("#right-menu li." + albumOrMedia + "-sort.sort-reverse").removeClass("selected");
					}
				}
			}
		}

		$("ul#right-menu li.ui").removeClass("hidden");

		if (currentMedia !== null || currentAlbum !== null && currentAlbum.subalbums.length === 0) {
			$("ul#right-menu li.slide").addClass("hidden");
		} else {
			$("ul#right-menu li.slide").removeClass("hidden");
			if (Options.albums_slide_style)
				$("ul#right-menu li.slide").addClass("selected");
			else
				$("ul#right-menu li.slide").removeClass("selected");
		}

		if (currentMedia !== null || currentAlbum !== null && currentAlbum.subalbums.length <= 1 && currentAlbum.media.length <= 1) {
			$("ul#right-menu li.spaced").addClass("hidden");
		} else {
			$("ul#right-menu li.spaced").removeClass("hidden");
			if (Options.spacing)
				$("ul#right-menu li.spaced").addClass("selected");
			else
				$("ul#right-menu li.spaced").removeClass("selected");
		}
		if (currentMedia !== null || currentAlbum !== null && currentAlbum.subalbums.length === 0) {
			$("ul#right-menu li.square-album-thumbnails").addClass("hidden");
		} else {
			$("ul#right-menu li.square-album-thumbnails").removeClass("hidden");
			if (Options.album_thumb_type == "square")
				$("ul#right-menu li.square-album-thumbnails").addClass("selected");
			else
				$("ul#right-menu li.square-album-thumbnails").removeClass("selected");
		}

		if (currentMedia !== null || currentAlbum !== null && (currentAlbum.subalbums.length === 0 || ! PhotoFloat.isFolderCacheBase(currentAlbum.cacheBase))) {
			$("ul#right-menu li.album-names").addClass("hidden");
		} else {
			$("ul#right-menu li.album-names").removeClass("hidden");
			if (Options.show_album_names_below_thumbs)
				$("ul#right-menu li.album-names").addClass("selected");
			else
				$("ul#right-menu li.album-names").removeClass("selected");
		}

		if (currentMedia !== null || currentAlbum !== null && (currentAlbum.subalbums.length === 0 && currentAlbum.media.length <= 1)) {
			$("ul#right-menu li.media-count").addClass("hidden");
		} else {
			$("ul#right-menu li.media-count").removeClass("hidden");
			if (Options.show_album_media_count)
				$("ul#right-menu li.media-count").addClass("selected");
			else
				$("ul#right-menu li.media-count").removeClass("selected");
		}

		if (
			currentMedia !== null ||
			currentAlbum !== null && (
				currentAlbum.media.length === 0 || ! PhotoFloat.isFolderCacheBase(currentAlbum.cacheBase) && currentAlbum.media.length > Options.big_virtual_folders_threshold
			)
		) {
			$("ul#right-menu li.media-names").addClass("hidden");
		} else {
			$("ul#right-menu li.media-names").removeClass("hidden");
			if (Options.show_media_names_below_thumbs)
				$("ul#right-menu li.media-names").addClass("selected");
			else
				$("ul#right-menu li.media-names").removeClass("selected");
		}

		if (
			currentMedia !== null ||
			currentAlbum !== null && (
				currentAlbum.media.length === 0 || ! PhotoFloat.isFolderCacheBase(currentAlbum.cacheBase) && currentAlbum.media.length > Options.big_virtual_folders_threshold
			)
		) {
			$("ul#right-menu li.square-media-thumbnails").addClass("hidden");
		} else {
			$("ul#right-menu li.square-media-thumbnails").removeClass("hidden");
			if (Options.media_thumb_type == "square")
			 	$("ul#right-menu li.square-media-thumbnails").addClass("selected");
			else
				$("ul#right-menu li.square-media-thumbnails").removeClass("selected");
		}

		if (
			$("ul#right-menu li.slide").hasClass("hidden") &&
			$("ul#right-menu li.spaced").hasClass("hidden") &&
			$("ul#right-menu li.album-names").hasClass("hidden") &&
			$("ul#right-menu li.media-count").hasClass("hidden") &&
			$("ul#right-menu li.media-names").hasClass("hidden") &&
			$("ul#right-menu li.square-album-thumbnails").hasClass("hidden") &&
			$("ul#right-menu li.square-media-thumbnails").hasClass("hidden")
		) {
			$("ul#right-menu li.ui").addClass("hidden");
		}

		if (
			currentAlbum !== null && (PhotoFloat.isSearchCacheBase(currentAlbum.cacheBase) || currentAlbum.cacheBase == Options.by_search_string) ||
			Options.search_regex ||
			Options.search_inside_words ||
			Options.search_any_word ||
			Options.search_case_sensitive ||
			Options.search_accent_sensitive ||
			$("ul#right-menu li#no-search-string").is(":visible") ||
			$("ul#right-menu li#no-results").is(":visible") ||
			$("ul#right-menu li#search-too-wide").is(":visible")
		) {
			$("ul#right-menu li#inside-words").removeClass("hidden");
			$("ul#right-menu li#any-word").removeClass("hidden");
			$("ul#right-menu li#case-sensitive").removeClass("hidden");
			$("ul#right-menu li#accent-sensitive").removeClass("hidden");
			$("ul#right-menu li#regex-word").removeClass("hidden");
			if (Options.search_regex) {
				$("ul#right-menu li#regex-word").addClass("selected");
				$("ul#right-menu li#inside-words").addClass("hidden");
				$("ul#right-menu li#any-word").addClass("hidden");
				$("ul#right-menu li#case-sensitive").addClass("hidden");
				$("ul#right-menu li#accent-sensitive").addClass("hidden");
			} else {
				$("ul#right-menu li#regex-word").removeClass("selected");
				if (Options.search_inside_words)
					$("ul#right-menu li#inside-words").addClass("selected");
				else
					$("ul#right-menu li#inside-words").removeClass("selected");
				if (Options.search_any_word)
					$("ul#right-menu li#any-word").addClass("selected");
				else
					$("ul#right-menu li#any-word").removeClass("selected");
				if (Options.search_case_sensitive)
					$("ul#right-menu li#case-sensitive").addClass("selected");
				else
					$("ul#right-menu li#case-sensitive").removeClass("selected");
				if (Options.search_accent_sensitive)
					$("ul#right-menu li#accent-sensitive").addClass("selected");
				else
					$("ul#right-menu li#accent-sensitive").removeClass("selected");
			}
		} else {
			$("ul#right-menu li#inside-words").addClass("hidden");
			$("ul#right-menu li#any-word").addClass("hidden");
			$("ul#right-menu li#case-sensitive").addClass("hidden");
			$("ul#right-menu li#accent-sensitive").addClass("hidden");
			$("ul#right-menu li#regex-word").addClass("hidden");
		}
	}

	function transformAltPlaceName(altPlaceName) {
		var underscoreIndex = altPlaceName.lastIndexOf('_');
		if (underscoreIndex != -1) {
			var number = altPlaceName.substring(underscoreIndex + 1);
			while (number.indexOf('0') === 0)
				number = number.substr(1);
			var base = altPlaceName.substring(0, underscoreIndex);
			return base + ' (' + _t('.subalbum') + number + ')';
		} else {
			return altPlaceName;
		}
	}

	function detectSearchSubAlbum() {
		var splittedHash = location.hash.split('/');
		var splittedSearchAndSubalbumHash;
		if (splittedHash.length >= 3 && PhotoFloat.isSearchCacheBase(splittedHash[2])) {
			splittedSearchAndSubalbumHash = splittedHash[2].split(Options.cache_folder_separator);
			searchCacheBase = splittedSearchAndSubalbumHash.slice(0, 2).join(Options.cache_folder_separator);
			searchSubAlbum = splittedSearchAndSubalbumHash.slice(2).join(Options.cache_folder_separator);
		}
		return;
	}

	function setTitle() {
		var title = "", documentTitle = "", components, i, isDateTitle, isGpsTitle, isSearchTitle, originalTitle;
		var titleAnchorClasses, hiddenTitle = "", beginLink, linksToLeave, numLinks, latitude, longitude, arrayCoordinates, numMediaInSubAlbums;
		// gpsLevelNumber is the number of levels for the by gps tree
		// current levels are country, region, place => 3
		var gpsLevelNumber = 3;
		var gpsName = '';
		var mediaForNames = null;
		var gpsHtmlTitle;

		updateMenu();

		if (Options.page_title !== "")
			originalTitle = Options.page_title;
		else
			originalTitle = translations[language]["#title-string"];


		if (! currentAlbum.path.length)
			components = [originalTitle];
		else {
			components = currentAlbum.path.split("/");
			components.unshift(originalTitle);
		}

		isDateTitle = (components.length > 1 && components[1] == Options.by_date_string);
		isGpsTitle = (components.length > 1 && components[1] == Options.by_gps_string);
		isSearchTitle = (components.length > 1 && components[1] == Options.by_search_string);

		// textComponents = components doesn't work: textComponents becomes a pointer to components
		var textComponents = components.slice();

		// generate the title in the page top
		titleAnchorClasses = 'title-anchor';
		if (isMobile.any())
			titleAnchorClasses += ' mobile';

		if (isDateTitle) {
			title = "<a class='" + titleAnchorClasses + "' href='#!/" + "'>" + components[0] + "</a>";
			title += "<span class='title-no-anchor'>(" + _t("#by-date") + ")</span>&raquo;";

			documentTitle += components[0];
			if (components.length > 2 || currentMedia !== null)
				documentTitle = " \u00ab " + documentTitle;
			documentTitle += " (" + _t("#by-date") + ")";

			for (i = 2; i < components.length; ++i) {
				if (i < components.length - 1 || currentMedia !== null)
					title += "<a class='" + titleAnchorClasses + "' href='#!/" + encodeURI(currentAlbum.ancestorsCacheBase[i]) + "'" + ">";
				else
					title += "<span class='title-no-anchor'>";
				title += textComponents[i];
				if (i < components.length - 1 || currentMedia !== null)
					title += "</a>";
				else
					title += "</span>";
				if (i == components.length - 1 && currentMedia === null) {
					if (! isMobile.any()) {
						title += " <span id=\"title-count\">(";
						title += currentAlbum.media.length + " ";
						title += _t(".title-media") + " ";
					 	if (components.length >= 5)
							title += _t("#title-in-day-album");
						else
							title += _t("#title-in-date-album");
						title += ")</span>";
					}
					title += "</span>";
				}
				if (i < components.length - 1 || currentMedia !== null)
					title += "&raquo;";

				// keep buildimg the html page title
				documentTitle = textComponents[i] + documentTitle;
				if (i < components.length - 1 || currentMedia !== null)
					documentTitle = " \u00ab " + documentTitle;
			}
		} else if (isGpsTitle) {
			title = "<a class='" + titleAnchorClasses + "' href='#!/" + "'>" + components[0] + "</a>";
			title += "<span class='title-no-anchor'>(" + _t("#by-gps") + ")</span>&raquo;";

			documentTitle += components[0];
			if (components.length > 2 || currentMedia !== null)
				documentTitle = " \u00ab " + documentTitle;
			documentTitle += " (" + _t("#by-gps") + ")";

			for (i = 2; i < components.length; ++i) {
				if (currentMedia !== null)
					mediaForNames = currentMedia;
				else
					mediaForNames = currentAlbum.media[0];
				if (i == 2)
					gpsName = mediaForNames.geoname.country_name;
				else if (i == 3)
					gpsName = mediaForNames.geoname.region_name;
				else if (i == 4) {
					if (mediaForNames.geoname.alt_place_name !== undefined)
						gpsName = transformAltPlaceName(mediaForNames.geoname.alt_place_name);
					else
						gpsName = mediaForNames.geoname.place_name;
				}

				if (gpsName === '')
					gpsName = _t('.not-specified');
				gpsHtmlTitle = _t("#place-icon-title") + gpsName;

				if (i < components.length - 1 || currentMedia !== null) {
					title += "<a class='" + titleAnchorClasses + "' href='#!/" + encodeURI(currentAlbum.ancestorsCacheBase[i]) + "'";
					title += " title='" + _t("#place-icon-title") + gpsName + _t("#place-icon-title-end") + "'";
					title += ">";
				} else
					title += "<span class='title-no-anchor'>";
				title += gpsName;
				if (i < components.length - 1 || currentMedia !== null)
					title += "</a>";
				else
					title += "</span>";

				if (currentMedia !== null) {
					latitude = currentMedia.metadata.latitude;
					longitude = currentMedia.metadata.longitude;
				} else {
					 arrayCoordinates = currentAlbum.ancestorsCenter[i];
					 latitude = arrayCoordinates.latitude;
					 longitude = arrayCoordinates.longitude;
				}
				title += "<a href=" + mapLink(latitude, longitude, Options.map_zoom_levels[(i - 2)]) + " target='_blank'>" +
									"<img class='title-img' title='" + gpsHtmlTitle + "' alt='" + gpsHtmlTitle + "' height='20px' src='img/ic_place_white_24dp_2x.png'>" +
									"</a>";

				if (i == components.length - 1 && currentMedia === null) {
					title += " <span id=\"title-count\">(";
					title += currentAlbum.media.length + " ";
					title += _t(".title-media") + " ";
					if (components.length >= gpsLevelNumber + 2)
						title += _t("#title-in-gps-album");
					else
						title += _t("#title-in-gpss-album");
					title += ")</span>";
				}
				if (i < components.length - 1 || currentMedia !== null)
					title += "&raquo;";

				// keep buildimg the html page title
				documentTitle = gpsName + documentTitle;
				if (i < components.length - 1 || currentMedia !== null)
					documentTitle = " \u00ab " + documentTitle;
			}
		} else if (isSearchTitle) {
			// i=0: title
			// i=1: Options.by_search_string
			// (optional) i=2: image cache
			title = "<a class='" + titleAnchorClasses + "' href='#!/" + "'>" + components[0] + "</a>&raquo;";

			if (currentMedia === null)
				title += "<span class='title-no-anchor'";
			else
				title += "<a class='" + titleAnchorClasses + "' href='#!/" + currentAlbum.cacheBase + "'";
			title += " style='font-style: italic;'>(" + _t("#by-search") + ")";
			if (currentMedia === null)
				title += "</span>";
			else
				title += "</a>";

			// do not show the options and the search words, they are visible in the menu
			// show the image name, if it is there
			if (currentMedia !== null) {
				title += "&raquo;";
			}

			// build the html page title
			documentTitle += " (" + _t("#by-search") + ") \u00ab " + components[0];
			if (currentMedia !== null)
				documentTitle = " \u00ab " + documentTitle;
		} else {
			// folders title
			title = "<a class='" + titleAnchorClasses + "' href='#!/" + "'>" + components[0] + "</a>";
			if (components.length > 1 || currentMedia !== null)
				title += "&raquo;";

			if (searchCacheBase) {
				title += "<a class='" + titleAnchorClasses + "' href='#!/" + searchCacheBase + "'>";
				title += _t("#by-search");
				title += "</a>";
				title += "&raquo;";
			}

			documentTitle += components[0];
			if (components.length > 2 || currentMedia !== null)
				documentTitle = " \u00ab " + documentTitle;

			for (i = 2; i < components.length; ++i) {
				if (i < components.length - 1 || currentMedia !== null)
					title += "<a class='" + titleAnchorClasses + "' href='#!/" + encodeURI(currentAlbum.ancestorsCacheBase[i]) + "'>";
				else
					title += "<span class='title-no-anchor'>";

				title += textComponents[i];

				if (i < components.length - 1 || currentMedia !== null)
					title += "</a>";
				else
					title += "</span>";

				if (i == components.length - 1 && currentMedia === null) {
					title += " <span id=\"title-count\">(";
					numMediaInSubAlbums = currentAlbum.numMediaInSubTree - currentAlbum.media.length;
					if (currentAlbum.media.length) {
						title += currentAlbum.media.length + " ";
						title += _t(".title-media") + " ";
						title += _t("#title-in-album");
						if (numMediaInSubAlbums)
							title += ", ";
					}
					if (numMediaInSubAlbums) {
						title += numMediaInSubAlbums + " ";
						if (! currentAlbum.media.length)
							title += _t(".title-media") + " ";
						title += _t("#title-in-subalbums");
					}
					if (currentAlbum.media.length > 0 && numMediaInSubAlbums > 0) {
						title += ", ";
						title += _t("#title-total") + " ";
						title += currentAlbum.media.length + numMediaInSubAlbums;
					}
					title += ")</span>";
				}

				if (i < components.length - 1 || currentMedia !== null)
					title += "&raquo;";

				// keep building the html page title
				documentTitle = textComponents[i] + documentTitle;
				if (i < components.length - 1 || currentMedia !== null)
					documentTitle = " \u00ab " + documentTitle;
			}
		}




		// leave only the last link on mobile
		linksToLeave = 1;
		numLinks = title.split("<a class=").length - 1;
		if (isMobile.any() && numLinks > linksToLeave) {
			for (i = 1; i <= numLinks - linksToLeave; i ++) {
				beginLink = title.indexOf("<a class=", 3);
				hiddenTitle += title.substring(0, beginLink);
				title = title.substring(beginLink);
			}
			title = "<a id=\"dots\" href=\"javascript:void(0)\">... &raquo; </a><span id=\"hidden-title\">" + hiddenTitle + "</span> " + title;
		}

		if (currentMedia !== null) {
			title += "<span id=\"media-name\">" + photoFloat.trimExtension(currentMedia.name) + "</span>";
			if (hasGpsData(currentMedia)) {
				latitude = currentMedia.metadata.latitude;
				longitude = currentMedia.metadata.longitude;
				title += "<a href=" + mapLink(latitude, longitude, Options.photo_map_zoom_level) + " target='_blank'>" +
										"<img class='title-img' title='" + _t("#show-on-map") + " [s]' alt='" + _t("#show-on-map") + "' height='20px' src='img/ic_place_white_24dp_2x.png'>" +
										"</a>";
			}
		}

		if (currentMedia === null && currentAlbum !== null && ! currentAlbum.subalbums.length && currentAlbum.media.length == 1) {
			title += " &raquo; <span id=\"media-name\">" + photoFloat.trimExtension(currentAlbum.media[0].name) + "</span>";
		}

		$("#title-string").html(title);

		$("#dots").off();
		$("#dots").on('click', function(ev) {
			if (ev.which == 1 && ! ev.shiftKey && ! ev.ctrlKey && ! ev.altKey) {
				$("#dots").hide();
				$("#hidden-title").show();
				return false;
			}
		});

		// keep generating the html page title
		if (currentMedia !== null)
			documentTitle = photoFloat.trimExtension(currentMedia.name) + documentTitle;
		else if (currentAlbum !== null && ! currentAlbum.subalbums.length && currentAlbum.media.length == 1)
			documentTitle =  photoFloat.trimExtension(currentAlbum.media[0].name) + " \u00ab " + documentTitle;

		document.title = documentTitle;
		setOptions();

		return;
	}

	function initializeSortPropertiesAndCookies() {
		// this function applies the sorting on the media and subalbum lists
		// and sets the album properties that attest the lists status

		// album properties reflect the current sorting of album and media objects
		// json files have subalbums and media sorted by date not reversed

		if (currentAlbum.albumNameSort === undefined) {
			currentAlbum.albumNameSort = false;
		}
		if (currentAlbum.albumDateReverseSort === undefined){
			currentAlbum.albumDateReverseSort = false;
		}
		if (currentAlbum.albumNameReverseSort === undefined){
			currentAlbum.albumNameReverseSort = false;
		}

		if (currentAlbum.mediaNameSort === undefined) {
			currentAlbum.mediaNameSort = false;
		}
		if (currentAlbum.mediaDateReverseSort === undefined){
			currentAlbum.mediaDateReverseSort = false;
		}
		if (currentAlbum.mediaNameReverseSort === undefined)
			currentAlbum.mediaNameReverseSort = false;

		// cookies reflect the requested sorting in ui
		// they remember the ui state when a change in sort is requested (via the top buttons) and when the hash changes
		// if they are not set yet, they are set to default values

		if (getBooleanCookie("albumNameSortRequested") === null)
			setBooleanCookie("albumNameSortRequested", Options.default_album_name_sort);
		if (getBooleanCookie("albumDateReverseSortRequested") === null)
			setBooleanCookie("albumDateReverseSortRequested", Options.default_album_reverse_sort);
		if (getBooleanCookie("albumNameReverseSortRequested") === null)
			setBooleanCookie("albumNameReverseSortRequested", Options.default_album_reverse_sort);

		if (getBooleanCookie("mediaNameSortRequested") === null)
			setBooleanCookie("mediaNameSortRequested", Options.default_media_name_sort);
		if (getBooleanCookie("mediaDateReverseSortRequested") === null)
			setBooleanCookie("mediaDateReverseSortRequested", Options.default_media_reverse_sort);
		if (getBooleanCookie("mediaNameReverseSortRequested") === null)
			setBooleanCookie("mediaNameReverseSortRequested", Options.default_media_reverse_sort);
	}

	function sortAlbumsMedia() {
		// this function applies the sorting on the media and subalbum lists
		// and sets the album properties that attest the lists status

		// album properties reflect the current sorting of album and media objects
		// json files have subalbums and media sorted by date not reversed

		var m;

		if (needAlbumNameSort()) {
			currentAlbum.subalbums = PhotoFloat.sortByPath(currentAlbum.subalbums);
			currentAlbum.albumNameSort = true;
			currentAlbum.albumNameReverseSort = false;
			// $("li.album-sort.by-name").addClass("selected");
		} else if (needAlbumDateSort()) {
			currentAlbum.subalbums = PhotoFloat.sortByDate(currentAlbum.subalbums);
			currentAlbum.albumNameSort = false;
			currentAlbum.albumDateReverseSort = false;
		}

		if (needAlbumNameReverseSort() || needAlbumDateReverseSort()) {
			currentAlbum.subalbums = currentAlbum.subalbums.reverse();
			if (needAlbumNameReverseSort())
				currentAlbum.albumNameReverseSort = ! currentAlbum.albumNameReverseSort;
			else
				currentAlbum.albumDateReverseSort = ! currentAlbum.albumDateReverseSort;
		}

		if (needMediaNameSort()) {
			currentAlbum.media = PhotoFloat.sortByName(currentAlbum.media);
			currentAlbum.mediaNameSort = true;
			currentAlbum.mediaNameReverseSort = false;
			if (currentMedia !== null) {
				for (m = 0; m < currentAlbum.media.length; m ++) {
					if (currentAlbum.media[m].cacheBase == currentMedia.cacheBase && currentAlbum.media[m].foldersCacheBase == currentMedia.foldersCacheBase) {
						currentMediaIndex = m;
						break;
					}
				}
			}
		} else if (needMediaDateSort()) {
			currentAlbum.media = PhotoFloat.sortByDate(currentAlbum.media);
			currentAlbum.mediaNameSort = false;
			currentAlbum.mediaDateReverseSort = false;
			if (currentMedia !== null) {
				for (m = 0; m < currentAlbum.media.length; m ++) {
					if (currentAlbum.media[m].cacheBase == currentMedia.cacheBase && currentAlbum.media[m].foldersCacheBase == currentMedia.foldersCacheBase) {
						currentMediaIndex = m;
						break;
					}
				}
			}
		}
		if (needMediaDateReverseSort() || needMediaNameReverseSort()) {
			currentAlbum.media = currentAlbum.media.reverse();
			if (needMediaNameReverseSort())
				currentAlbum.mediaNameReverseSort = ! currentAlbum.mediaNameReverseSort;
			else
				currentAlbum.mediaDateReverseSort = ! currentAlbum.mediaDateReverseSort;
			if (currentMediaIndex !== undefined && currentMediaIndex != -1)
				currentMediaIndex = currentAlbum.media.length - 1 - currentMediaIndex;
		}
	}

	function scrollToThumb() {
		var media, thumb;

		media = currentMedia;
		if (media === null) {
			media = previousMedia;
			if (media === null)
				return;
		}
		$("#thumbs img.thumbnail").each(function() {
			if (
				(PhotoFloat.isFolderCacheBase(currentAlbum.cacheBase) || currentAlbum.cacheBase == Options.folders_string) && this.title === media.albumName ||
				PhotoFloat.isByDateCacheBase(currentAlbum.cacheBase) && this.title === media.albumName ||
				PhotoFloat.isByGpsCacheBase(currentAlbum.cacheBase) && this.title === media.albumName ||
				PhotoFloat.isSearchCacheBase(currentAlbum.cacheBase) && this.title === media.albumName
			) {
				thumb = $(this);
				return false;
			}
		});
		if (typeof thumb === "undefined")
			return;
		if (currentMedia !== null) {
			var scroller = $("#album-view");
			scroller.stop().animate(
				{ scrollLeft: thumb.parent().position().left + scroller.scrollLeft() - scroller.width() / 2 + thumb.width() / 2 }, "slow"
			);
		} else
			$("html, body").stop().animate({ scrollTop: thumb.offset().top - $(window).height() / 2 + thumb.height() }, "slow");

		if (currentMedia !== null) {
			$(".thumb-container").removeClass("current-thumb");
			thumb.parent().addClass("current-thumb");
		}
	}

	function albumButtonWidth(thumbnailWidth, buttonBorder) {
		if (Options.albums_slide_style)
			return Math.round((thumbnailWidth + 2 * buttonBorder) * 1.1);
		else
			return thumbnailWidth + 2 * buttonBorder;
	}

	function correctUpHash(albumHash) {
		if (searchCacheBase) {
			if (searchSubAlbum.indexOf(albumHash) === 0 && albumHash.length < searchSubAlbum.length) {
				return searchCacheBase;
			} else {
				return PhotoFloat.pathJoin([albumHash, [searchCacheBase, searchSubAlbum].join(Options.cache_folder_separator)]);
			}
		} else if (albumHash == Options.by_search_string) {
			return Options.folders_string;
		}
		return albumHash;
	}

	function showAlbum(populate) {
		var i, imageLink, linkContainer, container, image, media, thumbsElement, subalbums, subalbumsElement, hash, subfolderHash, thumbHash, thumbnailSize;
		var width, height, thumbWidth, thumbHeight, imageString, calculatedWidth, populateMedia;
		var albumViewWidth, correctedAlbumThumbSize = Options.album_thumb_size;
		var mediaWidth, mediaHeight, slideBorder = 0, scrollBarWidth = 0, buttonBorder = 0, margin, imgTitle;
		var tooBig = false, isVirtualAlbum = false;
		var mapLinkIcon;
		var element;
		var caption, captionColor, captionHtml, captionHeight, captionFontSize, buttonAndCaptionHeight, albumButtonAndCaptionHtml, heightfactor;
		var folderArray, folder;

		PhotoFloat.subalbumIndex = 0;
		numSubAlbumsReady = 0;

		if (Options.albums_slide_style)
			slideBorder = 3;

		if (currentMedia === null && previousMedia === null)
			$("html, body").stop().animate({ scrollTop: 0 }, "slow");
		if (populate) {
			thumbnailSize = Options.media_thumb_size;

			populateMedia = populate;
			isVirtualAlbum = (PhotoFloat.isByDateCacheBase(currentAlbum.cacheBase) || PhotoFloat.isByGpsCacheBase(currentAlbum.cacheBase) || PhotoFloat.isSearchCacheBase(currentAlbum.cacheBase) );
			tooBig = currentAlbum.path.split("/").length < 4 && currentAlbum.media.length > Options.big_virtual_folders_threshold;
			if (populateMedia === true && isVirtualAlbum)
				populateMedia = populateMedia && ! tooBig;

			if (isVirtualAlbum && tooBig) {
				$("#thumbs").empty();
				$("#error-too-many-images").html(
					"<span id=\"too-many-images\">" + _t('#too-many-images') + "</span>: " + currentAlbum.media.length +
					" (<span id=\"too-many-images-limit-is\">" + _t('#too-many-images-limit-is') + "</span> " + Options.big_virtual_folders_threshold +  ")</span>"
				).show();
			} else if (
				populateMedia === true ||
				populateMedia == "refreshMedia" ||
				populateMedia == "refreshBoth"
			) {
				media = [];
				for (i = 0; i < currentAlbum.media.length; ++i) {
					width = currentAlbum.media[i].metadata.size[0];
					height = currentAlbum.media[i].metadata.size[1];
					thumbHash = chooseThumbnail(currentAlbum, currentAlbum.media[i], thumbnailSize);

					if (Options.media_thumb_type == "fixed_height") {
						if (height < Options.media_thumb_size) {
							thumbHeight = height;
							thumbWidth = width;
						} else {
							thumbHeight = Options.media_thumb_size;
							thumbWidth = thumbHeight * width / height;
						}
						calculatedWidth = thumbWidth;
					} else if (Options.media_thumb_type == "square") {
						// if (Math.max(width, height) < Options.media_thumb_size) {
						// 	thumbHeight = height;
						// 	thumbWidth = width;
						// } else {
						thumbHeight = thumbnailSize;
						thumbWidth = thumbnailSize;
						// }
						calculatedWidth = Options.media_thumb_size;
					}
					// if (PhotoFloat.isByDateCacheBase(currentAlbum.cacheBase) || PhotoFloat.isByGpsCacheBase(currentAlbum.cacheBase) || PhotoFloat.isSearchCacheBase(currentAlbum.cacheBase)) {
					// 	imgTitle = currentAlbum.media[i].albumName;
					// 	imgTitle = imgTitle.substr(imgTitle.indexOf('/') + 1);
					// } else
					// 	imgTitle = currentAlbum.media[i].name;
					imgTitle = currentAlbum.media[i].albumName;

					mapLinkIcon = "";
					if (hasGpsData(currentAlbum.media[i])) {
						var latitude = currentAlbum.media[i].metadata.latitude;
						var longitude = currentAlbum.media[i].metadata.longitude;
						mapLinkIcon = "<a href=" + mapLink(latitude, longitude, Options.photo_map_zoom_level) + " target='_blank'>" +
													"<img class='thumbnail-map-link' title='" + _t("#show-on-map") + " [s]' alt='" + _t("#show-on-map") + "' height='20px' src='img/ic_place_white_24dp_2x.png'>" +
													"</a>";
					}

					imageString =	"<div class=\"thumb-and-caption-container\" style=\"" +
										"width: " + calculatedWidth + "px;\"" +
									">" +
								"<div class=\"thumb-container\" " + "style=\"" +
										"width: " + calculatedWidth + "px; " +
										"height: " + Options.media_thumb_size + "px;" +
									"\">" +
									mapLinkIcon +
									"<span class=\"helper\"></span>" +
									"<img title=\"" + imgTitle + "\"" +
										"alt=\"" + photoFloat.trimExtension(currentAlbum.media[i].name) + "\"" +
										"src=\"" +  encodeURI(thumbHash) + "\"" +
										"class=\"thumbnail" + "\"" +
										"height=\"" + thumbHeight + "\"" +
										"width=\"" + thumbWidth + "\"" +
									"/>" +
								"</div>" +
								"<div class=\"media-caption\">" +
								"<span>" +
								currentAlbum.media[i].name.replace(/ /g, "</span> <span style='white-space: nowrap;'>") +
								"</span>";
					imageString += "</div>" +
							"</div>";
					image = $(imageString);

					image.get(0).media = currentAlbum.media[i];
					hash = photoFloat.mediaHashURIEncoded(currentAlbum, currentAlbum.media[i]);
					imageLink = $("<a id='link-" + hash + "' href='#!/" + hash + "'></a>");
					imageLink.append(image);
					media.push(imageLink);
					(function(theLink, theImage) {
						theImage.on("error", function() {
							media.splice(media.indexOf(theLink), 1);
							theLink.remove();
							currentAlbum.media.splice(currentAlbum.media.indexOf(theImage.get(0).media), 1);
						});
					})(imageLink, image);
				}

				thumbsElement = $("#thumbs");
				thumbsElement.empty();
				thumbsElement.append.apply(thumbsElement, media);
			}

			if (currentMedia === null) {
				if (fromEscKey && firstEscKey) {
					// respect the existing mediaLink (you cannot do it more than once)
					firstEscKey = false;
				} else {
					// reset mediaLink
					if (currentAlbum.media.length)
						mediaLink = "#!/" + photoFloat.mediaHashURIEncoded(currentAlbum, currentAlbum.media[0]);
					else
						mediaLink = "#!/" + currentAlbum.cacheBase;
					firstEscKey = true;
				}

				upLink = "#!/";
				if (currentAlbum.parentCacheBase && currentAlbum.parentCacheBase != "root") {
					upLink = "#!/" + correctUpHash(currentAlbum.parentCacheBase);
				}

				if (
					populate === true ||
					populate == "refreshSubalbums" ||
					populateMedia == "refreshBoth"
				) {
					subalbums = [];

					// resize down the album buttons if they are too wide
					albumViewWidth = $("body").width() -
							parseInt($("#album-view").css("padding-left")) -
							parseInt($("#album-view").css("padding-right")) -
							scrollBarWidth;
					if ((albumButtonWidth(correctedAlbumThumbSize, buttonBorder) + Options.spacing) * Options.min_album_thumbnail > albumViewWidth) {
						if (Options.albums_slide_style)
							correctedAlbumThumbSize =
								Math.floor((albumViewWidth / Options.min_album_thumbnail - Options.spacing - 2 * slideBorder) / 1.1 - 2 * buttonBorder);
						else
							correctedAlbumThumbSize =
								Math.floor(albumViewWidth / Options.min_album_thumbnail - Options.spacing - 2 * buttonBorder);
					}
					margin = 0;
					if (Options.albums_slide_style)
						margin = Math.round(correctedAlbumThumbSize * 0.05);

					captionFontSize = Math.round(em2px("body", 1) * correctedAlbumThumbSize / Options.album_thumb_size);
					captionHeight = parseInt(captionFontSize * 1.1) + 1;
					if (PhotoFloat.isFolderCacheBase(currentAlbum.cacheBase) && ! Options.show_album_names_below_thumbs)
						heightfactor = 0;
					else if (! Options.show_album_media_count)
						heightfactor = 1.1;
					else
						heightfactor = 2.8;
					buttonAndCaptionHeight = albumButtonWidth(correctedAlbumThumbSize, buttonBorder) + captionHeight * heightfactor;

					// insert into DOM
					subalbumsElement = $("#subalbums");
					subalbumsElement.empty();
					subalbumsElement.insertBefore(thumbsElement);

					for (i = 0; i < currentAlbum.subalbums.length; ++i) {
						if (PhotoFloat.isSearchCacheBase(currentAlbum.cacheBase)) {
							subfolderHash = PhotoFloat.pathJoin([
								currentAlbum.subalbums[i].cacheBase,
								currentAlbum.cacheBase + Options.cache_folder_separator + currentAlbum.subalbums[i].cacheBase
							]);
						} else if (searchCacheBase) {
							subfolderHash = PhotoFloat.pathJoin([
								currentAlbum.subalbums[i].cacheBase,
								[searchCacheBase, searchSubAlbum].join(Options.cache_folder_separator)
							]);
						} else {
							subfolderHash = currentAlbum.subalbums[i].cacheBase;
						}

						// generate the subalbum caption
						if (PhotoFloat.isByDateCacheBase(currentAlbum.cacheBase)) {
							folderArray = currentAlbum.subalbums[i].cacheBase.split(Options.cache_folder_separator);
							folder = "";
							if (folderArray.length >= 2)
								folder += folderArray[1];
							if (folderArray.length >= 3)
								folder += "-" + folderArray[2];
							if (folderArray.length == 4)
								folder += "-" + folderArray[3];
						} else if (PhotoFloat.isByGpsCacheBase(currentAlbum.cacheBase)) {
							var level = currentAlbum.subalbums[i].cacheBase.split(Options.cache_folder_separator).length - 2;
							var folderName = '';
							var folderTitle = '';
							if (currentAlbum.subalbums[i].name === '')
								folderName = _t('.not-specified');
							else if (level < 2)
								folderName = currentAlbum.subalbums[i].name;
							else
								folderName = transformAltPlaceName(currentAlbum.subalbums[i].alt_name);
							folderTitle = _t('#place-icon-title') + folderName;

							folder = "<span class='gps-folder'>" +
												folderName +
												"<a href='" + mapLink(currentAlbum.subalbums[i].center.latitude, currentAlbum.subalbums[i].center.longitude, Options.map_zoom_levels[level]) +
																"' title='" + folderName +
																"' target='_blank'" +
														">" +
													"<img class='title-img' title='" + folderTitle + "'  alt='" + folderTitle + "' height='15px' src='img/ic_place_white_24dp_2x.png' />" +
												"</a>" +
											"</span>";
						}
						else {
							folder = currentAlbum.subalbums[i].path;
						}

						// // get the value in style sheet (element with that class doesn't exist in DOM)
						// var $el = $('<div class="album-caption"></div>');
						// $($el).appendTo('body');
						// $($el).remove();
						captionColor = Options.albums_slide_style ? Options.slide_album_caption_color : Options.album_caption_color;

						captionHtml = "<div class='album-caption";
						if (PhotoFloat.isFolderCacheBase(currentAlbum.cacheBase) && ! Options.show_album_names_below_thumbs)
							captionHtml += " hidden";
						captionHtml += "' id='album-caption-" + PhotoFloat.hashCode(currentAlbum.subalbums[i].cacheBase) + "'" +
													"style='" +
														"width: " + correctedAlbumThumbSize + "px; " +
														"font-size: " + captionFontSize + "px; " +
														"height: " + captionHeight + "px; " +
														"color: " + captionColor + ";" +
													"'" +
													">" + folder + "</div>";

						captionHtml += "<div class='album-caption-count";
						if (PhotoFloat.isFolderCacheBase(currentAlbum.cacheBase) && ! Options.show_album_names_below_thumbs || ! Options.show_album_media_count)
							captionHtml += " hidden";
						captionHtml += "'" +
									"style='" +
										"font-size: " + Math.round((captionFontSize / 1.5)) + "px; " +
										"height: " + captionHeight + "px; " +
										"color: " + captionColor + ";" +
									"'" +
								">(";
						captionHtml +=		currentAlbum.subalbums[i].numMediaInSubTree;
						captionHtml +=		" <span class='title-media'>";
						captionHtml +=		_t(".title-media");
						captionHtml +=		"</span>";
						captionHtml += ")</div>";
						caption = $(captionHtml);


						// a dot could be present in a cache base, making $("#" + cacheBase) fail, beware...
						albumButtonAndCaptionHtml =
							"<div id='" + PhotoFloat.hashCode(currentAlbum.subalbums[i].cacheBase) + "' " +
								"class='album-button-and-caption";
						if (Options.albums_slide_style)
							albumButtonAndCaptionHtml += " slide";
						albumButtonAndCaptionHtml +=
								"' " +
								"style='" +
									"margin-right: " + Options.spacing + "px; " +
									"margin-top: " + Options.spacing + "px; " +
									"height: " + buttonAndCaptionHeight + "px; " +
									"width: " + albumButtonWidth(correctedAlbumThumbSize, buttonBorder) + "px; ";
						if (Options.albums_slide_style)
							albumButtonAndCaptionHtml += "background-color:" + Options.album_button_background_color + ";";
						albumButtonAndCaptionHtml +=
								"'" +
							">" +
							"</div>";
						linkContainer = $(albumButtonAndCaptionHtml);

						image = $(
											"<div " +
											 	"class='album-button' " +
												"style='" +
													"width:" + correctedAlbumThumbSize + "px; " +
													"height:" + correctedAlbumThumbSize + "px; " +
													"margin:" + margin + "px;" +
												"'" +
												">" +
												"</div>"
										);
						linkContainer.append(image);
						linkContainer.append(caption);

						subalbumsElement.append(linkContainer);
						container = $("#" + PhotoFloat.hashCode(currentAlbum.subalbums[i].cacheBase));
						// add the clicks
						container.off('click').css("cursor", "pointer").on('click', {hash: subfolderHash}, function(ev) {
							window.location.href = "#!/" + ev.data.hash;
						});

						//////////////////// begin anonymous function /////////////////////
						//      })(currentAlbum.subalbums[i], image, container);
						(function(theSubalbum, theImage, theLink) {
							// function(subalbum, container, callback, error)  ---  callback(album,   album.media[index], container,            subalbum);
							photoFloat.pickRandomMedia(theSubalbum, currentAlbum, function(randomAlbum, randomMedia, theOriginalAlbumContainer, subalbum) {
								var htmlText, maxHeight, difference;
								var titleName, link, goTo, humanGeonames;
								var mediaSrc = chooseThumbnail(randomAlbum, randomMedia, Options.album_thumb_size);
								var overflow;

								PhotoFloat.subalbumIndex ++;
								mediaWidth = randomMedia.metadata.size[0];
								mediaHeight = randomMedia.metadata.size[1];
								if (Options.album_thumb_type == "fit") {
									if (mediaWidth < correctedAlbumThumbSize && mediaHeight < correctedAlbumThumbSize) {
										thumbWidth = mediaWidth;
										thumbHeight = mediaHeight;
									} else {
										if (mediaWidth > mediaHeight) {
											thumbWidth = correctedAlbumThumbSize;
											thumbHeight = Math.floor(correctedAlbumThumbSize * mediaHeight / mediaWidth);
										} else {
											thumbWidth = Math.floor(correctedAlbumThumbSize * mediaWidth / mediaHeight);
											thumbHeight = correctedAlbumThumbSize;
										}
									}
								} else if (Options.album_thumb_type == "square") {
									thumbWidth = correctedAlbumThumbSize;
									thumbHeight = correctedAlbumThumbSize;
								}

								if (PhotoFloat.isByDateCacheBase(currentAlbum.cacheBase)) {
									titleName = PhotoFloat.pathJoin([randomMedia.dayAlbum, randomMedia.name]);
									link = PhotoFloat.pathJoin(["#!", randomMedia.dayAlbumCacheBase, randomMedia.foldersCacheBase, randomMedia.cacheBase]);
								} else if (PhotoFloat.isByGpsCacheBase(currentAlbum.cacheBase)) {
									humanGeonames = PhotoFloat.pathJoin([Options.by_gps_string, randomMedia.geoname.country_name, randomMedia.geoname.region_name, randomMedia.geoname.place_name]);
									titleName = PhotoFloat.pathJoin([humanGeonames, randomMedia.name]);
									link = PhotoFloat.pathJoin(["#!", randomMedia.gpsAlbumCacheBase, randomMedia.foldersCacheBase, randomMedia.cacheBase]);
								} else if (PhotoFloat.isSearchCacheBase(currentAlbum.cacheBase)) {
									titleName = randomMedia.albumName;
									link = PhotoFloat.pathJoin(["#!", randomMedia.foldersCacheBase, currentAlbum.cacheBase + Options.cache_folder_separator + theSubalbum.cacheBase, randomMedia.cacheBase]);
								} else {
									titleName = randomMedia.albumName;
									link = PhotoFloat.pathJoin(["#!", randomMedia.foldersCacheBase, randomMedia.cacheBase]);
								}
								titleName = titleName.substr(titleName.indexOf('/') + 1);
								goTo = _t(".go-to") + " " + titleName;
								htmlText =	"<a href=\"" + link + "\">" +
										"<img src=\"img/link-arrow.png\" " +
											"title=\"" + goTo + "\" " +
											"alt=\"" + goTo + "\" " +
											"class=\"album-button-random-media-link\" " +
											" style=\"width: 20px;" +
												" height: 20px;" +
												"\"" +">" +
										"</a>" +
										"<span class=\"helper\"></span>" +
										"<img " +
											"title=\"" + titleName + "\"" +
											" class=\"thumbnail\"" +
											" src=\"" + encodeURI(mediaSrc) + "\"" +
											" style=\"width:" + thumbWidth + "px;" +
												" height:" + thumbHeight + "px;" +
												"\"" +
										">";
								theImage.html(htmlText);

								numSubAlbumsReady ++;
								if (numSubAlbumsReady >= theOriginalAlbumContainer.subalbums.length) {
									// now all the subalbums random thumbnails has been loaded
									// we can run the function that prepare the stuffs for sharing
									socialButtons();
								}
							}, function error() {
								currentAlbum.subalbums.splice(currentAlbum.subalbums.indexOf(theSubalbum), 1);
								theLink.remove();
								subalbums.splice(subalbums.indexOf(theLink), 1);
							});
							i ++; i --;
						})(currentAlbum.subalbums[i], image, container);
						//////////////////// end anonymous function /////////////////////
					}

					$("#subalbums").show();
					$("#album-view").removeClass("media-view-container");

					// check for overflow in album-caption class in order to adapt album caption height to the string length
					// when diving into search subalbum, the whole album path is showed and it can be lengthy
					maxHeight = null;
					$('.album-caption').each(function() {
						var thisHeight = $(this)[0].scrollHeight;
						maxHeight = (thisHeight > maxHeight) ? thisHeight : maxHeight;
					});
					difference = maxHeight - parseFloat($(".album-caption").css("height"));
					$(".album-button-and-caption").css("height", (parseInt($(".album-button-and-caption").css("height")) + difference) + 'px');
					$(".album-caption").css("height", maxHeight + 'px');

					if (Options.albums_slide_style)
						$(".album-button").css("background-color", Options.album_button_background_color);
					else
						$(".album-button").css("border", "none");
				}
			}

		}

		if (currentMedia === null) {
			$(".thumb-container").removeClass("current-thumb");
			$("#album-view").removeClass("media-view-container");
			if (currentAlbum.subalbums.length > 0)
				$("#subalbums").show();
			else
				$("#subalbums").hide();
			$("#media-view").hide();
			$("#media-view").removeClass("no-bottom-space");
			$("#album-view").removeClass("no-bottom-space");
			$("#media-box-inner").empty();
			$("#media-box").hide();
			$("#thumbs").show();
			var foldersViewLink = "#!/" + encodeURIComponent(Options.folders_string);
			var byDateViewLink = "#!/" + encodeURIComponent(Options.by_date_string);
			var byGpsViewLink = "#!/" + encodeURIComponent(Options.by_gps_string);
			$(".day-gps-folders-view").removeClass("selected").addClass("active").removeClass("hidden").off("click");
			if (currentAlbum.cacheBase == Options.folders_string) {
				$("#folders-view").removeClass("active").addClass("selected");
				$("#by-date-view").on("click", function(ev) {
					window.location.href = byDateViewLink;
				});
				photoFloat.addClickToByGpsButton(byGpsViewLink);
			} else if (currentAlbum.cacheBase == Options.by_date_string) {
				$("#folders-view").on("click", function(ev) {
					window.location.href = foldersViewLink;
				});
				$("#by-date-view").removeClass("active").addClass("selected");
				photoFloat.addClickToByGpsButton(byGpsViewLink);
			}	else if (currentAlbum.cacheBase == Options.by_gps_string) {
				$("#folders-view").on("click", function(ev) {
					window.location.href = foldersViewLink;
				});
				$("#by-date-view").on("click", function(ev) {
					window.location.href = byDateViewLink;
				});
				$("#by-gps-view").removeClass("active").addClass("selected");
			} else if (
				PhotoFloat.isSearchCacheBase(currentAlbum.cacheBase) && currentAlbum.media.length === 0 && currentAlbum.subalbums.length === 0
			) {
				$("#folders-view").on("click", function(ev) {
					$("#album-view").removeClass("hidden");
					$(".search-failed").hide();
					window.location.href = foldersViewLink;
				});
				$("#by-date-view").on("click", function(ev) {
					$(".search-failed").hide();
					$("#album-view").removeClass("hidden");
					window.location.href = byDateViewLink;
				});
				photoFloat.addClickToByGpsButton(byGpsViewLink);
			} else {
				$(".day-gps-folders-view").addClass("hidden");
			}
			$("#powered-by").show();
		} else {
			if (currentAlbum.media.length == 1)
				$("#thumbs").hide();
			else
				$("#thumbs").show();
			$("#powered-by").hide();
		}

		setOptions();

		setTimeout(scrollToThumb, 1);
	}

	function lateralSocialButtons() {
		return $(".ssk-group").css("display") == "block";
	}
	function bottomSocialButtons() {
		return ! lateralSocialButtons();
	}
	function scaleMedia() {
		var media, container, containerBottom = 0, containerTop = 0, containerRatio, photoSrc, previousSrc;
		var containerHeight = $(window).innerHeight(), containerWidth = $(window).innerWidth(), mediaBarBottom = 0;
		var width = currentMedia.metadata.size[0], height = currentMedia.metadata.size[1], ratio = width / height;

		if (fullScreenStatus && Modernizr.fullscreen)
			container = $(window);
		else {
			container = $("#media-view");
			if ($("#thumbs").is(":visible"))
				containerBottom = $("#album-view").outerHeight();
			else if (bottomSocialButtons() && containerBottom < $(".ssk").outerHeight())
				// correct container bottom when social buttons are on the bottom
				containerBottom = $(".ssk").outerHeight();
			containerTop = 0;
			if ($("#title-container").is(":visible"))
				containerTop = $("#title-container").outerHeight();
			containerHeight -= containerBottom + containerTop;
			container.css("top", containerTop + "px");
			container.css("bottom", containerBottom + "px");
		}

		containerRatio = containerWidth / containerHeight;

		media = $("#media");
		media.off();

		if (currentMedia.mediaType == "photo") {
			photoSrc = chooseReducedPhoto(currentMedia, container);
			previousSrc = media.attr("src");
			// chooseReducedPhoto() sets maxSize to 0 if it returns the original media
			if (maxSize) {
				if (width > height && width > maxSize) {
					height = Math.round(height * maxSize / width);
					width = maxSize;
				} else if (height > width && height > maxSize) {
					width = Math.round(width * maxSize / height);
					height = maxSize;
				}
			}
			if (photoSrc != previousSrc || media.attr("width") != width || media.attr("height") != height) {
				$("link[rel=image_src]").remove();
				$('link[rel="video_src"]').remove();
				$("head").append("<link rel=\"image_src\" href=\"" + encodeURI(photoSrc) + "\" />");
				media
					.attr("src", encodeURI(photoSrc))
					.attr("width", width)
					.attr("height", height)
					.attr("ratio", ratio);
			}
		}

		if (parseInt(media.attr("width")) > containerWidth && media.attr("ratio") > containerRatio) {
			height = container.width() / media.attr("ratio");
			media
				.css("width", containerWidth + "px")
				.css("height", (containerWidth / ratio) + "px")
				.parent()
					.css("height", height)
					.css("margin-top", - height / 2)
					.css("top", "50%");
			if (currentMedia.mediaType == "video")
				mediaBarBottom = 0;
			else if (currentMedia.mediaType == "photo")
				mediaBarBottom = (containerHeight - containerWidth / ratio) / 2;
		} else if (parseInt(media.attr("height")) > containerHeight && media.attr("ratio") < containerRatio) {
			media
				.css("height", containerHeight + "px")
				.css("width", (containerHeight * ratio) + "px")
				.parent()
					.css("height", "100%")
					.css("margin-top", "0")
					.css("top", "0");
			if (currentMedia.mediaType == "video") {
				media.css("height", parseInt(media.css("height")) - $("#links").outerHeight());
				mediaBarBottom = 0;
			} else if (currentMedia.mediaType == "photo")
				// put media bar slightly below so that video buttons are not covered
				mediaBarBottom = 0;
		} else {
			media
				.css("height", "")
				.css("width", "")
				.parent()
					.css("height", media.attr("height"))
					.css("margin-top", - media.attr("height") / 2)
					.css("top", "50%");
			mediaBarBottom = (container.height() - media.attr("height")) / 2;
			if (fullScreenStatus) {
				if (currentMedia.mediaType == "video") {
					mediaBarBottom = 0;
				}
			}
		}

		$("#media-bar").css("bottom", 0);

		media.show();

		if (! fullScreenStatus && currentAlbum.media.length > 1 && lateralSocialButtons()) {
			// correct back arrow position when social buttons are on the left
			$("#prev").css("left", "");
			$("#prev").css("left", (parseInt($("#prev").css("left")) + $(".ssk").outerWidth()) + "px");
		}

		$(window).on("resize", scaleMedia);
	}
	function chooseReducedPhoto(media, container) {
		var chosenMedia, reducedWidth, reducedHeight;
		var mediaWidth = media.metadata.size[0], mediaHeight = media.metadata.size[1];
		var mediaSize = Math.max(mediaWidth, mediaHeight);
		var mediaRatio = mediaWidth / mediaHeight, containerRatio;

		chosenMedia = PhotoFloat.originalMediaPath(media);
		maxSize = 0;

		if (container === null) {
			// try with what is more probable to be the container
			if (fullScreenStatus)
				container = $(window);
			else {
				container = $("#media-view");
			}
		}

		containerRatio = container.width() / container.height();

		for (var i = 0; i < Options.reduced_sizes.length; i++) {
			if (Options.reduced_sizes[i] < mediaSize) {
				if (mediaWidth > mediaHeight) {
					reducedWidth = Options.reduced_sizes[i];
					reducedHeight = Options.reduced_sizes[i] * mediaHeight / mediaWidth;
				} else {
					reducedHeight = Options.reduced_sizes[i];
					reducedWidth = Options.reduced_sizes[i] * mediaWidth / mediaHeight;
				}

				if (
					mediaRatio > containerRatio && reducedWidth < container.width() * screenRatio ||
					mediaRatio < containerRatio && reducedHeight < container.height() * screenRatio
				)
					break;
			}
			chosenMedia = photoFloat.mediaPath(currentAlbum, media, Options.reduced_sizes[i]);
			maxSize = Options.reduced_sizes[i];
		}
		return chosenMedia;
	}

	function chooseThumbnail(album, media, thumbnailSize) {
		return photoFloat.mediaPath(album, media, thumbnailSize);
	}

	function showMedia(album) {
		var width = currentMedia.metadata.size[0], height = currentMedia.metadata.size[1];
		var prevMedia, nextMedia, text, thumbnailSize, i, linkTag, triggerLoad, videoOK = true;
		var nextReducedPhoto, prevReducedPhoto;
		var exposureTime;

		mediaLink = "#!/" + photoFloat.mediaHashURIEncoded(currentAlbum, currentMedia);
		firstEscKey = true;

		thumbnailSize = Options.media_thumb_size;
		$("#media-box").show();
		if (currentAlbum.media.length == 1) {
			$("#next").hide();
			$("#prev").hide();
			$("#media-view").addClass("no-bottom-space");
			$("#album-view").addClass("no-bottom-space");
			$("#thumbs").hide();
		} else {
			$("#next").show();
			$("#prev").show();
			$("#media-view").removeClass("no-bottom-space");
			$("#album-view").removeClass("no-bottom-space");
			$("#media-view").css("bottom", (thumbnailSize + 15).toString() + "px");
			$("#album-view").css("height", (thumbnailSize + 20).toString() + "px");
			$("#album-view").addClass("media-view-container");
			$("#album-view.media-view-container").css("height", (thumbnailSize + 22).toString() + "px");
			$("#thumbs").show();
		}

		var albumViewHeight = 0;
		if ($("#album-view").is(":visible"))
			albumViewHeight = $("#album-view").outerHeight();

		$('#media').remove();
		$("#media").off("load");

		if (currentMedia.mediaType == "video") {
			if (! Modernizr.video) {
				$('<div id="video-unsupported-html5">' + _t("#video-unsupported-html5") + '</div>').appendTo('#media-box-inner');
				videoOK = false;
			}
			else if (! Modernizr.video.h264) {
				$('<div id="video-unsupported-h264">' + _t("#video-unsupported-h264") + '</div>').appendTo('#media-box-inner');
				videoOK = false;
			}
		}

		if (currentMedia.mediaType == "photo" || currentMedia.mediaType == "video" && videoOK) {

			if (currentMedia.mediaType == "video") {
				if (fullScreenStatus && currentMedia.albumName.match(/\.avi$/) === null) {
					// .avi videos are not played by browsers
					videoSrc = currentMedia.albumName;
				} else {
					videoSrc = photoFloat.mediaPath(currentAlbum, currentMedia, "");
				}
				$('<video/>', { id: 'media', controls: true })
					.appendTo('#media-box-inner')
					.attr("width", width)
					.attr("height", height)
					.attr("ratio", width / height)
					.attr("src", encodeURI(videoSrc))
					.attr("alt", currentMedia.name);
				triggerLoad = "loadstart";
				linkTag = "<link rel=\"video_src\" href=\"" + encodeURI(videoSrc) + "\" />";
			} else if (currentMedia.mediaType == "photo") {
				photoSrc = chooseReducedPhoto(currentMedia, null);
				if (maxSize) {
					if (width > height &&  width > maxSize) {
						height = Math.round(height * maxSize / width);
						width = maxSize;
					} else if (height > width && height > maxSize) {
						width = Math.round(width * maxSize / height);
						height = maxSize;
					}
				}

				$('<img/>', { id: 'media' })
					.appendTo('#media-box-inner')
					.hide()
					.attr("width", width)
					.attr("height", height)
					.attr("ratio", width / height)
					.attr("src", encodeURI(photoSrc))
					.attr("alt", currentMedia.name)
					.attr("title", currentMedia.date);
				linkTag = "<link rel=\"image_src\" href=\"" + encodeURI(photoSrc) + "\" />";
				triggerLoad = "load";
			}

			$("link[rel=image_src]").remove();
			$('link[rel="video_src"]').remove();
			$("head").append(linkTag);
			$('#media').on(triggerLoad, scaleMedia());
			if (! Options.persistent_metadata) {
				$("#metadata").hide();
				$("#metadata-show").show();
				$("#metadata-hide").hide();
			}

			if (currentAlbum.media.length > 1) {
				i = currentMediaIndex;
				currentAlbum.media[currentMediaIndex].byDateName =
					PhotoFloat.pathJoin([currentAlbum.media[currentMediaIndex].dayAlbum, currentAlbum.media[currentMediaIndex].name]);
				currentAlbum.media[currentMediaIndex].byGpsName =
						PhotoFloat.pathJoin([currentAlbum.media[currentMediaIndex].gpsAlbum, currentAlbum.media[currentMediaIndex].name]);
				if (i === 0)
					i = currentAlbum.media.length - 1;
				else
					i --;
				prevMedia = currentAlbum.media[i];
				prevMedia.byDateName = PhotoFloat.pathJoin([prevMedia.dayAlbum, prevMedia.name]);
				prevMedia.byGpsName = PhotoFloat.pathJoin([prevMedia.gpsAlbum, prevMedia.name]);

				i = currentMediaIndex;
				if (i == currentAlbum.media.length - 1)
					i = 0;
				else
					i ++;
				nextMedia = currentAlbum.media[i];
				nextMedia.byDateName = PhotoFloat.pathJoin([nextMedia.dayAlbum, nextMedia.name]);
				nextMedia.byGpsName = PhotoFloat.pathJoin([nextMedia.gpsAlbum, nextMedia.name]);

				if (nextMedia.mediaType == "photo") {
					nextReducedPhoto = chooseReducedPhoto(nextMedia, null);
					$.preloadImages(nextReducedPhoto);
				}
				if (prevMedia.mediaType == "photo") {
					prevReducedPhoto = chooseReducedPhoto(prevMedia, null);
					$.preloadImages(prevReducedPhoto);
				}
			}
		}

		$("#media-view").off('contextmenu click mousewheel');
		$("#media-bar").off();
		$('#next').off();
		$('#prev').off();


		if (currentAlbum.media.length == 1) {
			if (currentAlbum.parentCacheBase && currentAlbum.parentCacheBase != "root")
				upLink = "#!/" + correctUpHash(currentAlbum.parentCacheBase);
			nextLink = "";
			prevLink = "";
			$("#media-view").css('cursor', 'default');
		} else {
			upLink = "#!/" + correctUpHash(currentAlbum.cacheBase);
			nextLink = "#!/" + photoFloat.mediaHashURIEncoded(currentAlbum, nextMedia);
			prevLink = "#!/" + photoFloat.mediaHashURIEncoded(currentAlbum, prevMedia);
			$("#next").show();
			$("#prev").show();
			$("#media-view")
				.css('cursor', '')
				.on('contextmenu', function(ev) {
					if (! ev.shiftKey && ! ev.ctrlKey && ! ev.altKey) {
						ev.preventDefault();
						swipeRight(prevLink);
					}
				})
				.on('click', function(ev) {
					if (ev.which == 1 && ! ev.altKey && (! ev.shiftKey && ! ev.ctrlKey && currentMedia.mediaType == "photo" || (ev.shiftKey || ev.ctrlKey) && currentMedia.mediaType == "video")) {
						swipeLeft(nextLink);
						return false;
					} else {
						return true;
					}
				})
				.on('mousewheel', swipeOnWheel);
				$("#media-bar").on('click', function(ev) {
					ev.stopPropagation();
				}).on('contextmenu', function(ev) {
					ev.stopPropagation();
				});
			$('#next').on('click', function(ev) {
				if (ev.which == 1 && ! ev.shiftKey && ! ev.ctrlKey && ! ev.altKey) {
					swipeLeft(nextLink);
					return false;
				}
			});
			$('#prev').on('click', function(ev) {
				if (ev.which == 1 && ! ev.shiftKey && ! ev.ctrlKey && ! ev.altKey) {
					swipeRight(prevLink);
					return false;
				}
			});
		}

		$("#original-link").attr("target", "_blank").attr("href", encodeURI(photoFloat.originalMediaPath(currentMedia)));
		$("#download-link").attr("href", encodeURI(photoFloat.originalMediaPath(currentMedia))).attr("download", "");
		if (hasGpsData(currentMedia)) {
			$("#menu-map-link").attr("target", "_blank").attr("href", encodeURI(mapLink(currentMedia.metadata.latitude, currentMedia.metadata.longitude, Options.photo_map_zoom_level)));
			$('#menu-map-link').show();
			$('#menu-map-divider').show();
		} else {
			$("#menu-map-link").removeAttr("href").css("cursor","pointer");
			$('#menu-map-link').hide();
			$('#menu-map-divider').hide();
		}

		var foldersViewLink = "#!/" + PhotoFloat.pathJoin([
									currentMedia.foldersCacheBase,
									currentMedia.cacheBase
								]);
		var byDateViewLink = "#!/" + PhotoFloat.pathJoin([
									currentMedia.dayAlbumCacheBase,
									currentMedia.foldersCacheBase,
									currentMedia.cacheBase
								]);
		var byGpsViewLink = "#!/" + PhotoFloat.pathJoin([
									currentMedia.gpsAlbumCacheBase,
									currentMedia.foldersCacheBase,
									currentMedia.cacheBase
								]);


		$(".day-gps-folders-view").addClass("active").removeClass("hidden").removeClass("selected").off("click");
		if (PhotoFloat.isFolderCacheBase(currentAlbum.cacheBase)) {
			// folder album: change to by date or by gps view
			$("#folders-view").removeClass("active").addClass("selected").off("click");
			$("#by-date-view").on("click", function(ev) {
				window.location.href = byDateViewLink;
				return false;
			});

			if (! hasGpsData(currentMedia)) {
				$("#by-gps-view").addClass("hidden");
			} else {
				$("#by-gps-view").on("click", function(ev) {
					window.location.href = byGpsViewLink;
					return false;
				});
			}
		} else if (PhotoFloat.isByDateCacheBase(currentAlbum.cacheBase)) {
			// by date album: change to folder or by gps view
			$("#folders-view").on("click", function(ev) {
				window.location.href = foldersViewLink;
				return false;
			});
			$("#by-date-view").removeClass("active").addClass("selected").off("click");
			if (! hasGpsData(currentMedia)) {
				$("#by-gps-view").addClass("hidden");
			} else {
				$("#by-gps-view").on("click", function(ev) {
					window.location.href = byGpsViewLink;
					return false;
				});
			}
		} else if (PhotoFloat.isByGpsCacheBase(currentAlbum.cacheBase)) {
			$("#folders-view").on("click", function(ev) {
				window.location.href = foldersViewLink;
				return false;
			});
			$("#by-date-view").on("click", function(ev) {
				window.location.href = byDateViewLink;
				return false;
			});
			// by gps album: change to folder or by day view
			$("#by-gps-view").removeClass("active").addClass("selected").off("click");
		} else if (PhotoFloat.isSearchCacheBase(currentAlbum.cacheBase)) {
			// by search album: change to folder or by gps or by view
			$("#folders-view").on("click", function(ev) {
				window.location.href = foldersViewLink;
				return false;
			});
			$("#by-date-view").on("click", function(ev) {
				window.location.href = byDateViewLink;
				return false;
			});
			if (! hasGpsData(currentMedia)) {
				$("#by-gps-view").addClass("hidden");
			} else {
				$("#by-gps-view").on("click", function(ev) {
					window.location.href = byGpsViewLink;
					return false;
				});
			}
		}

		$('#metadata tr.gps').off('click');
		text = "<table>";
		if (typeof currentMedia.metadata.title !== "undefined")
			text += "<tr><td id=\"metadata-data-title\"></td><td>" + currentMedia.metadata.title.replace(/\n/g, "<br>") + "</td></tr>";
		if (typeof currentMedia.metadata.description !== "undefined")
			text += "<tr><td id=\"metadata-data-description\"></td><td>" + currentMedia.metadata.description.replace(/\n/g, "<br>") + "</td></tr>";
		if (typeof currentMedia.metadata.tags !== "undefined")
			text += "<tr><td id=\"metadata-data-tags\"></td><td>" + currentMedia.metadata.tags + "</td></tr>";
		if (typeof currentMedia.date !== "undefined")
			text += "<tr><td id=\"metadata-data-date\"></td><td>" + currentMedia.date + "</td></tr>";
		if (typeof currentMedia.metadata.size !== "undefined")
			text += "<tr><td id=\"metadata-data-size\"></td><td>" + currentMedia.metadata.size[0] + " x " + currentMedia.metadata.size[1] + "</td></tr>";
		if (typeof currentMedia.metadata.make !== "undefined")
			text += "<tr><td id=\"metadata-data-make\"></td><td>" + currentMedia.metadata.make + "</td></tr>";
		if (typeof currentMedia.metadata.model !== "undefined")
			text += "<tr><td id=\"metadata-data-model\"></td><td>" + currentMedia.metadata.model + "</td></tr>";
		if (typeof currentMedia.metadata.aperture !== "undefined")
			text += "<tr><td id=\"metadata-data-aperture\"></td><td> f/" + currentMedia.metadata.aperture + "</td></tr>";
		if (typeof currentMedia.metadata.focalLength !== "undefined")
			text += "<tr><td id=\"metadata-data-focalLength\"></td><td>" + currentMedia.metadata.focalLength + " mm</td></tr>";
		if (typeof currentMedia.metadata.subjectDistanceRange !== "undefined")
			text += "<tr><td id=\"metadata-data-subjectDistanceRange\"></td><td>" + currentMedia.metadata.subjectDistanceRange + "</td></tr>";
		if (typeof currentMedia.metadata.iso !== "undefined")
			text += "<tr><td id=\"metadata-data-iso\"></td><td>" + currentMedia.metadata.iso + "</td></tr>";
		if (typeof currentMedia.metadata.sceneCaptureType !== "undefined")
			text += "<tr><td id=\"metadata-data-sceneCaptureType\"></td><td>" + currentMedia.metadata.sceneCaptureType + "</td></tr>";
		if (typeof currentMedia.metadata.exposureTime !== "undefined") {
			if (typeof currentMedia.metadata.exposureTime === "string")
				exposureTime = currentMedia.metadata.exposureTime;
			else if (currentMedia.metadata.exposureTime > 0.3)
				exposureTime = Math.round(currentMedia.metadata.exposureTime * 10 ) / 10;
			else
				exposureTime = "1/" + Math.round(1 / currentMedia.metadata.exposureTime);
			text += "<tr><td id=\"metadata-data-exposureTime\"></td><td>" + exposureTime + " sec</td></tr>";
		}
		if (typeof currentMedia.metadata.exposureProgram !== "undefined")
			text += "<tr><td id=\"metadata-data-exposureProgram\"></td><td>" + currentMedia.metadata.exposureProgram + "</td></tr>";
		if (typeof currentMedia.metadata.exposureCompensation !== "undefined")
			text += "<tr><td id=\"metadata-data-exposureCompensation\"></td><td>" + currentMedia.metadata.exposureCompensation + "</td></tr>";
		if (typeof currentMedia.metadata.spectralSensitivity !== "undefined")
			text += "<tr><td id=\"metadata-data-spectralSensitivity\"></td><td>" + currentMedia.metadata.spectralSensitivity + "</td></tr>";
		if (typeof currentMedia.metadata.sensingMethod !== "undefined")
			text += "<tr><td id=\"metadata-data-sensingMethod\"></td><td>" + currentMedia.metadata.sensingMethod + "</td></tr>";
		if (typeof currentMedia.metadata.lightSource !== "undefined")
			text += "<tr><td id=\"metadata-data-lightSource\"></td><td>" + currentMedia.metadata.lightSource + "</td></tr>";
		if (typeof currentMedia.metadata.flash !== "undefined")
			text += "<tr><td id=\"metadata-data-flash\"></td><td>" + currentMedia.metadata.flash + "</td></tr>";
		if (typeof currentMedia.metadata.orientationText !== "undefined")
			text += "<tr><td id=\"metadata-data-orientation\"></td><td>" + currentMedia.metadata.orientationText + "</td></tr>";
		if (typeof currentMedia.metadata.duration !== "undefined")
			text += "<tr><td id=\"metadata-data-duration\"></td><td>" + currentMedia.metadata.duration + " sec</td></tr>";
		if (typeof currentMedia.metadata.latitude !== "undefined")
			text += "<tr id='map-link' class='gps'><td id=\"metadata-data-latitude\"></td><td>" + currentMedia.metadata.latitudeMS + " </td></tr>";
		if (typeof currentMedia.metadata.longitude !== "undefined")
			text += "<tr class='gps'><td id=\"metadata-data-longitude\"></td><td>" + currentMedia.metadata.longitudeMS + " </td></tr>";
		text += "</table>";
		$("#metadata").html(text);
		var linkTitle = _t('#show-map') + Options.map_service;
		$('#metadata tr.gps').attr("title", linkTitle).on('click', function(ev) {
			ev.stopPropagation();
			window.open(mapLink(currentMedia.metadata.latitude, currentMedia.metadata.longitude, Options.photo_map_zoom_level), '_blank');
		});

		translate();

		$("#subalbums").hide();
		$("#media-view").show();
	}

	function hasGpsData(media) {
		return media.mediaType == "photo" && typeof media.metadata.latitude !== "undefined";
	}

	function mapLink(latitude, longitude, zoom) {
		var link;
		if (Options.map_service == 'openstreetmap') {
			link = 'http://www.openstreetmap.org/#map=' + zoom + '/' + latitude + '/' + longitude;
		}
		else if (Options.map_service == 'googlemaps') {
			link = 'https://www.google.com/maps/@' + latitude + ',' + longitude + ',' + zoom + 'z';
		}
		else if (Options.map_service == 'osmtools') {
			link = 'http://m.osmtools.de/index.php?mlon=' + longitude + '&mlat=' + latitude + '&icon=6&zoom=' + zoom;
		}
		return link;
	}

	function setOptions() {
		var albumThumbnailSize, mediaThumbnailSize;
		albumThumbnailSize = Options.album_thumb_size;
		mediaThumbnailSize = Options.media_thumb_size;
		$("body").css("background-color", Options.background_color);

		$("#title").css("font-size", Options.title_font_size);
		$(".title-anchor").css("color", Options.title_color);
		$(".title-anchor").hover(function() {
			//mouse over
			$(this).css("color", Options.title_color_hover);
		}, function() {
			//mouse out
			$(this).css("color", Options.title_color);
		});
		$("#media-name").css("color", Options.title_image_name_color);
		$(".thumb-and-caption-container").css("margin-right", Options.spacing.toString() + "px");

		if (currentMedia !== null || ! Options.show_media_names_below_thumbs)
			$(".media-caption").addClass("hidden");
		else
			$(".media-caption").removeClass("hidden");

		if (Options.show_album_media_count)
			$("#title-count").removeClass("hidden");
		else
			$("#title-count").addClass("hidden");

	}

	function em2px(selector, em) {
		var emSize = parseFloat($(selector).css("font-size"));
		return (em * emSize);
	}
	function getBooleanCookie(key) {
		var keyValue = document.cookie.match('(^|;) ?' + key + '=([^;]*)(;|$)');
		if (! keyValue)
			return null;
		else if (keyValue[2] == 1)
			return true;
		else
			return false;
	}
	function setBooleanCookie(key, value) {
		var expires = new Date();
		expires.setTime(expires.getTime() + (1 * 24 * 60 * 60 * 1000));
		if (value)
			value = 1;
		else
			value = 0;
		document.cookie = key + '=' + value + ';expires=' + expires.toUTCString();
		return true;
	}

	function getCookie(key) {
		var keyValue = document.cookie.match('(^|;) ?' + key + '=([^;]*)(;|$)');
		if (! keyValue)
			return null;
		else
			return keyValue[2];
	}
	function getNumberCookie(key) {
		var keyValue = getCookie(key);
		if (keyValue === null)
			return null;
		else
			return parseFloat(keyValue);
	}
	function setCookie(key, value) {
		var expires = new Date();
		expires.setTime(expires.getTime() + (1 * 24 * 60 * 60 * 1000));
		document.cookie = key + '=' + value + ';expires=' + expires.toUTCString();
		return true;
	}

	// this function refer to the need that the html showed be sorted
	function needAlbumNameSort() {
		var result =
			currentAlbum.subalbums.length &&
			! currentAlbum.albumNameSort &&
			getBooleanCookie("albumNameSortRequested");
		return result;
	}
	function needAlbumDateSort() {
		var result =
			currentAlbum.subalbums.length &&
			currentAlbum.albumNameSort &&
			! getBooleanCookie("albumNameSortRequested");
		return result;
	}
	function needAlbumDateReverseSort() {
		var result =
			currentAlbum.subalbums.length &&
			! currentAlbum.albumNameSort &&
			currentAlbum.albumDateReverseSort !== getBooleanCookie("albumDateReverseSortRequested");
		return result;
	}
	function needAlbumNameReverseSort() {
		var result =
			currentAlbum.subalbums.length &&
			currentAlbum.albumNameSort &&
			currentAlbum.albumNameReverseSort !== getBooleanCookie("albumNameReverseSortRequested");
		return result;
	}

	function needMediaNameSort() {
		var result =
			currentAlbum.media.length &&
			! currentAlbum.mediaNameSort &&
			getBooleanCookie("mediaNameSortRequested");
		return result;
	}
	function needMediaDateSort() {
		var result =
			currentAlbum.media.length &&
			currentAlbum.mediaNameSort &&
			! getBooleanCookie("mediaNameSortRequested");
		return result;
	}
	function needMediaDateReverseSort() {
		var result =
			currentAlbum.media.length &&
			! currentAlbum.mediaNameSort &&
			currentAlbum.mediaDateReverseSort !== getBooleanCookie("mediaDateReverseSortRequested");
		return result;
	}
	function needMediaNameReverseSort() {
		var result =
			currentAlbum.media.length &&
			currentAlbum.mediaNameSort &&
			currentAlbum.mediaNameReverseSort !== getBooleanCookie("mediaNameReverseSortRequested");
		return result;
	}

	/* Error displays */

	function die(error) {
		if (error == 403) {
			$("#auth-text").stop().fadeIn(1000);
			$("#password").focus();
		} else {
			// Jason's code only had the following line
			//$("#error-text").stop().fadeIn(2500);

			var rootLink = "#!/" + Options.folders_string;

			$("#album-view").fadeOut(200);
			$("#media-view").fadeOut(200);

			if (window.location.href == rootLink) {
				$("#loading").hide();
				$("#error-text-folder").stop();
				$("#error-root-folder").stop().fadeIn(2000);
				$("#powered-by").show();
			} else {
				$("#error-text-folder").stop().fadeIn(200);
				$("#error-text-folder, #error-overlay, #auth-text").fadeOut(3500);
				$("#album-view").stop().fadeOut(100).fadeIn(3500);
				$("#media-view").stop().fadeOut(100).fadeIn(3500);
				window.location.href = rootLink;
			}
		}
		// $("#error-overlay").fadeTo(500, 0.8);
		$("body, html").css("overflow", "hidden");
	}

	function undie() {
		$(".error, #error-overlay, #auth-text", ".search-failed").fadeOut(500);
		$("body, html").css("overflow", "auto");
	}



	/* Entry point for most events */

	function hashParsed(album, media, mediaIndex) {
		var populateAlbum;

		undie();
		$("#loading").hide();
		detectSearchSubAlbum();

		$(window).off("resize");

		if (album === currentAlbum && media === currentMedia)
			return;
		if (album != currentAlbum)
			currentAlbum = null;

		previousAlbum = currentAlbum;
		if (currentAlbum && PhotoFloat.isByDateCacheBase(currentAlbum.cacheBase) && media !== null) {
			previousMedia = media;
		}
		else {
			previousMedia = currentMedia;
		}
		currentAlbum = album;
		currentMedia = media;
		currentMediaIndex = mediaIndex;

		setOptions();

		if (currentMedia === null || typeof currentMedia === "object") {
			setTitle();

			initializeSortPropertiesAndCookies();
			$("#menu-icon").attr("title", _t("#menu-icon-title"));
			sortAlbumsMedia();
			updateMenu();
		}

		if (currentMedia !== null || currentAlbum !== null && ! currentAlbum.subalbums.length && currentAlbum.media.length == 1) {
			if (currentMedia === null) {
				currentMedia = currentAlbum.media[0];
				currentMediaIndex = 0;
				$("#next-media").css("cursor", "default");
			} else {
				$("#next-media").css("cursor", "ew-resize");
			}
			nextMedia = null;
			previousMedia = null;
			showMedia(currentAlbum);
		}
		populateAlbum = previousAlbum !== currentAlbum || previousMedia !== currentMedia;
		showAlbum(populateAlbum);
		// options function must be called again in order to set elements previously absent
		setOptions();
		if (currentMedia !== null) {
			// no subalbums, nothing to wait
			// set social buttons events
			if (currentMedia.mediaType == "video")
				$("#media").on("loadstart", socialButtons);
			else
				$("#media").on("load", socialButtons);
		} else  if (
			currentAlbum !== null && ! currentAlbum.subalbums.length ||
			numSubAlbumsReady >= album.subalbums.length
		) {
			// no subalbums
			// set social buttons href's when all the stuff is loaded
			$(window).on("load", socialButtons());
		} else {
			// subalbums are present, we have to wait when all the random thumbnails will be loaded
		}
		fromEscKey = false;

		return;
	}

	function getOptions(callback) {
		if (Object.keys(Options).length > 0)
			callback(location.hash, hashParsed, die);
		else {
			var optionsFile = PhotoFloat.pathJoin(["cache/options.json"]);
			var ajaxOptions = {
				type: "GET",
				dataType: "json",
				url: optionsFile,
				success: function(data) {
					// for map zoom levels, see http://wiki.openstreetmap.org/wiki/Zoom_levels

					for (var key in data)
						if (data.hasOwnProperty(key))
							Options[key] = data[key];
					translate();
					// server_cache_path actually is a constant: it cannot be passed as an option, because getOptions need to know it before reading the options
					// options.json is in this directory
					Options.server_cache_path = 'cache';

					maxSize = Options.reduced_sizes[Options.reduced_sizes.length - 1];

					// override according to user selections
					var slideCookie = getBooleanCookie("albums_slide_style");
					if (slideCookie !== null)
						Options.albums_slide_style = slideCookie;

					if (Options.thumb_spacing)
						Options.spacingToggle = Options.thumb_spacing;
					else
						Options.spacingToggle = Options.media_thumb_size * 0.03;

					var spacingCookie = getNumberCookie("spacing");
					if (spacingCookie !== null) {
						Options.spacing = spacingCookie;
					} else {
						Options.spacing = Options.thumb_spacing;
					}

					var showAlbumNamesCookie = getBooleanCookie("show_album_names_below_thumbs");
					if (showAlbumNamesCookie !== null)
						Options.show_album_names_below_thumbs = showAlbumNamesCookie;

					var showMediaCountCookie = getBooleanCookie("show_album_media_count");
					if (showMediaCountCookie !== null)
						Options.show_album_media_count = showMediaCountCookie;

					var showMediaNamesCookie = getBooleanCookie("show_media_names_below_thumbs");
					if (showMediaNamesCookie !== null)
						Options.show_media_names_below_thumbs = showMediaNamesCookie;

					var squareAlbumsCookie = getCookie("album_thumb_type");
					if (squareAlbumsCookie !== null)
						Options.album_thumb_type = squareAlbumsCookie;

					var squareMediaCookie = getCookie("media_thumb_type");
					if (squareMediaCookie !== null)
						Options.media_thumb_type = squareMediaCookie;

					Options.search_inside_words = false;
					var searchInsideWordsCookie = getBooleanCookie("search_inside_words");
					if (searchInsideWordsCookie !== null)
						Options.search_inside_words = searchInsideWordsCookie;

					Options.search_any_word = false;
					var searchAnyWordCookie = getBooleanCookie("search_any_word");
					if (searchAnyWordCookie !== null)
						Options.search_any_word = searchAnyWordCookie;

					Options.search_case_sensitive = false;
					var searchCaseSensitiveCookie = getBooleanCookie("search_case_sensitive");
					if (searchCaseSensitiveCookie !== null)
						Options.search_case_sensitive = searchCaseSensitiveCookie;

					Options.search_accent_sensitive = false;
					var searchAccentSensitiveCookie = getBooleanCookie("search_accent_sensitive");
					if (searchAccentSensitiveCookie !== null)
						Options.search_accent_sensitive = searchAccentSensitiveCookie;

					Options.search_regex = false;
					var searchRegexCookie = getBooleanCookie("search_regex");
					if (searchRegexCookie !== null)
						Options.search_regex = searchRegexCookie;

					callback(location.hash, hashParsed, die);
				},
				error: function(jqXHR, textStatus, errorThrown) {
					if (errorThrown == "Not Found") {
						$("#album-view").fadeOut(200);
						$("#media-view").fadeOut(200);
						$("#album-view").stop().fadeIn(3500);
						$("#media-view").stop().fadeIn(3500);
						$("#error-options-file").stop().fadeIn(200);
						$("#error-options-file, #error-overlay, #auth-text").fadeOut(2500);
					}
				}
			};
			$.ajax(ajaxOptions);
		}
	}

	// this function is needed in order to let this point to the correct value in photoFloat.parseHash
	function parseHash(hash, callback, error) {
		photoFloat.parseHash(hash, callback, error);
	}

	/* Event listeners */

	$(document).on('keydown', function(e) {
		if (e.target.tagName.toLowerCase() != 'input') {
			if (! e.ctrlKey && ! e.shiftKey && ! e.altKey) {
				if (nextLink && (e.keyCode === 39 || e.keyCode === 78 || e.keyCode === 13 || e.keyCode === 32) && currentMedia !== null) {
					//            arrow right                  n             return              space
					swipeLeft(nextLink);
					return false;
				} else if (prevLink && (e.keyCode === 37 || e.keyCode === 80 || e.keyCode === 8) && currentMedia !== null) {
					//                   arrow left                   p           backspace
					swipeRight(prevLink);
					return false;
				} else if (e.keyCode === 27 && ! Modernizr.fullscreen && fullScreenStatus) {
					//             esc
					goFullscreen(e);
					return false;
				} else if (upLink && (e.keyCode === 27 || e.keyCode === 38 || e.keyCode === 33)) {
					//                            esc            arrow up             page up
					fromEscKey = true;
					swipeDown(upLink);
					return false;
				} else if (mediaLink && currentMedia === null && (e.keyCode === 40 || e.keyCode === 34)) {
					//                                              arrow down           page down
					swipeUp(mediaLink);
					return false;
				} else if (currentMedia !== null && e.keyCode === 68) {
					//                                        d
					$("#download-link")[0].click();
					return false;
				} else if (currentMedia !== null && e.keyCode === 70) {
					//                                        f
					goFullscreen(e);
					return false;
				} else if (currentMedia !== null && e.keyCode === 77) {
					//                                        m
					showMetadata(e);
					return false;
				} else if (currentMedia !== null && e.keyCode === 79) {
					//                                        o
					$("#original-link")[0].click();
					return false;
				} else if (currentMedia !== null && hasGpsData(currentMedia) && e.keyCode === 83) {
					//                                                                    s
						$("#map-link")[0].click();
					return false;
				}
			}

			if (e.keyCode === 69 && ! e.ctrlKey && ! e.shiftKey) {
				//        e, possibly with alt
					$("#menu-icon")[0].click();
				return false;
			}

			return true;
		}
	});
	$("#album-view").on('mousewheel', swipeOnWheel);

	function swipeOnWheel(event, delta) {
		if (currentMedia === null)
			return true;
		if (delta < 0) {
			swipeLeft(nextLink);
			return false;
		} else if (delta > 0) {
			swipeRight(prevLink);
			return false;
		}
		return true;
	}

	$(document).on('load', detectSwipe('media-box-inner',swipe));

	if (isMobile.any()) {
		$("#links").css("display", "inline").css("opacity", 0.5);
	} else {
		//~ $("#media-view").off();
		$("#media-view").on('mouseenter', function() {
			$("#links").stop().fadeTo("slow", 0.50).css("display", "inline");
		});
		$("#media-view").on('mouseleave', function() {
			$("#links").stop().fadeOut("slow");
		});
	}

	$("#next, #prev").on('mouseenter', function() {
		$(this).stop().fadeTo("fast", 1);
	});

	$("#next, #prev").on('mouseleave', function() {
		$(this).stop().fadeTo("fast", 0.4);
	});

	$("#metadata-show").on('click', showMetadataFromMouse);
	$("#metadata-hide").on('click', showMetadataFromMouse);
	$("#metadata").on('click', showMetadataFromMouse);

	$("#fullscreen").on('click', goFullscreenFromMouse);
	$("#next").attr("title", _t("#next-media-title"));
	$("#prev").attr("title", _t("#prev-media-title"));

	function goFullscreen(e) {
		$("#media").off();
		if (Modernizr.fullscreen) {
			e.preventDefault();
			$("#media-box").fullScreen({
				callback: function(isFullscreen) {
					fullScreenStatus = isFullscreen;
					$("#enter-fullscreen").toggle();
					$("#exit-fullscreen").toggle();
					showMedia(currentAlbum);
				}
			});
		} else {
			$("#media").off();
			if (! fullScreenStatus) {
				$("#title-container").hide();
				$("#album-view").hide();
				$("#enter-fullscreen").toggle();
				$("#exit-fullscreen").toggle();
				fullScreenStatus = true;
			} else {
				$("#title-container").show();
				$("#album-view").show();
				$("#enter-fullscreen").toggle();
				$("#exit-fullscreen").toggle();
				fullScreenStatus = false;
			}
			showMedia(currentAlbum);
		}
	}

	function goFullscreenFromMouse(ev) {
		if (ev.which == 1 && ! ev.shiftKey && ! ev.ctrlKey && ! ev.altKey) {
			goFullscreen(ev);
			return false;
		}
	}

	function showMetadataFromMouse(ev) {
		if (ev.which == 1 && ! ev.shiftKey && ! ev.ctrlKey && ! ev.altKey) {
			ev.stopPropagation();
			showMetadata();
			return false;
		}
	}

	function focusSearchField() {
		if (! isMobile.any())
			$("#search-field").focus();
		else
			$("#search-field").blur();
	}

	// binds the click events to the sort buttons

	// search
	$('#search-button').on("click", function() {
		var searchOptions = '';
		// save current hash in order to come back there when exiting from search
		savedLink = location.hash;
		var searchTerms = encodeURIComponent($("#search-field").val().normalize().trim().replace(/  /g, ' ').replace(/ /g, '_'));
		var bySearchViewLinkBase = "#!/" + Options.by_search_string;
		if (searchTerms) {
			var bySearchViewLink = bySearchViewLinkBase + Options.cache_folder_separator;
			if (Options.search_inside_words)
				searchOptions += 'i' + Options.search_options_separator;
			if (Options.search_any_word)
				searchOptions += 'n' + Options.search_options_separator;
			if (Options.search_case_sensitive)
				searchOptions += 'c' + Options.search_options_separator;
			if (Options.search_accent_sensitive)
				searchOptions += 'a' + Options.search_options_separator;
			bySearchViewLink += searchOptions + searchTerms;
			window.location.href = bySearchViewLink;
		} else {
			window.location.href = bySearchViewLinkBase;
		}
		focusSearchField();
		return false;
	});
	$('#search-field').keypress(function(ev) {
		if (ev.which == 13) {
			//Enter key pressed, trigger search button click event
			$('#search-button').click();
			focusSearchField();
			return false;
		}
	});

	$("li#inside-words").on('click', toggleInsideWordsSearch);
	function toggleInsideWordsSearch(ev) {
		Options.search_inside_words = ! Options.search_inside_words;
		setBooleanCookie("search_inside_words", Options.search_inside_words);
		updateMenu();
		if ($("#search-field").val().trim())
			$('#search-button').click();
		focusSearchField();
	}

	$("li#any-word").on('click', toggleAnyWordSearch);
	function toggleAnyWordSearch(ev) {
		Options.search_any_word = ! Options.search_any_word;
		setBooleanCookie("search_any_word", Options.search_any_word);
		updateMenu();
		if ($("#search-field").val().trim())
			$('#search-button').click();
		focusSearchField();
	}

	$("li#case-sensitive").on('click', toggleCaseSensitiveSearch);
	function toggleCaseSensitiveSearch(ev) {
		Options.search_case_sensitive = ! Options.search_case_sensitive;
		setBooleanCookie("search_case_sensitive", Options.search_case_sensitive);
		updateMenu();
		if ($("#search-field").val().trim())
			$('#search-button').click();
		focusSearchField();
	}

	$("li#accent-sensitive").on('click', toggleAccentSensitiveSearch);
	function toggleAccentSensitiveSearch(ev) {
		Options.search_accent_sensitive = ! Options.search_accent_sensitive;
		setBooleanCookie("search_accent_sensitive", Options.search_accent_sensitive);
		updateMenu();
		if ($("#search-field").val().trim())
			$('#search-button').click();
		focusSearchField();
	}

	$("li#regex-word").on('click', toggleRegexSearch);
	function toggleRegexSearch(ev) {
		Options.search_regex = ! Options.search_regex;
		setBooleanCookie("search_regex", Options.search_regex);
		updateMenu();
		if ($("#search-field").val().trim())
			$('#search-button').click();
		focusSearchField();
	}

	// subalbums
	$("li.album-sort.by-date").on('click', sortAlbumsByDate);
	function sortAlbumsByDate(ev) {
		if (currentMedia === null && currentAlbum.subalbums.length > 1 && currentAlbum.albumNameSort && ev.which == 1 && ! ev.shiftKey && ! ev.ctrlKey && ! ev.altKey) {
			setBooleanCookie("albumNameSortRequested", false);
			setBooleanCookie("albumDateReverseSortRequested", currentAlbum.albumNameReverseSort);
			sortAlbumsMedia();
			updateMenu();
			showAlbum("refreshSubalbums");
			focusSearchField();
		}
		return false;
	}

	$("li.album-sort.by-name").on('click', sortAlbumsByName);

	function sortAlbumsByName(ev) {
		if (currentMedia === null && currentAlbum.subalbums.length > 1 && ! currentAlbum.albumNameSort && ev.which == 1 && ! ev.shiftKey && ! ev.ctrlKey && ! ev.altKey) {
			setBooleanCookie("albumNameSortRequested", true);
			setBooleanCookie("albumNameReverseSortRequested", currentAlbum.albumDateReverseSort);
			sortAlbumsMedia();
			updateMenu();
			showAlbum("refreshSubalbums");
			focusSearchField();
		}
		return false;
	}

	$("li.album-sort.sort-reverse").on('click', sortAlbumsReverse);

	function sortAlbumsReverse(ev) {
		if (currentMedia === null && currentAlbum.subalbums.length > 1 && ev.which == 1 && ! ev.shiftKey && ! ev.ctrlKey && ! ev.altKey) {
			if (currentAlbum.albumNameSort)
				setBooleanCookie("albumNameReverseSortRequested", ! currentAlbum.albumNameReverseSort);
			else
				setBooleanCookie("albumDateReverseSortRequested", ! currentAlbum.albumDateReverseSort);
			sortAlbumsMedia();
			updateMenu();
			showAlbum("refreshSubalbums");
			focusSearchField();
		}
		return false;
	}
	// media
	$("li.media-sort.by-date").on('click', sortMediaByDate);

	function sortMediaByDate(ev) {
		if (currentMedia === null && currentAlbum.media.length > 1 && currentAlbum.mediaNameSort && ev.which == 1 && ! ev.shiftKey && ! ev.ctrlKey && ! ev.altKey) {
			setBooleanCookie("mediaNameSortRequested", false);
			setBooleanCookie("mediaDateReverseSortRequested", getBooleanCookie("mediaDateReverseSortRequested"));
			sortAlbumsMedia();
			updateMenu();
			showAlbum("refreshMedia");
			focusSearchField();
		}
		return false;
	}

	$("li.media-sort.by-name").on('click', sortMediaByName);

	function sortMediaByName(ev) {
		if (currentMedia === null && currentAlbum.media.length > 1 && ! currentAlbum.mediaNameSort && ev.which == 1 && ! ev.shiftKey && ! ev.ctrlKey && ! ev.altKey) {
			setBooleanCookie("mediaNameSortRequested", true);
			setBooleanCookie("mediaNameReverseSortRequested", getBooleanCookie("mediaNameReverseSortRequested"));
			sortAlbumsMedia();
			updateMenu();
			showAlbum("refreshMedia");
			focusSearchField();
		}
		return false;
	}

	$("li.media-sort.sort-reverse").on('click', sortMediaReverse);

	function sortMediaReverse(ev) {
		if (currentMedia === null && currentAlbum.media.length > 1 && ev.which == 1 && ! ev.shiftKey && ! ev.ctrlKey && ! ev.altKey) {
			if (currentAlbum.mediaNameSort)
				setBooleanCookie("mediaNameReverseSortRequested", ! getBooleanCookie("mediaNameReverseSortRequested"));
			else
				setBooleanCookie("mediaDateReverseSortRequested", ! getBooleanCookie("mediaDateReverseSortRequested"));

			sortAlbumsMedia();
			updateMenu();
			showAlbum("refreshMedia");
			focusSearchField();
		}
		return false;
	}

	$("ul#right-menu li.slide").on('click', toggleSlideMode);
	function toggleSlideMode(ev) {
		if (currentMedia === null && currentAlbum.subalbums.length && ev.which == 1 && ! ev.shiftKey && ! ev.ctrlKey && ! ev.altKey) {
			Options.albums_slide_style = ! Options.albums_slide_style;
			setBooleanCookie("albums_slide_style", Options.albums_slide_style);
			updateMenu();
			showAlbum("refreshSubalbums");
			focusSearchField();
		}
		return false;
	}

	$("ul#right-menu li.spaced").on('click', toggleSpacing);
	function toggleSpacing(ev) {
		if ((currentAlbum.subalbums.length || currentAlbum.media.length) && ev.which == 1 && ! ev.shiftKey && ! ev.ctrlKey && ! ev.altKey) {
			if (Options.spacing)
				Options.spacing = 0;
			else
				Options.spacing = Options.spacingToggle;
			setCookie("spacing", Options.spacing);
			updateMenu();
			showAlbum("refreshBoth");
			focusSearchField();
		}
		return false;
	}

	$("ul#right-menu li.album-names").on('click', toggleAlbumNames);
	function toggleAlbumNames(ev) {
		if (currentMedia === null && currentAlbum.subalbums.length && ev.which == 1 && ! ev.shiftKey && ! ev.ctrlKey && ! ev.altKey) {
			Options.show_album_names_below_thumbs = ! Options.show_album_names_below_thumbs;
			setBooleanCookie("show_album_names_below_thumbs", Options.show_album_names_below_thumbs);
			updateMenu();
			showAlbum("refreshSubalbums");
			focusSearchField();
		}
		return false;
	}

	$("ul#right-menu li.media-count").on('click', toggleMediaCount);
	function toggleMediaCount(ev) {
		if (currentMedia === null && currentAlbum.subalbums.length && ev.which == 1 && ! ev.shiftKey && ! ev.ctrlKey && ! ev.altKey) {
			Options.show_album_media_count = ! Options.show_album_media_count;
			setBooleanCookie("show_album_media_count", Options.show_album_media_count);
			updateMenu();
			showAlbum("refreshSubalbums");
			focusSearchField();
		}
		return false;
	}

	$("ul#right-menu li.media-names").on('click', toggleMediaNames);
	function toggleMediaNames(ev) {
		if (currentMedia === null && currentAlbum.media.length && ev.which == 1 && ! ev.shiftKey && ! ev.ctrlKey && ! ev.altKey) {
			Options.show_media_names_below_thumbs = ! Options.show_media_names_below_thumbs;
			setBooleanCookie("show_media_names_below_thumbs", Options.show_media_names_below_thumbs);
			updateMenu();
			showAlbum("refreshMedia");
			focusSearchField();
		}
		return false;
	}

	$("ul#right-menu li.square-album-thumbnails").on('click', toggleAlbumsSquare);
	function toggleAlbumsSquare(ev) {
		if (currentMedia === null && ev.which == 1 && ! ev.shiftKey && ! ev.ctrlKey && ! ev.altKey) {
			Options.album_thumb_type = Options.album_thumb_type == "square" ? "fit" : "square";
			setCookie("album_thumb_type", Options.album_thumb_type);
			updateMenu();
			showAlbum("refreshSubalbums");
			focusSearchField();
		}
		return false;
	}

	$("ul#right-menu li.square-media-thumbnails").on('click', toggleMediaSquare);
	function toggleMediaSquare(ev) {
		if (currentMedia === null && ev.which == 1 && ! ev.shiftKey && ! ev.ctrlKey && ! ev.altKey) {
			Options.media_thumb_type = Options.media_thumb_type == "square" ? "fixed_height" : "square";
			setCookie("media_thumb_type", Options.media_thumb_type);
			updateMenu();
			showAlbum("refreshMedia");
			focusSearchField();
		}
		return false;
	}

	function showMetadata() {
		if ($("#metadata").css("display") == "none") {
			$("#metadata-show").hide();
			$("#metadata-hide").show();
			$("#metadata")
				.stop()
				.css("height", 0)
				.css("padding-top", 0)
				.css("padding-bottom", 0)
				.show()
				.stop()
				.animate({ height: $("#metadata > table").height(), paddingTop: 3, paddingBottom: 3 }, "slow", function() {
					$(this).css("height", "auto");
				});
		} else {
			$("#metadata-show").show();
			$("#metadata-hide").hide();
			$("#metadata")
				.stop()
				.animate({ height: 0, paddingTop: 0, paddingBottom: 0 }, "slow", function() {
					$(this).hide();
				});
		}
	}

	function toggleMenu(ev) {
		$("ul#right-menu").toggleClass("expand");
		if ($("ul#right-menu").hasClass("expand"))
			focusSearchField();
		updateMenu();
	}

	$("#menu-icon").on("click", toggleMenu);

	$(window).hashchange(function() {
		$("#loading").show();
		$("#album-view").removeClass("hidden");
		$("link[rel=image_src]").remove();
		$("link[rel=video_src]").remove();
		$("ul#right-menu").removeClass("expand");
		searchCacheBase = '';
		searchSubAlbum = '';
		getOptions(parseHash);
	});
	$(window).hashchange();

	$("#auth-form").submit(function() {
		var password = $("#password");
		password.css("background-color", "rgb(128, 128, 200)");
		photoFloat.authenticate(password.val(), function(success) {
			password.val("");
			if (success) {
				password.css("background-color", "rgb(200, 200, 200)");
				$(window).hashchange();
			} else
				password.css("background-color", "rgb(255, 64, 64)");
		});
		return false;
	});
});
