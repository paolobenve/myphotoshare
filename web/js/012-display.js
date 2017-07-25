var Options = {};
var nextLink = "", prevLink = "";
var language;
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

function getLanguage() {
	language = "en";
	if (Options.language && translations[Options.language] !== undefined)
		language = Options.language;
	else {
		var userLang = navigator.language || navigator.userLanguage || navigator.browserLanguage || navigator.systemLanguage;
		language = userLang.split('-')[0];
	}
	return language;
}

function translate() {
	language = getLanguage();
	var selector;
	for (var key in translations[language]) {
		if (translations[language].hasOwnProperty(key)) {
			if (key == '#title-string' && document.title.substr(0, 5) != "<?php")
				// don't set page title, php has already set it
				continue;
			selector = $(key);
			if (selector.length) {
				selector.html(translations[language][key]);
			}
		}
	}
}

function _t(id) {
	language = getLanguage();
	return translations[language][id];
}

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
	var byDateRegex;
	var numSubAlbumsReady = 0;
	
	if (! isMobile.any())
		$(".ssk-whatsapp").hide();
	
	/* Displays */
	
	// adapted from https://stackoverflow.com/questions/15084675/how-to-implement-swipe-gestures-for-mobile-devices#answer-27115070
	function detectSwipe(el,callback) {
		var swipe_det, ele, min_x, direc;
		var touchStart, touchMove, touchEnd;
		touchStart = function(e){
			var t = e.touches[0];
			swipe_det.sX = t.screenX;
		};
		touchMove = function(e){
			e.preventDefault();
			var t = e.touches[0];
			swipe_det.eX = t.screenX;
		};
		touchEnd = function(e){
			if ((swipe_det.eX - swipe_det.sX > min_x || swipe_det.eX - swipe_det.sX < - min_x) && 
				swipe_det.eX > 0
			) {
				if(swipe_det.eX > swipe_det.sX)
					direc = "r";
				else
					direc = "l";
			}
			
			if (direc != "") {
				if(typeof callback == 'function')
					callback(el,direc);
			}
			direc = "";
			swipe_det.sX = 0; swipe_det.eX = 0;
		};
		swipe_det = new Object();
		swipe_det.sX = 0; swipe_det.eX = 0;
		min_x = 30;  //min x swipe for horizontal swipe
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
		}
	}
	
	function swipeRight(dest) {
		if (dest) {
			$("#media-box-inner").stop().animate({
				right: "-=" + window.innerWidth,
			}, 300, function() {
				location.href = dest;
				$("#media-box-inner").css('right', "");
			});
		}
	}
	function swipeLeft(dest) {
		if (dest) {
			$("#media-box-inner").stop().animate({
				left: "-=" + window.innerWidth,
			}, 300, function() {
				location.href = dest;
				$("#media-box-inner").css('left', "");
			});
		}
	}
	
	function socialButtons() {
		var url, hash, myShareUrl = "";
		var type, mediaArray = [], allThumbnails = [], src, re, position, randomIndex;
		var i, iCorrected, folders, myShareText, myShareTextAdd, maxThumbnailNumber;
		url = location.protocol + "//" + location.host;
		folders = location.pathname;
		folders = folders.substring(0, folders.lastIndexOf('/'));
		url += folders;
		if (currentMedia === null) {
			// album: prepare the thumbnail names, they will be passed to php code for generating a n-thumbnail image
			type = "a";
			re = new  RegExp("_(" + Options.album_thumb_size.toString() + "a(s|f)\\.jpg|" +
				Options.media_thumb_size.toString() + "t(s|f)\\.jpg)$");
			// recollect all the thumbnails showed in page
			$(".thumbnail").each(function() {
				src = $(this).attr("src");
				position = src.search(re);
				src = src.substring(0, position + 1) + Options.album_thumb_size.toString() + "as.jpg";
				src = src.substring(Options.server_cache_path.length);
				if (allThumbnails.indexOf(src) == -1)
					allThumbnails.push(src);
			});
			
			if (allThumbnails.length < 9 || Options.max_album_share_thumbnails_number == 4)
				maxThumbnailNumber = 4;
			else if (allThumbnails.length < 16 || Options.max_album_share_thumbnails_number == 9)
				maxThumbnailNumber = 9;
			else if (allThumbnails.length < 25 || Options.max_album_share_thumbnails_number == 16)
				maxThumbnailNumber = 16;
			else if (allThumbnails.length < 36 || Options.max_album_share_thumbnails_number == 25)
				maxThumbnailNumber = 25;
			else
				maxThumbnailNumber = Options.max_album_share_thumbnails_number;
			// maxThumbnailNumber random thumbnail will be passed to php as url parameters
			if (allThumbnails.length <= maxThumbnailNumber) {
				// add the thumbnails (repeating them) until length is maxThumbnailNumber
				iCorrected = 0;
				for (i = 0; i < maxThumbnailNumber; i ++) {
					mediaArray.push(allThumbnails[iCorrected]);
					iCorrected ++;
					if (iCorrected == allThumbnails.length)
						iCorrected = 0;
				}
			} else if (allThumbnails.length > maxThumbnailNumber) {
				for (i = 0; i < allThumbnails.length * 5; i ++) {
					// 0 <= random index < allThumbnails.length
					randomIndex = Math.floor(Math.random() * (allThumbnails.length - 1)) + 1;
					if (mediaArray.indexOf(allThumbnails[randomIndex]) == -1)
						mediaArray.push(allThumbnails[randomIndex]);
					if (mediaArray.length == maxThumbnailNumber)
						break;
				}
			}
		} else {
			mediaArray.push($("#media").attr("src"));
			if (currentMedia.mediaType == "video") {
				type = "v";
			} else if (currentMedia.mediaType == "photo") {
				type = "p";
			}
		}
		
		hash = location.hash;
		myShareUrl = url + '?';
		for (i = 0; i < mediaArray.length; i ++)
			myShareUrl += 's' + i + '=' + encodeURIComponent(mediaArray[i]) + '&';
		myShareUrl += 't=' + type + '#' + hash.substring(1);
		
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
			//~ selector: '.custom-parent .ssk',
			//~ url: myShareUrl,
			//~ text: myShareText,
			//~ twitter: {
				//~ url: location.href,
				//~ text: myShareText,
				//~ via: 'twitter-screen-name',
				//~ countCallback: function(shareUrl, onCountReady) {
					//~ // Get count somewhere manually and call onCountReady() whenever you got the count.
					//~ var count = 5;
					//~ return onCountReady(count);
				//~ }
			//~ }
		});
	}
	
	
	function setTitle() {
		var title = "", documentTitle = "", last = "", components, i, dateTitle, originalTitle;
		var titleAnchorClasses, hiddenTitle = "", beginLink, linksToLeave, numLinks;
		if (Options.page_title !== "")
			originalTitle = Options.page_title;
		else
			originalTitle = translations[language]["#title-string"];
		
		if (! PhotoFloat.firstAlbumPopulation || getBooleanCookie("albumReverseSortRequested") || getBooleanCookie("mediaReverseSortRequested")) {
			if (PhotoFloat.firstAlbumPopulation)
				PhotoFloat.firstAlbumPopulation = false;
			if (needMediaHtmlReverse()) {
				currentAlbum.media = currentAlbum.media.reverse();
				if (currentMediaIndex !== undefined && currentMediaIndex != -1)
					currentMediaIndex = currentAlbum.media.length - 1 - currentMediaIndex;
			}
			if (needAlbumHtmlReverse())
				currentAlbum.albums = currentAlbum.albums.reverse();
		}

		if (! currentAlbum.path.length)
			components = [originalTitle];
		else {
			components = currentAlbum.path.split("/");
			components.unshift(originalTitle);
		}
		
		dateTitle = components.length > 1 && components[1] == Options.by_date_string;
		// textComponents = components doesn't work: textComponents becomes a pointer to components
		var textComponents = [];
		for (i = 0; i < components.length; ++i)
			textComponents[i] = components[i];
		if (dateTitle) {
			if (components.length >= 4) {
				textComponents[3] = components[3].replace(components[2], '').trim();
				if (components.length >= 5) {
					textComponents[4] = components[4].replace(textComponents[3], '').replace(textComponents[2], '').trim();
				}
			}
		}
		// generate the title in the page
		titleAnchorClasses = 'title-anchor';
		if (isMobile.any())
			titleAnchorClasses += ' mobile';
		for (i = 0; i < components.length; ++i) {
			if (i)
				last += "/" + components[i];
			if (i != 1 || components[i] != Options.folders_string) {
				if (i < components.length - 1 || currentMedia !== null)
					if (i != 0 || ! dateTitle) {
						if (i == 1 && dateTitle)
							title = "<a class='" + titleAnchorClasses + "' href=\"#!/" + photoFloat.cachePath(last.substring(1)) + "\">" + title;
						else
							title += "<a class='" + titleAnchorClasses + "' href=\"#!/" + (i ? photoFloat.cachePath(last.substring(1)) : "") + "\">";
					}
				if (i == 1 && dateTitle)
					title += "(" + _t("#by-date") + ")";
				else
					title += textComponents[i];
				if (i < components.length - 1 || currentMedia !== null)
					if (! (i == 0 && dateTitle))
						title += "</a>";
			}
			if (i == 0 && dateTitle)
				title += " ";
			else if ((i < components.length - 1 || currentMedia !== null) &&
				(i == components.length - 1 || components[i + 1] != Options.folders_string))
				title += " &raquo; ";
		}
		
		// leave only the last link on mobile, the last two otherwise
		linksToLeave = 2;
		if (isMobile.any())
			linksToLeave = 1;
		numLinks = title.split("<a ").length - 1;
		if (numLinks > linksToLeave) {
			for (i = 1; i <= numLinks - linksToLeave; i ++) {
				beginLink = title.indexOf("<a class=", 3);
				hiddenTitle += title.substring(0, beginLink);
				title = title.substring(beginLink);
			}
			title = "<a id=\"dots\" href=\"javascript:void(0)\">... &raquo; </a><span id=\"hidden-title\">" + hiddenTitle + "</span> " + title;
		}
		
		if (currentMedia !== null)
			title += "<span id=\"media-name\">" + photoFloat.trimExtension(currentMedia.name) + "</span>";
			
		else if (currentMedia !== null || currentAlbum !== null && ! currentAlbum.albums.length && currentAlbum.media.length == 1)
			title += " &raquo; <span id=\"media-name\">" + photoFloat.trimExtension(currentAlbum.media[0].name) + "</span>";
		else {
			// the arrows for changing sort
			if (currentAlbum.albums.length > 1)
				title += "<a id=\"album-sort-arrows\" class=\"arrows\" href=\"javascript:void(0)\">" +
						"<img id=\"album-sort-reverse\" title=\"" + _t("#album-sort-reverse") + "\" height=\"15px\" src=\"img/Folder_sort_reverse.png\">" +
						"<img id=\"album-sort-normal\" title=\"" + _t("#album-sort-normal") + "\" height=\"15px\" src=\"img/Folder_sort_normal.png\">" +
					"</a>";
			if (currentAlbum.media.length > 1)
				title += "<a id=\"media-sort-arrows\" class=\"arrows\" href=\"javascript:void(0)\">" +
						"<img id=\"media-sort-reverse\" title=\"" + _t("#media-sort-reverse") + "\" height=\"15px\" src=\"img/People_sort_reverse.png\">" +
						"<img id=\"media-sort-normal\" title=\"" + _t("#media-sort-normal") + "\" height=\"15px\" src=\"img/People_sort_normal.png\">" +
					"</a>";
		}
		
		document.title = documentTitle;
		$("#title-string").html(title);
		
		$("#dots").off("click");
		$("#dots").click(function() {
			$("#dots").hide();
			$("#hidden-title").show();
			return false;
		});

		// generate the html page title
		for (i = 0; i < components.length; ++i) {
			if (i == 0) {
				documentTitle += components[0];
				if (components.length > 2 || currentMedia !== null)
					documentTitle = " \u00ab " + documentTitle;
			}
			else if (i == 1 && dateTitle) {
				documentTitle += " (" + _t("#by-date") + ")";
			}
			else if (i > 1) {
				documentTitle = textComponents[i] + documentTitle;
				if (i < components.length - 1 || currentMedia !== null)
					documentTitle = " \u00ab " + documentTitle;
			}
		}
		if (currentMedia !== null)
			documentTitle = photoFloat.trimExtension(currentMedia.name) + documentTitle;
		else if (currentMedia !== null || currentAlbum !== null && ! currentAlbum.albums.length && currentAlbum.media.length == 1)
			documentTitle =  photoFloat.trimExtension(currentAlbum.media[0].name) + " \u00ab " + documentTitle;
		
		if (currentMedia === null) {
			if (getBooleanCookie("albumReverseSortRequested")) {
				$("#album-sort-reverse").hide();
				$("#album-sort-normal").show();
			} else {
				$("#album-sort-reverse").show();
				$("#album-sort-normal").hide();
			}
			if (isMobile.any()) {
				$(".arrows").css("padding", "0 .5em").css("display", "inline");
			} else {
				$("body").off('mouseenter');
				$("body").off('mouseleave');
				$("body").on('mouseenter', "#title-container", function() {
					if (currentAlbum.albums.length > 1) {
						$("#album-sort-arrows").show();
					}
					if (currentAlbum.media.length > 1 && ! (currentAlbum.path.match(byDateRegex) && currentAlbum.media.length >= Options.big_date_folders_threshold)) {
						$("#media-sort-arrows").show();
					}
				});
				$("body").on('mouseleave', "#title-container", function() {
					$("#album-sort-arrows").hide();
					$("#media-sort-arrows").hide();
				});
			}
			$("#title").unbind('click');
			if (currentAlbum.albums.length > 1) {
				$("#title").on('click', "#album-sort-arrows", function() {
					currentAlbum.albums = currentAlbum.albums.reverse();
					
					if (getBooleanCookie("albumReverseSortRequested")) {
						setBooleanCookie("albumReverseSortRequested", false);
						$("#album-sort-reverse").show();
						$("#album-sort-normal").hide();
					} else {
						setBooleanCookie("albumReverseSortRequested", true);
						$("#album-sort-reverse").hide();
						$("#album-sort-normal").show();
					}
					showAlbum("conditional");
				});
			}
			if (currentAlbum.media.length > 1) {
				$("#title").on('click', "#media-sort-arrows", function() {
					if (currentMedia !== null)
						currentMediaIndex = currentAlbum.media.length - 1 - currentMediaIndex;
					currentAlbum.media = currentAlbum.media.reverse();
					
					if (getBooleanCookie("mediaReverseSortRequested")) {
						setBooleanCookie("mediaReverseSortRequested", false);
						$("#media-sort-reverse").show();
						$("#media-sort-normal").hide();
					} else {
						setBooleanCookie("mediaReverseSortRequested", true);
						$("#media-sort-reverse").hide();
						$("#media-sort-normal").show();
					}
					showAlbum("conditional");
					});
			}
			setOptions();
		}
		if (getBooleanCookie("albumReverseSortRequested")) {
			$("#album-sort-reverse").hide();
			$("#album-sort-normal").show();
		} else {
			$("#album-sort-reverse").show();
			$("#album-sort-normal").hide();
		}
		if (getBooleanCookie("mediaReverseSortRequested")) {
			$("#media-sort-reverse").hide();
			$("#media-sort-normal").show();
		} else {
			$("#media-sort-reverse").show();
			$("#media-sort-normal").hide();
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
		$("#thumbs img").each(function() {
			if (this.title === media.name) {
				thumb = $(this);
				return false;
			}
		});
		if (typeof thumb === "undefined")
			return;
		if (currentMedia !== null) {
			var scroller = $("#album-view");
			scroller.stop().animate(
				{ scrollLeft: thumb.parent().position().left + scroller.scrollLeft() - scroller.width() / 2 + thumb.width() / 2 },
				"slow"
			);
		} else
			$("html, body").stop().animate({ scrollTop: thumb.offset().top - $(window).height() / 2 + thumb.height() }, "slow");
		
		if (currentMedia !== null) {
			$("#thumbs img").removeClass("current-thumb");
			thumb.addClass("current-thumb");
		}
	}
	
	function albumButtonWidth(thumbnailWidth) {
		if (Options.albums_slide_style)
			return Math.round(thumbnailWidth * 1.1);
		else
			return thumbnailWidth;
	}
	
	function showAlbum(populate) {
		var i, link, image, media, thumbsElement, subalbums, subalbumsElement, hash, thumbHash, thumbnailSize;
		var width, height, thumbWidth, thumbHeight, imageString, calculatedWidth, bydateStringWithTrailingSeparator, populateMedia;
		var albumViewWidth, calculatedAlbumThumbSize = Options.album_thumb_size;
		var mediaWidth, mediaHeight, isOriginal;
		
		if (currentMedia === null && previousMedia === null)
			$("html, body").stop().animate({ scrollTop: 0 }, "slow");
		if (populate) {
			thumbnailSize = Options.media_thumb_size;
			
			populateMedia = populate;
			if (populateMedia === true && ! ! currentAlbum.path.match(byDateRegex))
				populateMedia = populateMedia && (currentAlbum.media.length < Options.big_date_folders_threshold);
			
			if (populateMedia === true || populateMedia && needMediaHtmlReverse()) {
				media = [];
				for (i = 0; i < currentAlbum.media.length; ++i) {
					width = currentAlbum.media[i].metadata.size[0];
					height = currentAlbum.media[i].metadata.size[1];
					[thumbHash, isOriginal] = chooseThumbnail(currentAlbum, currentAlbum.media[i], thumbnailSize, thumbnailSize);
					bydateStringWithTrailingSeparator = Options.by_date_string + Options.cache_folder_separator;
					if (thumbHash.indexOf(bydateStringWithTrailingSeparator) === 0) {
						currentAlbum.media[i].completeName =
							currentAlbum.media[i].foldersAlbum + '/' + currentAlbum.media[i].name;
						thumbHash =
							PhotoFloat.cachePath(currentAlbum.media[i].completeName
								.substring(0, currentAlbum.media[i].completeName.length - currentAlbum.media[i].name.length - 1)) +
							"/" +
							PhotoFloat.cachePath(currentAlbum.media[i].name);
					}
					if (isOriginal) {
						thumbHeight = width;
						thumbWidth = height;
					} else {
						if (Options.media_thumb_type == "fixed_height") {
							thumbHeight = Options.media_thumb_size;
							thumbWidth = thumbHeight * width / height;
							calculatedWidth = thumbWidth.toString();
						} else {
							thumbHeight = thumbnailSize;
							thumbWidth = thumbnailSize;
							calculatedWidth = Options.media_thumb_size.toString().toString();
						}
					}
					imageString = "<div class=\"thumb-container\" ";
					imageString += "style=\"width: " + calculatedWidth + "px;\">";
					imageString += 		"<span class=\"helper\"></span>";
					imageString += 		"<img title=\"" + currentAlbum.media[i].name +
								"\" alt=\"" + photoFloat.trimExtension(currentAlbum.media[i].name) +
								"\" src=\"" +  thumbHash +
								"\" class=\"thumbnail" +
								"\" height=\"" + thumbHeight +
								"\" width=\"" + thumbWidth +
								"\" />" +
								"<div class=\"media-caption\">" +
								currentAlbum.media[i].name.replace(/ /g, "</span> <span style=\"white-space: nowrap;\">") +
								"</div>" +
								"</div>";
					image = $(imageString);
					
					image.get(0).media = currentAlbum.media[i];
					hash = photoFloat.mediaHash(currentAlbum, currentAlbum.media[i]);
					link = $("<a href=\"#!/" + hash + "\"></a>");
					link.append(image);
					media.push(link);
					(function(theLink, theImage, theAlbum) {
						theImage.error(function() {
							media.splice(media.indexOf(theLink), 1);
							theLink.remove();
							theAlbum.media.splice(theAlbum.media.indexOf(theImage.get(0).media), 1);
						});
					})(link, image, currentAlbum);
				}
				
				thumbsElement = $("#thumbs");
				thumbsElement.empty();
				thumbsElement.append.apply(thumbsElement, media);
				
				if (needMediaHtmlReverse())
					currentAlbum.mediaReverseSort = ! currentAlbum.mediaReverseSort;
			} else if (currentAlbum.media.length < Options.big_date_folders_threshold) {
				$("#thumbs").html("<span id=\"too-many-images\">Too many images: " + currentAlbum.media.length + " (limit for date album is " + Options.big_date_folders_threshold +  ")</span>");
				$("#thumbs").empty();
			}
			
			if (currentMedia === null) {
				if (populate === true || populate && needAlbumHtmlReverse()) {
					subalbums = [];
					
					// resize down the album buttons if they are too wide
					albumViewWidth = $("body").width() -
							parseInt($("#album-view").css("padding-left")) -
							parseInt($("#album-view").css("padding-right")) -
							15; // the trailing subtraction is for the scroll slide
					if (albumButtonWidth(calculatedAlbumThumbSize) > albumViewWidth / Options.min_album_thumbnail) {
						calculatedAlbumThumbSize =
							Math.floor(albumViewWidth / Options.min_album_thumbnail - Options.thumb_spacing - 6);
						if (Options.albums_slide_style)
							calculatedAlbumThumbSize = Math.floor(calculatedAlbumThumbSize / 1.1);
					}
					
					
					for (i = 0; i < currentAlbum.albums.length; ++i) {
						link = $("<a href=\"#!/" + photoFloat.albumHash(currentAlbum.albums[i]) + "\"></a>");
						imageString = "<div class=\"album-button\"";
						imageString += 		" style=\"";
						//~ imageString += 			"width: " + (calculatedAlbumThumbSize + 6) + "px;";
						//~ imageString += 			" height: " + (calculatedAlbumThumbSize + 6) + "px;";
						imageString += 			"width: " + (calculatedAlbumThumbSize + 2) + "px;";
						imageString += 			" height: " + (calculatedAlbumThumbSize + 2) + "px;";
						if (! Options.albums_slide_style)
							imageString +=		" background-color: " + Options.album_button_background_color + ";";
						imageString += 			"\"";
						imageString += ">";
						imageString += "</div>";
						image = $(imageString);
						link.append(image);
						subalbums.push(link);
						(function(theContainer, theAlbum, theImage, theLink) {
							photoFloat.pickRandomMedia(theAlbum, theContainer, function(randomAlbum, randomMedia, originalAlbum) {
								var distance = 0;
								var htmlText, isOriginal;
								var folderArray, originalAlbumFoldersArray, folder, captionHeight, buttonAndCaptionHeight, html;
								
								[mediaSrc, isOriginal] = chooseThumbnail(randomAlbum, randomMedia, Options.album_thumb_size, calculatedAlbumThumbSize);
								if (isOriginal) {
									thumbWidth = randomMedia.metadata.size[0];
									thumbHeight = randomMedia.metadata.size[1];
								} else {
									if (Options.album_thumb_type == "fit") {
										mediaWidth = randomMedia.metadata.size[0];
										mediaHeight = randomMedia.metadata.size[1];
										if (mediaWidth > mediaHeight) {
											thumbWidth = calculatedAlbumThumbSize;
											thumbHeight = calculatedAlbumThumbSize * mediaHeight / mediaWidth;
										} else {
											thumbWidth = calculatedAlbumThumbSize * mediaWidth / mediaHeight;
											thumbHeight = calculatedAlbumThumbSize;
										}
										distance = (calculatedAlbumThumbSize - thumbHeight) / 2;
									}
								}
								//~ mediaSrc = photoFloat.mediaPath(randomAlbum, randomMedia, Options.album_thumb_size);
								htmlText = "<span class=\"helper\"></span>" +
										"<img " +
											"title=\"" + randomMedia.albumName + "\"" +
											" class=\"thumbnail\"" +
											" src=\"" + mediaSrc + "\"" +
											" style=\"width:" + thumbWidth + "px;" +
												" height:" + thumbHeight + "px;" +
												" margin-top: " + distance + "px" +
												"\"" +
										">";
								theImage.html(htmlText);
								
								if (originalAlbum.path.indexOf(Options.by_date_string) === 0)
									folderArray = randomMedia.dayAlbum.split("/");
								else
									folderArray = randomMedia.albumName.split("/");
								originalAlbumFoldersArray = originalAlbum.path.split("/");
								folder = folderArray[originalAlbumFoldersArray.length];
								
								// get the value in style sheet (element with that class doesn't exist in DOM
								var $el = $('<div class="album-caption"></div>');
								$($el).appendTo('body');
								var paddingTop = parseInt($($el).css('padding-top'));
								$($el).remove();
								
								captionHeight = em2px("body", 3) * calculatedAlbumThumbSize / Options.album_thumb_size;
								buttonAndCaptionHeight = calculatedAlbumThumbSize + captionHeight + paddingTop + 3 * 4;
								html = "<div class=\"album-button-and-caption";
								if (Options.albums_slide_style)
									html += " slide";
								html += "\"";
								html += "style=\"";
								html += 	"height: " + buttonAndCaptionHeight.toString() + "px; " +
										"margin-right: " + Options.thumb_spacing + "px; ";
								html += "width: " + albumButtonWidth(calculatedAlbumThumbSize).toString() + "px; ";
								html += "padding-top: " + Math.round(calculatedAlbumThumbSize * 0.05).toString() + "px; ";
								if (Options.albums_slide_style)
									html += "background-color: " + Options.album_button_background_color + "; ";
								html += "\"";
								html += ">";
								theImage.wrap(html);
								html = "<div class=\"album-caption\"";
								html += " style=\"width: " + calculatedAlbumThumbSize.toString() + "px; " +
										"font-size: " + (captionHeight / 3).toString() + "px; " +
										"height: " + captionHeight.toString() + "px; ";
								html += 	"color: " + Options.album_caption_color + "; ";
								html += "\"";
								html += ">" + folder + "</div>";
								theImage.parent().append(html);
								// this function must be called every time a album slide is created,
								// in order to include this images in the composite php will create
								numSubAlbumsReady ++;
								if (numSubAlbumsReady == originalAlbum.albums.length) {
									// only run the function when all the album has loaded their random image
									socialButtons();
								}
							}, function error() {
								theContainer.albums.splice(currentAlbum.albums.indexOf(theAlbum), 1);
								theLink.remove();
								subalbums.splice(subalbums.indexOf(theLink), 1);
							});
							i++;i--;
						})(currentAlbum, currentAlbum.albums[i], image, link);
						
					}
					
					subalbumsElement = $("#subalbums");
					subalbumsElement.empty();
					subalbumsElement.append.apply(subalbumsElement, subalbums);
					subalbumsElement.insertBefore(thumbsElement);
					
					if (needAlbumHtmlReverse())
						currentAlbum.albumReverseSort = ! currentAlbum.albumReverseSort;
				}
			}
			
		}
		
		if (currentMedia === null) {
			$("#thumbs img").removeClass("current-thumb");
			$("#album-view").removeClass("media-view-container");
			$("#subalbums").show();
			$("#media-view").hide();
			$("#media-view").removeClass("no-bottom-space");
			$("#album-view").removeClass("no-bottom-space");
			$("#media-box-inner").empty();
			$("#media-box").hide();
			$("#thumbs").show();
			$("#day-folders-view-container").show();
			if (currentAlbum.path == Options.folders_string) {
				$("#folders-view").hide();
				$("#date-view").show();
				$("#day-folders-view-link").attr("href", "#!/" + Options.by_date_string);
			}
			else if (currentAlbum.path == Options.by_date_string) {
				$("#folders-view").show();
				$("#date-view").hide();
				$("#day-folders-view-link").attr("href", "#!/" + Options.folders_string);
			} else {
				$("#folders-view").hide();
				$("#date-view").hide();
			}
			$("#powered-by").show();
		} else {
			if (currentAlbum.media.length == 1)
				$("#thumbs").hide();
			else
				$("#thumbs").show();
			$("#powered-by").hide();
		}
		setTimeout(scrollToThumb, 1);
	}
	function getDecimal(fraction) {
		if (fraction[0] < fraction[1])
			return fraction[0] + "/" + fraction[1];
		return (fraction[0] / fraction[1]).toString();
	}
	
	function lateralSocialButtons() {
		return $(".ssk-group").css("display") == "block";
	}
	function bottomSocialButtons() {
		return ! lateralSocialButtons();
	}
	function scaleMedia() {
		var media, container, containerBottom = 0, containerTop = 0, containerRatio, ratio, photoSrc, previousSrc;
		var containerHeight = $(window).innerHeight(), containerWidth = $(window).innerWidth(), mediaBarBottom = 0;
		var width = currentMedia.metadata.size[0], height = currentMedia.metadata.size[1],ratio = width / height;
		
		$(window).off("resize");
		
		if (fullScreenStatus)
			container = $(window);
		else {
			container = $("#media-view");
			if ($("#thumbs").is(":visible"))
				containerBottom = $("#album-view").outerHeight();
			else if (bottomSocialButtons() && containerBottom < $(".ssk").outerHeight())
				// correct container bottom when social buttons are on the bottom
				containerBottom = $(".ssk").outerHeight();
			containerTop = $("#title-container").outerHeight();
			containerHeight -= containerBottom + $("#title-container").outerHeight();
			container.css("top", containerTop + "px");
			container.css("bottom", containerBottom + "px");
		}
		
		containerRatio = containerWidth / containerHeight;
		
		media = $("#media");
		media.off('loadstart').off("load");
		
		if (currentMedia.mediaType == "photo") {
			photoSrc = chooseReducedPhoto(container);
			previousSrc = media.attr("src");
			if (! imageExists(photoSrc)) {
				photoSrc = photoFloat.originalMediaPath(currentMedia);
			} else {
				// chooseReducedPhoto() sets maxSize to 0 if it returns the original media
				if (maxSize) {
					if (width > height) {
						height = Math.round(height * maxSize / width);
						width = maxSize;
					} else {
						width = Math.round(width * maxSize / height);
						height = maxSize;
					}
				}
			}
			if (photoSrc != previousSrc || media.attr("width") != width || media.attr("height") != height) {
				$("link[rel=image_src]").remove();
				$('link[rel="video_src"]').remove();
				$("head").append("<link rel=\"image_src\" href=\"" + photoSrc + "\" />");
				media
					.attr("src", photoSrc)
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
		
		$("#media-bar").css("bottom", mediaBarBottom + "px");
		
		media.show();
		
		if (! fullScreenStatus && currentAlbum.media.length > 1 && lateralSocialButtons()) {
			// correct back arrow position when social buttons are on the left
			$("#prev").css("left", "");
			$("#prev").css("left", (parseInt($("#prev").css("left")) + $(".ssk").outerWidth()) + "px");
		}
		
		$(window).bind("resize", scaleMedia);
	}
	function chooseReducedPhoto(container) {
		var chosenMedia, reducedWidth, reducedHeight;
		var mediaWidth = currentMedia.metadata.size[0], mediaHeight = currentMedia.metadata.size[1];
		var mediaSize = Math.max(mediaWidth, mediaHeight);
		chosenMedia = PhotoFloat.originalMediaPath(currentMedia);
		maxSize = 0;
		for (var i = 0; i < Options.reduced_sizes.length; i++) {
			if (Options.reduced_sizes[i] > mediaSize)
				continue;
			if (container !== null) {
				if (mediaWidth > mediaHeight) {
					reducedWidth = Options.reduced_sizes[i];
					reducedHeight = Options.reduced_sizes[i] * mediaHeight / mediaWidth;
				} else {
					reducedHeight = Options.reduced_sizes[i];
					reducedWidth = Options.reduced_sizes[i] * mediaWidth / mediaHeight;
				}
				
				if (reducedWidth < container.width() && reducedHeight < container.height())
					break;
			}
			chosenMedia = photoFloat.mediaPath(currentAlbum, currentMedia, Options.reduced_sizes[i]);
			maxSize = Options.reduced_sizes[i];
			if (container === null)
				break;
		}
		return chosenMedia;
	}
	function chooseThumbnail(album, media, thumbnailSize, calculatedThumbnailSize) {
		var chosenMedia = PhotoFloat.originalMediaPath(media);
		var mediaWidth = media.metadata.size[0], mediaHeight = media.metadata.size[1];
		var mediaMaxSize = Math.max(mediaWidth, mediaHeight);
		var mediaMinSize = Math.min(mediaWidth, mediaHeight);
		var isOriginal = true;
		
		if (
			Options.album_thumb_type == "square" && mediaMinSize > calculatedThumbnailSize ||
			Options.album_thumb_type == "fit" && mediaMaxSize > calculatedThumbnailSize ||
			Options.album_thumb_type == "fixed_height" && mediaHeight > calculatedThumbnailSize
		) {
			chosenMedia = photoFloat.mediaPath(album, media, thumbnailSize);
			isOriginal = false;
		}
		
		return [chosenMedia, isOriginal];
	}
	
	function imageExists(imageUrl){
		var http = new XMLHttpRequest();
		http.open('HEAD', imageUrl, false);
		http.send();
		return http.status != 404;
	}
	
	function showMedia(album) {
		var width = currentMedia.metadata.size[0], height = currentMedia.metadata.size[1];
		var previousMedia, nextMedia, text, thumbnailSize, i, changeViewLink, linkTag, triggerLoad, videoOK = true;
		var windowWidth = $(window).width(), windowHeight = $(window).height();
		
		thumbnailSize = Options.media_thumb_size;
		$("#media-box").show();
		if (currentAlbum.media.length == 1) {
			$("#next").hide();
			$("#prev").hide();
			$(".next-media").removeAttr("href");
			$("#next").removeAttr("href");
			$("#prev").removeAttr("href");
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
				$('<div id="video-unsupported">' +
						'<p>Sorry, your browser doesn\'t support the HTML5 &lt;video&gt; element!</p>' +
						'<p>Here\'s a <a href="http://caniuse.com/video">list of which browsers do</a>.</p>' +
					'</div>').appendTo('#media-box-inner');
				videoOK = false;
			}
			else if (! Modernizr.video.h264) {
				$('<div id="video-unsupported">' +
						'<p>Sorry, your browser doesn\'t support the H.264 video format!</p>' +
					'</div>').appendTo('#media-box-inner');
				videoOK = false;
			}
		}
		
		if (currentMedia.mediaType == "photo" || currentMedia.mediaType == "video" && videoOK) {
			if (currentAlbum.path == currentMedia.foldersAlbum) {
				$("#folders-view").hide();
				$("#date-view").show();
			}
			else {
				$("#folders-view").show();
				$("#date-view").hide();
			}
			
			if (currentMedia.mediaType == "video") {
				if (fullScreenStatus) {
					////////////////////////////////////////////
					// the original video doesn't work: WHY????
					// videoSrc = currentMedia.albumName;
					////////////////////////////////////////////
					videoSrc = photoFloat.mediaPath(currentAlbum, currentMedia, "");
				} else {
					videoSrc = photoFloat.mediaPath(currentAlbum, currentMedia, "");
				}
				$('<video/>', { id: 'media', controls: true })
					.appendTo('#media-box-inner')
					.attr("width", width)
					.attr("height", height)
					.attr("ratio", width / height)
					.attr("src", videoSrc)
					.attr("alt", currentMedia.name);
				triggerLoad = 'loadstart';
				linkTag = "<link rel=\"video_src\" href=\"" + videoSrc + "\" />";
			} else if (currentMedia.mediaType == "photo") {
				photoSrc = chooseReducedPhoto(null);
				if (maxSize && imageExists(photoSrc)) {
					if (width > height) {
						height = Math.round(height * maxSize / width);
						width = maxSize;
					} else {
						width = Math.round(width * maxSize / height);
						height = maxSize;
					}
				} else {
					photoSrc = photoFloat.originalMediaPath(currentMedia);
				}
				$('<img/>', { id: 'media' })
					.appendTo('#media-box-inner')
					.hide()
					.attr("width", width)
					.attr("height", height)
					.attr("ratio", width / height)
					.attr("src", photoSrc)
					.attr("alt", currentMedia.name)
					.attr("title", currentMedia.date);
				linkTag = "<link rel=\"image_src\" href=\"" + photoSrc + "\" />";
				triggerLoad = 'load';
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
					currentAlbum.media[currentMediaIndex].dayAlbum + '/' + currentAlbum.media[currentMediaIndex].name;
				// following 2 iteration are needed with date album: the same photo could be present coming from different albums
				do {
					if (i == 0)
						i = currentAlbum.media.length - 1;
					else
						i --;
					previousMedia = currentAlbum.media[i];
					previousMedia.byDateName = previousMedia.dayAlbum + '/' + previousMedia.name;
				} while (previousMedia.byDateName == currentAlbum.media[currentMediaIndex].byDateName && i != currentMediaIndex);
				
				i = currentMediaIndex;
				do {
					if (i == currentAlbum.media.length - 1)
						i = 0;
					else
						i ++;
					nextMedia = currentAlbum.media[i];
					nextMedia.byDateName = nextMedia.dayAlbum + '/' + nextMedia.name;
				} while (nextMedia.byDateName == currentAlbum.media[currentMediaIndex].byDateName && i != currentMediaIndex);
				
				$.preloadImages(photoFloat.mediaPath(currentAlbum, nextMedia, Options.reduced_sizes[Options.reduced_sizes.length - 1]));
				$.preloadImages(photoFloat.mediaPath(currentAlbum, previousMedia, Options.reduced_sizes[Options.reduced_sizes.length - 1]));
			}
		}
		
		$(".next-media").off("click");
		$('#next').off("click");
		$('#prev').off("click");
		if (currentAlbum.media.length == 1) {
			nextLink = "";
			prevLink = "";
		} else {
			nextLink = "#!/" + photoFloat.mediaHash(currentAlbum, nextMedia);
			prevLink = "#!/" + photoFloat.mediaHash(currentAlbum, previousMedia);
			$("#next").show();
			$("#prev").show();
			$(".next-media").click(function(){ swipeLeft(nextLink); return false; });
			$('#next').click(function(){ swipeLeft(nextLink); return false; });
			$('#prev').click(function(){ swipeRight(prevLink); return false; });
		}
		$("#original-link").attr("target", "_blank").attr("href", photoFloat.originalMediaPath(currentMedia));
		
		if (currentAlbum.path.indexOf(Options.by_date_string) === 0)
			changeViewLink = "#!/" + PhotoFloat.cachePath(currentMedia.foldersAlbum) + "/" + PhotoFloat.cachePath(currentMedia.name);
		else
			changeViewLink = "#!/" + PhotoFloat.cachePath(currentMedia.dayAlbum) + "/" + PhotoFloat.cachePath(currentMedia.name);
		$("#day-folders-view-link").attr("href", changeViewLink);
		
		text = "<table>";
		if (typeof currentMedia.metadata.make !== "undefined") text += "<tr><td>Camera Maker</td><td>" + currentMedia.metadata.make + "</td></tr>";
		if (typeof currentMedia.metadata.model !== "undefined") text += "<tr><td>Camera Model</td><td>" + currentMedia.metadata.model + "</td></tr>";
		if (typeof currentMedia.metadata.date !== "undefined") text += "<tr><td>Time Taken</td><td>" + currentMedia.metadata.date + "</td></tr>";
		if (typeof currentMedia.metadata.size !== "undefined") text += "<tr><td>Resolution</td><td>" + currentMedia.metadata.size[0] + " x " + currentMedia.metadata.size[1] + "</td></tr>";
		if (typeof currentMedia.metadata.aperture !== "undefined") text += "<tr><td>Aperture</td><td> f/" + getDecimal(currentMedia.metadata.aperture) + "</td></tr>";
		if (typeof currentMedia.metadata.focalLength !== "undefined") text += "<tr><td>Focal Length</td><td>" + getDecimal(currentMedia.metadata.focalLength) + " mm</td></tr>";
		if (typeof currentMedia.metadata.subjectDistanceRange !== "undefined") text += "<tr><td>Subject Distance Range</td><td>" + currentMedia.metadata.subjectDistanceRange + "</td></tr>";
		if (typeof currentMedia.metadata.iso !== "undefined") text += "<tr><td>ISO</td><td>" + currentMedia.metadata.iso + "</td></tr>";
		if (typeof currentMedia.metadata.sceneCaptureType !== "undefined") text += "<tr><td>Scene Capture Type</td><td>" + currentMedia.metadata.sceneCaptureType + "</td></tr>";
		if (typeof currentMedia.metadata.exposureTime !== "undefined") text += "<tr><td>Exposure Time</td><td>" + getDecimal(currentMedia.metadata.exposureTime) + " sec</td></tr>";
		if (typeof currentMedia.metadata.exposureProgram !== "undefined") text += "<tr><td>Exposure Program</td><td>" + currentMedia.metadata.exposureProgram + "</td></tr>";
		if (typeof currentMedia.metadata.exposureCompensation !== "undefined") text += "<tr><td>Exposure Compensation</td><td>" + getDecimal(currentMedia.metadata.exposureCompensation) + "</td></tr>";
		if (typeof currentMedia.metadata.spectralSensitivity !== "undefined") text += "<tr><td>Spectral Sensitivity</td><td>" + currentMedia.metadata.spectralSensitivity + "</td></tr>";
		if (typeof currentMedia.metadata.sensingMethod !== "undefined") text += "<tr><td>Sensing Method</td><td>" + currentMedia.metadata.sensingMethod + "</td></tr>";
		if (typeof currentMedia.metadata.lightSource !== "undefined") text += "<tr><td>Light Source</td><td>" + currentMedia.metadata.lightSource + "</td></tr>";
		if (typeof currentMedia.metadata.flash !== "undefined") text += "<tr><td>Flash</td><td>" + currentMedia.metadata.flash + "</td></tr>";
		if (typeof currentMedia.metadata.orientation !== "undefined") text += "<tr><td>Orientation</td><td>" + currentMedia.metadata.orientation + "</td></tr>";
		if (typeof currentMedia.metadata.duration !== "undefined") text += "<tr><td>Duration</td><td>" + currentMedia.metadata.duration + " sec</td></tr>";
		text += "</table>";
		$("#metadata").html(text);
		
		$("#subalbums").hide();
		$("#media-view").show();
	}
	
	function setOptions() {
		var albumThumbnailSize, mediaThumbnailSize;
		albumThumbnailSize = Options.album_thumb_size;
		mediaThumbnailSize = Options.media_thumb_size;
		$("body").css("background-color", Options.background_color);
		$("#day-folders-view-container").hover(function() {
			//mouse over
			$(this).css("color", Options.switch_button_color_hover);
			$(this).css("background-color", Options.switch_button_background_color_hover);
		}, function() {
			//mouse out
			$(this).css("color", Options.switch_button_color);
			$(this).css("background-color", Options.switch_button_background_color);
		});
		
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
		$(".thumb-container").css("margin-right", Options.thumb_spacing.toString() + "px");
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
		return;
	}
	function needAlbumHtmlReverse() {
		if (currentAlbum.albumReverseSort === undefined)
			currentAlbum.albumReverseSort = false;
		var needReverse =
			currentAlbum.albumReverseSort && ! getBooleanCookie("albumReverseSortRequested") ||
			! currentAlbum.albumReverseSort && getBooleanCookie("albumReverseSortRequested");
		return needReverse;
	}
	function needMediaHtmlReverse() {
		if (currentAlbum.mediaReverseSort === undefined)
			currentAlbum.mediaReverseSort = false;
		var needReverse =
			currentAlbum.mediaReverseSort && ! getBooleanCookie("mediaReverseSortRequested") ||
			! currentAlbum.mediaReverseSort && getBooleanCookie("mediaReverseSortRequested");
		return needReverse;
	}

	/* Error displays */
	
	function die(error) {
		if (error == 403) {
			$("#auth-text").fadeIn(1000);
			$("#password").focus();
		} else
			$("#error-text").fadeIn(2500);
		$("#error-overlay").fadeTo(500, 0.8);
		$("body, html").css("overflow", "hidden");
	}
	function undie() {
		$("#error-text, #error-overlay, #auth-text").fadeOut(500);
		$("body, html").css("overflow", "auto");
	}
	

	
	/* Entry point for most events */
	
	function hashParsed(album, media, mediaIndex) {
		var populateAlbum;
		undie();
		$("#loading").hide();
		if (album === currentAlbum && media === currentMedia)
			return;
		if (album != currentAlbum)
			currentAlbum = null;
		
		previousAlbum = currentAlbum;
		if (currentAlbum && currentAlbum.path.indexOf(Options.by_date_string) === 0 && media !== null) {
			previousMedia = media;
		}
		else {
			previousMedia = currentMedia;
		}
		currentAlbum = album;
		currentMedia = media;
		currentMediaIndex = mediaIndex;
		
		setOptions();
		if (currentMedia === null || typeof currentMedia === "object")
			setTitle();
		
		if (currentMedia !== null || currentAlbum !== null && ! currentAlbum.albums.length && currentAlbum.media.length == 1)
		{
			if (currentMedia === null) {
				currentMedia = currentAlbum.media[0];
				currentMediaIndex = 1;
			}
			$("#day-folders-view-container").show();
			nextMedia = null;
			previousMedia = null;
			showMedia(currentAlbum);
		}
		else {
			$("#day-folders-view-container").hide();
		}
		populateAlbum = previousAlbum !== currentAlbum || previousMedia !== currentMedia;
		showAlbum(populateAlbum);
		if (currentMedia !== null || ! Options.show_media_names_below_thumbs_in_albums)
			$(".media-caption").hide();
		else
			$(".media-caption").show();
		// options function must be called again in order to set elements previously absent
		setOptions();
		if (currentMedia !== null || currentAlbum !== null && ! currentAlbum.albums.length) {
			// no subalbums, nothing to wait
			// set social buttons events
			$("#media").on("load", socialButtons);
		}
	}

	function getOptions(cacheSubDir, callback) {
		if (Object.keys(Options).length > 0)
			callback(location.hash, hashParsed, die);
		else {
			if (cacheSubDir && cacheSubDir.substr(-1) != "/")
				cacheSubDir += "/";
			var optionsFile = cacheSubDir + "options.json";
			var ajaxOptions = {
				type: "GET",
				dataType: "json",
				url: optionsFile,
				success: function(data) {
					for (var key in data)
						if (data.hasOwnProperty(key))
							Options[key] = data[key];
					if (Options.server_cache_path && Options.server_cache_path.substr(-1) != "/")
						Options.server_cache_path += "/";
					if (Options.server_album_path && Options.server_album_path.substr(-1) != "/")
						Options.server_album_path += "/";
					translate();
					
					if (getBooleanCookie("albumReverseSortRequested") === null)
						setBooleanCookie("albumReverseSortRequested", Options.default_album_reverse_sort);
					if (getBooleanCookie("mediaReverseSortRequested") === null)
						setBooleanCookie("mediaReverseSortRequested", Options.default_media_reverse_sort);
					
					byDateRegex = "^" + Options.by_date_string + "\/[1-2][0-9]{1,3}";
					
					maxSize = Options.reduced_sizes[Options.reduced_sizes.length - 1];
					
					callback(location.hash, hashParsed, die);
				},
				error: function(jqXHR, textStatus, errorThrown) {
					if (errorThrown == "Not Found" && ! cacheSubDir)
						getOptions(Options.server_cache_path, callback);
					else {
						$("#album-view").fadeOut(200);
						$("#media-view").fadeOut(200);
						$("#album-view").fadeIn(3500);
						$("#media-view").fadeIn(3500);
						$("#error-options-file").fadeIn(200);
						$("#error-options-file, #error-overlay, #auth-text").fadeOut(2500);
					}
				}
			};
			if (typeof error !== "undefined" && error !== null) {
				ajaxOptions.error = function(jqXHR, textStatus, errorThrown) {
					$("#error-options-file").fadeIn(2000);
					$("#error-options-file, #error-overlay, #auth-text").fadeOut(1000);
				};
			}
			$.ajax(ajaxOptions);
		}
	}
	
	// this function is needed in order to let this point to the correct value in photoFloat.parseHash
	function parseHash(hash, callback, error) {
		photoFloat.parseHash(hash, callback, error);
	}
	
	/* Event listeners */
	
	$(window).hashchange(function() {
		$("#loading").show();
		$("link[rel=image_src]").remove();
		$("link[rel=video_src]").remove();
		getOptions("", parseHash);
	});
	$(window).hashchange();
	
	
	$(document).keydown(function(e){
		if (currentMedia === null)
		if (! e.ctrlKey && ! e.shiftKey && e.altKey && (e.keyCode === 34 || e.keyCode === 39 || e.keyCode === 40)) {
			swipeLeft(nextLink);
			return false;
		} else if (! e.ctrlKey && ! e.shiftKey && e.altKey  && (e.keyCode === 33 || e.keyCode === 37 || e.keyCode === 38)) {
			swipeRight(prevLink);
			return false;
		}
		return true;
	});
	$(document).mousewheel(function(event, delta) {
		
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
	});
	
	$(document).on("load", detectSwipe('media-box-inner',swipe));
	
	if (isMobile.any()) {
		$("#links").css("display", "inline").css("opacity", 0.5);
	} else {
		$("#media-view").off("mouseenter");
		$("#media-view").off("mouseleave");
		$("#media-view").mouseenter(function() {
			$("#links").stop().fadeTo("slow", 0.50).css("display", "inline");
		});
		$("#media-view").mouseleave(function() {
			$("#links").stop().fadeOut("slow");
		});
	}
	
	$("#next, #prev").mouseenter(function() {
		$(this).stop().fadeTo("fast", 1);
	});
	$("#next, #prev").mouseleave(function() {
		$(this).stop().fadeTo("fast", 0.4);
	});
	if ($.support.fullscreen) {
		$("#fullscreen").show();
		$("#fullscreen").click(function(e) {
			e.preventDefault();
			$('#media').off('loadstart').unbind("load");
			$("#media-box").fullScreen({
				callback: function(isFullscreen) {
					fullScreenStatus = isFullscreen;
					$("#enter-fullscreen").toggle();
					$("#exit-fullscreen").toggle();
					showMedia(currentAlbum);
				}
			});
		});
	}
	$("#metadata-show").click(function() {
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
	});
	$("#metadata-hide").click(function() {
		$("#metadata-show").show();
		$("#metadata-hide").hide();
		$("#metadata")
			.stop()
			.animate({ height: 0, paddingTop: 0, paddingBottom: 0 }, "slow", function() {
				$(this).hide();
			});
	});
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
