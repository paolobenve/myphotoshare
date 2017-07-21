var Options = {};
var nextLink, backLink;

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
		if (key == '#title-string' && document.title.substr(0, 5) != "<?php")
			// don't set page title, php has already set it
			continue;
		selector = $(key);
		if (selector.length) {
			selector.html(translations[language][key]);
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
	var photoFloat = new PhotoFloat();
	var maxSize;
	var fullScreenStatus = false;
	var photoSrc, videoSrc;
	var language;
	var byDateRegex;
	var numSubAlbumsReady = 0;
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
	
	/* Displays */
	
	// from https://stackoverflow.com/questions/15084675/how-to-implement-swipe-gestures-for-mobile-devices#answer-27115070
	function detectswipe(el,func) {
		swipe_det = new Object();
		swipe_det.sX = 0; swipe_det.sY = 0; swipe_det.eX = 0; swipe_det.eY = 0;
		var min_x = 30;  //min x swipe for horizontal swipe
		var max_x = 30;  //max x difference for vertical swipe
		var min_y = 50;  //min y swipe for vertical swipe
		var max_y = 60;  //max y difference for horizontal swipe
		var direc = "";
		ele = document.getElementById(el);
		ele.addEventListener('touchstart',function(e){
			var t = e.touches[0];
			swipe_det.sX = t.screenX; 
			swipe_det.sY = t.screenY;
		},false);
		ele.addEventListener('touchmove',function(e){
			e.preventDefault();
			var t = e.touches[0];
			swipe_det.eX = t.screenX; 
			swipe_det.eY = t.screenY;    
		},false);
		ele.addEventListener('touchend',function(e){
			//horizontal detection
			if ((((swipe_det.eX - min_x > swipe_det.sX) || (swipe_det.eX + min_x < swipe_det.sX)) && ((swipe_det.eY < swipe_det.sY + max_y) && (swipe_det.sY > swipe_det.eY - max_y) && (swipe_det.eX > 0)))) {
			if(swipe_det.eX > swipe_det.sX) direc = "r";
			else direc = "l";
			}
			//vertical detection
			else if ((((swipe_det.eY - min_y > swipe_det.sY) || (swipe_det.eY + min_y < swipe_det.sY)) && ((swipe_det.eX < swipe_det.sX + max_x) && (swipe_det.sX > swipe_det.eX - max_x) && (swipe_det.eY > 0)))) {
				if(swipe_det.eY > swipe_det.sY) direc = "d";
				else direc = "u";
			}

			if (direc != "") {
				if(typeof func == 'function') func(el,direc);
			}
			direc = "";
			swipe_det.sX = 0; swipe_det.sY = 0; swipe_det.eX = 0; swipe_det.eY = 0;
		},false);  
	}
	
	function swipeRight(dest) {
		$("#media-box-inner").animate({
			right: "-=" + window.innerWidth,
		}, 300, function() {
			location.href = dest;
			$("#media-box-inner").css('right', "");
		});
	}
	function swipeLeft(dest) {
		$("#media-box-inner").animate({
			left: "-=" + window.innerWidth,
		}, 300, function() {
			location.href = dest;
			$("#media-box-inner").css('left', "");
		});
	}
	
	function swipe(el,d) {
		if (d == "r") {
			swipeRight(backLink);
		} else if (d == "l") {
			swipeLeft(nextLink);
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
		} else if (currentMedia.mediaType == "video") {
			mediaArray.push($("#video").attr("src"));
			type = "v";
		} else {
			type = "i";
			mediaArray.push($("#photo").attr("src"));
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
		$('.ssk-whatsapp').attr('data-url', myShareUrl);
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
		if (Options.page_title !== "")
			originalTitle = Options.page_title;
		else
			originalTitle = translations[language]["#title-string"];
		
		if (! PhotoFloat.firstAlbumPopulation || getBooleanCookie("albumReverseSortRequested") || getBooleanCookie("mediaReverseSortRequested")) {
			if (PhotoFloat.firstAlbumPopulation)
				PhotoFloat.firstAlbumPopulation = false;
			if (needMediaHtmlReverse()) {
				currentAlbum.photos = currentAlbum.photos.reverse();
				if (currentMediaIndex !== undefined && currentMediaIndex != -1)
					currentMediaIndex = currentAlbum.photos.length - 1 - currentMediaIndex;
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
		for (i = 0; i < components.length; ++i) {
			if (i)
				last += "/" + components[i];
			if (i != 1 || components[i] != Options.folders_string) {
				if (i < components.length - 1 || currentMedia !== null)
					if (! (i == 0 && dateTitle))
						if (i == 1 && dateTitle)
							title = "<a class='title-anchor' href=\"#!/" + (i ? photoFloat.cachePath(last.substring(1)) : "") + "\">" + title;
						else
							title += "<a class='title-anchor' href=\"#!/" + (i ? photoFloat.cachePath(last.substring(1)) : "") + "\">";
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
		if (currentMedia !== null)
			title += "<span id=\"photo-name\">" + photoFloat.trimExtension(currentMedia.name) + "</span>";
			
		else if (currentMedia !== null || currentAlbum !== null && ! currentAlbum.albums.length && currentAlbum.photos.length == 1)
			title += " &raquo; <span id=\"photo-name\">" + photoFloat.trimExtension(currentAlbum.photos[0].name) + "</span>";
		else {
			// the arrows for changing sort
			if (currentAlbum.albums.length > 1)
				title += "<a id=\"album-sort-arrows\" class=\"arrows\" href=\"javascript:void(0)\">" +
						"<img id=\"album-sort-reverse\" title=\"" + _t("#album-sort-reverse") + "\" height=\"15px\" src=\"img/Folder_sort_reverse.png\">" +
						"<img id=\"album-sort-normal\" title=\"" + _t("#album-sort-normal") + "\" height=\"15px\" src=\"img/Folder_sort_normal.png\">" +
					"</a>";
			if (currentAlbum.photos.length > 1)
				title += "<a id=\"media-sort-arrows\" class=\"arrows\" href=\"javascript:void(0)\">" +
						"<img id=\"media-sort-reverse\" title=\"" + _t("#media-sort-reverse") + "\" height=\"15px\" src=\"img/People_sort_reverse.png\">" +
						"<img id=\"media-sort-normal\" title=\"" + _t("#media-sort-normal") + "\" height=\"15px\" src=\"img/People_sort_normal.png\">" +
					"</a>";
		}
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
		else if (currentMedia !== null || currentAlbum !== null && ! currentAlbum.albums.length && currentAlbum.photos.length == 1)
			documentTitle =  photoFloat.trimExtension(currentAlbum.photos[0].name) + " \u00ab " + documentTitle;
		
		document.title = documentTitle;
		$("#title-string").html(title);
		
		if (currentMedia === null) {
			$("body").on('mouseenter', "#title-container", function() {
				if (currentAlbum.albums.length > 1) {
					$("#album-sort-arrows").show();
					if (getBooleanCookie("albumReverseSortRequested")) {
						$("#album-sort-reverse").hide();
						$("#album-sort-normal").show();
					} else {
						$("#album-sort-reverse").show();
						$("#album-sort-normal").hide();
					}
				}
				if (currentAlbum.photos.length > 1 && ! (currentAlbum.path.match(byDateRegex) && currentAlbum.photos.length >= Options.big_date_folders_threshold)) {
					$("#media-sort-arrows").show();
				}
			});
			$("body").on('mouseleave', "#title-container", function() {
				$("#album-sort-arrows").hide();
				$("#media-sort-arrows").hide();
			});
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
			if (currentAlbum.photos.length > 1) {
				$("#title").on('click', "#media-sort-arrows", function() {
					if (currentMedia !== null)
						currentMediaIndex = currentAlbum.photos.length - 1 - currentMediaIndex;
					currentAlbum.photo = currentAlbum.photos.reverse();
					
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
		var photo, thumb;

		photo = currentMedia;
		if (photo === null) {
			photo = previousMedia;
			if (photo === null)
				return;
		}
		$("#thumbs img").each(function() {
			if (this.title === photo.name) {
				thumb = $(this);
				return false;
			}
		});
		if (typeof thumb === "undefined")
			return;
		if (currentMedia !== null) {
			var scroller = $("#album-view");
			scroller.stop().animate({ scrollLeft: thumb.parent().position().left + scroller.scrollLeft() - scroller.width() / 2 + thumb.width() / 2 }, "slow");
		} else
			$("html, body").stop().animate({ scrollTop: thumb.offset().top - $(window).height() / 2 + thumb.height() }, "slow");
		
		if (currentMedia !== null) {
			$("#thumbs img").removeClass("current-thumb");
			thumb.addClass("current-thumb");
		}
	}
	
	
	function showAlbum(populate) {
		var i, link, image, photos, thumbsElement, subalbums, subalbumsElement, hash, thumbHash, thumbnailSize;
		var width, height, thumbWidth, thumbHeight, imageString, bydateStringWithTrailingSeparator, populateMedia;
		var photoWidth, photoHeight;
		if (currentMedia === null && previousMedia === null)
			$("html, body").stop().animate({ scrollTop: 0 }, "slow");
		if (populate) {
			thumbnailSize = Options.media_thumb_size;
			
			populateMedia = populate;
			if (populateMedia === true && ! ! currentAlbum.path.match(byDateRegex))
				populateMedia = populateMedia && (currentAlbum.photos.length < Options.big_date_folders_threshold);
			
			if (populateMedia === true || populateMedia && needMediaHtmlReverse()) {
				photos = [];
				for (i = 0; i < currentAlbum.photos.length; ++i) {
					hash = photoFloat.photoHash(currentAlbum, currentAlbum.photos[i]);
					thumbHash = photoFloat.photoPath(currentAlbum, currentAlbum.photos[i], thumbnailSize);
					bydateStringWithTrailingSeparator = Options.by_date_string + Options.cache_folder_separator;
					if (thumbHash.indexOf(bydateStringWithTrailingSeparator) === 0) {
						thumbHash =
							PhotoFloat.cachePath(currentAlbum.photos[i].completeName
								.substring(0, currentAlbum.photos[i].completeName.length - currentAlbum.photos[i].name.length - 1)) +
							"/" +
							PhotoFloat.cachePath(currentAlbum.photos[i].name);
					}
					link = $("<a href=\"#!/" + hash + "\"></a>");
					width = currentAlbum.photos[i].size[0];
					height = currentAlbum.photos[i].size[1];
					imageString = "<div class=\"thumb-container\" ";
					imageString += "style=\"width: ";
					if (Options.media_thumb_type == "fixed_height") {
						thumbHeight = Options.media_thumb_size;
						thumbWidth = thumbHeight * width / height;
						imageString += thumbWidth.toString();
					} else {
						imageString += Options.media_thumb_size.toString().toString();
					}
					imageString += 			"px;\">";
					imageString += 		"<img title=\"" + currentAlbum.photos[i].name +
								"\" alt=\"" + photoFloat.trimExtension(currentAlbum.photos[i].name) +
								"\" src=\"" +  thumbHash +
								"\" class=\"thumbnail";
					if (Options.media_thumb_type == "fixed_height") {
						imageString += 	"\" height=\"" + thumbHeight +
								"\" width=\"" + thumbWidth;
					} else {
						imageString += 	"\" height=\"" + thumbnailSize +
								"\" width=\"" + thumbnailSize;
					}
					imageString += 		"\" />" +
								"<div class=\"media-caption\">" +
								currentAlbum.photos[i].name.replace(/ /g, "</span> <span style=\"white-space: nowrap;\">") +
								"</div>" +
								"</div>";
					image = $(imageString);
					
					
					
					image.get(0).photo = currentAlbum.photos[i];
					link.append(image);
					photos.push(link);
					(function(theLink, theImage, theAlbum) {
						theImage.error(function() {
							photos.splice(photos.indexOf(theLink), 1);
							theLink.remove();
							theAlbum.photos.splice(theAlbum.photos.indexOf(theImage.get(0).photo), 1);
						});
					})(link, image, currentAlbum);
				}
				
				thumbsElement = $("#thumbs");
				thumbsElement.empty();
				thumbsElement.append.apply(thumbsElement, photos);
				
				if (needMediaHtmlReverse())
					currentAlbum.mediaReverseSort = ! currentAlbum.mediaReverseSort;
			} else if (currentAlbum.photos.length < Options.big_date_folders_threshold) {
				$("#thumbs").html("<span id=\"too-many-images\">Too many images: " + currentAlbum.photos.length + " (limit for date album is " + Options.big_date_folders_threshold +  ")</span>");
				$("#thumbs").empty();
			}
			
			if (currentMedia === null) {
				if (populate === true || populate && needAlbumHtmlReverse()) {
					subalbums = [];
					for (i = 0; i < currentAlbum.albums.length; ++i) {
						link = $("<a href=\"#!/" + photoFloat.albumHash(currentAlbum.albums[i]) + "\"></a>");
						imageString = "<div class=\"album-button\"";
						imageString += 		" style=\"";
						imageString += 			"width: " + (Options.album_thumb_size + 6) + "px;";
						imageString += 			" height: " + (Options.album_thumb_size + 6) + "px;";
						if (! Options.albums_slide_style)
							imageString +=		" background-color: " + Options.album_button_background_color + ";";
						imageString += 			"\"";
						imageString += ">";
						imageString += "</div>";
						image = $(imageString);
						link.append(image);
						subalbums.push(link);
						(function(theContainer, theAlbum, theImage, theLink) {
							photoFloat.pickRandomMedia(theAlbum, theContainer, function(randomAlbum, randomPhoto, originalAlbum) {
								var distance = 0;
								var htmlText;
								var folderArray, originalAlbumFoldersArray, folder, captionHeight, ButtonAndCaptionHeight, html;
								if (Options.album_thumb_type == "fit") {
									photoWidth = randomPhoto.size[0];
									photoHeight = randomPhoto.size[1];
									if (photoWidth > photoHeight) {
										thumbWidth = Options.album_thumb_size;
										thumbHeight = Options.album_thumb_size * photoHeight / photoWidth;
									} else {
										thumbWidth = Options.album_thumb_size * photoWidth / photoHeight;
										thumbHeight = Options.album_thumb_size;
									}
									distance = (Options.album_thumb_size - thumbHeight) / 2;
								}
								htmlText = "<img " +
										"title=\"" + randomPhoto.albumName + "\"" +
										" class=\"thumbnail\"" +
										" src=\"" + photoFloat.photoPath(randomAlbum, randomPhoto, Options.album_thumb_size) + "\"" +
										" style=\"width:" + thumbWidth + "px;" +
											" height:" + thumbHeight + "px;" +
											" margin-top: " + distance + "px" +
											"\"" +
										">";
								theImage.html(htmlText);
								
								if (originalAlbum.path.indexOf(Options.by_date_string) === 0)
									folderArray = randomPhoto.dayAlbum.split("/");
								else
									folderArray = randomPhoto.albumName.split("/");
								originalAlbumFoldersArray = originalAlbum.path.split("/");
								folder = folderArray[originalAlbumFoldersArray.length];
								
								captionHeight = em2px("body", 4);
								ButtonAndCaptionHeight = Options.album_thumb_size + captionHeight;
								html = "<div class=\"album-button-and-caption";
								if (Options.albums_slide_style)
									html += " slide";
								html += "\"";
								html += "style=\"";
								html += 	"height: " + ButtonAndCaptionHeight.toString() + "px; " +
										"margin-right: " + Options.thumb_spacing + "px; ";
								if (Options.albums_slide_style)
									html += "width: " + Math.round(Options.album_thumb_size * 1.1).toString() + "px; ";
								else
									html += "width: " + Options.album_thumb_size.toString() + "px; ";
								html += "padding-top: " + Math.round(Options.album_thumb_size * 0.05).toString() + "px; ";
								if (Options.albums_slide_style)
									html += "background-color: " + Options.album_button_background_color + "; ";
								html += "\"";
								html += ">";
								theImage.wrap(html);
								html = "<div class=\"album-caption\"";
								html += " style=\"width: " + Options.album_thumb_size.toString() + "px; height: " + captionHeight.toString() + "px; ";
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
			$("#album-view").removeClass("photo-view-container");
			$("#subalbums").show();
			$("#media-view").hide();
			$("#media-box-inner").empty();
			$("#media-box").hide();
			$("#thumbs").show();
			$("#day-folders-view-container").show();
			if (currentAlbum.path == Options.folders_string) {
				$("#folders-view").hide();
				$("#day-view").show();
				$("#day-folders-view-link").attr("href", "#!/" + Options.by_date_string);
			}
			else if (currentAlbum.path == Options.by_date_string) {
				$("#folders-view").show();
				$("#day-view").hide();
				$("#day-folders-view-link").attr("href", "#!/" + Options.folders_string);
			} else {
				$("#folders-view").hide();
				$("#day-view").hide();
			}
			$("#powered-by").show();
		} else {
			if (currentAlbum.photos.length == 1)
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
	function scaleMedia() {
		var media, container, height, containerBottom, bottom, width, photoSrc, previousSrc;
		$(window).off("resize");
		if (currentMedia.mediaType == "video") {
			$('#video').off('loadstart');
		} else {
			$("#photo").off("load");
		}
		if (fullScreenStatus)
			container = $(window);
		else {
			container = $("#media-view");
			containerBottom = 0;
			if ($("#album-view").is(":visible"))
				containerBottom = $("#album-view").outerHeight();
			else if ($(".ssk-group").css("display") != "block" && parseInt($("#media-bar").css("bottom")) < $(".ssk").outerHeight())
				// correct container bottom when social buttons are on the bottom
				containerBottom = $(".ssk").outerHeight();

			container.css("bottom", containerBottom + "px");
			container.css("top", $("#title-container").outerHeight() + "px");
		}
		
		if (currentMedia.mediaType == "video") {
			media = $("#video");
		} else {
			media = $("#photo");
			photoSrc = chooseMediaForScaling(currentMedia, container);
			// chooseMediaForScaling() sets maxSize to 0 if it returns the original media
			previousSrc = media.attr("src");
			width = currentMedia.size[0];
			height = currentMedia.size[1];
			if (maxSize) {
				if (width > height) {
					height = Math.round(height * maxSize / width);
					width = maxSize;
				} else {
					width = Math.round(width * maxSize / height);
					height = maxSize;
				}
			}
			if (photoSrc != previousSrc) {
				$("link[rel=image_src]").remove();
				$('link[rel="video_src"]').remove();
				$("head").append("<link rel=\"image_src\" href=\"" + photoSrc + "\" />");
				media.attr("src", photoSrc)
					.attr("width", width).attr("height", height).attr("ratio", width / height);
			}
		}
		
		if (parseInt(media.attr("width")) > container.width() && media.attr("ratio") > container.width() / container.height()) {
			height = container.width() / media.attr("ratio");
			media.css("width", "100%").
				css("height", "auto").
				parent().
					css("height", height).
					css("margin-top", - height / 2).
					css("top", "50%");
			bottom = ((container.height() - parseInt(media.css("height"))) / 2) + "px";
		} else if (parseInt(media.attr("height")) > container.height() && media.attr("ratio") < container.width() / container.height()) {
			media.css("height", "100%").
				css("width", "auto").
				parent().
					css("height", "100%").
					css("margin-top", "0").
					css("top", "0");
			if (currentMedia.mediaType != "video")
				bottom = 0;
			else
				bottom = ((container.height() - parseInt(media.css("height"))) / 2) + "px";
		} else {
			media.css("height", "").css("width", "").
				parent().
					css("height", media.attr("height")).
					css("margin-top", - media.attr("height") / 2).
					css("top", "50%");
			bottom = ((container.height() - parseInt(media.css("height"))) / 2) + "px";
		}
		
		if (currentMedia.mediaType == "video") {
			$("#media-bar").css("bottom", 0);
		} else {
			media.css("bottom", bottom);
			$("#media-bar").css("bottom", bottom);
		}
		
		if (! fullScreenStatus && currentAlbum.photos.length > 1 && $(".ssk-group").css("display") == "block") {
			// correct back arrow position when social buttons are on the left
			$("#back").css("left", "");
			$("#back").css("left", (parseInt($("#back").css("left")) + $(".ssk").outerWidth()) + "px");
		}
		
		$(window).bind("resize", scaleMedia);
	}
	function chooseMediaForScaling(media, container) {
		var chosenMedia, reducedWidth, reducedHeight;
		chosenMedia = PhotoFloat.originalPhotoPath(currentMedia);
		maxSize = 0;
		for (var i = 0; i < Options.reduced_sizes.length; i++) {
			if (media.size[0] > media.size[1]) {
				reducedWidth = Options.reduced_sizes[i];
				reducedHeight = Options.reduced_sizes[i] * media.size[1] / media.size[0];
			} else {
				reducedHeight = Options.reduced_sizes[i];
				reducedWidth = Options.reduced_sizes[i] * media.size[0] / media.size[1];
			}
			
			if (reducedWidth < container.width() && reducedHeight < container.height())
				break;
			chosenMedia = photoFloat.photoPath(currentAlbum, currentMedia, Options.reduced_sizes[i]);
			maxSize = Options.reduced_sizes[i];
		}
		return chosenMedia;
	}
	
	function showMedia(album) {
		var width, height, previousMedia, nextMedia, text, thumbnailSize, i, changeViewLink, linkTag, triggerLoad, videoOK = true;
		var windowWidth, windowHeight;
		width = currentMedia.size[0];
		height = currentMedia.size[1];

		windowWidth = $(window).width();
		windowHeight = $(window).height();
		
		thumbnailSize = Options.media_thumb_size;
		$("#media-box").show();
		if (currentAlbum.photos.length == 1) {
			$("#next").hide();
			$("#back").hide();
			$(".next-media").removeAttr("href");
			$("#next").removeAttr("href");
			$("#back").removeAttr("href");
			$("#media-view").addClass("no-bottom-space");
			$("#album-view").addClass("no-bottom-space");
		} else {
			$("#next").show();
			$("#back").show();
			$("#media-view").removeClass("no-bottom-space");
			$("#album-view").removeClass("no-bottom-space");
			$("#media-view").css("bottom", (thumbnailSize + 15).toString() + "px");
			$("#album-view").css("height", (thumbnailSize + 20).toString() + "px");
			$("#album-view").addClass("photo-view-container");
			$("#album-view.photo-view-container").css("height", (thumbnailSize + 22).toString() + "px");
		}

		var albumViewHeight = 0;
		if ($("#album-view").is(":visible"))
			albumViewHeight = $("#album-view").outerHeight();
		
		$('#media-box-inner > img').remove();
		$('#media-box-inner > video').remove();
		
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
		
		
		if (currentMedia.mediaType != "video" || videoOK) {
			if (currentAlbum.path == photoFloat.photoFoldersAlbum(currentMedia)) {
				$("#folders-view").hide();
				$("#day-view").show();
			}
			else {
				$("#folders-view").show();
				$("#day-view").hide();
			}
			
			if (currentMedia.mediaType == "video") {
				if (fullScreenStatus) {
					////////////////////////////////////////////
					// the original video doesn't work: WHY????
					// videoSrc = currentMedia.albumName;
					////////////////////////////////////////////
					videoSrc = photoFloat.videoPath(currentAlbum, currentMedia);
				} else {
					videoSrc = photoFloat.videoPath(currentAlbum, currentMedia);
				}
				$('<video/>', { id: 'video', controls: true }).appendTo('#media-box-inner')
					.attr("width", width).attr("height", height).attr("ratio", width / height)
					.attr("src", videoSrc)
					.attr("alt", currentMedia.name);
				triggerLoad = 'loadstart';
				$('#media').on(triggerLoad, scaleMedia());
				linkTag = "<link rel=\"video_src\" href=\"" + videoSrc + "\" />";
			} else {
				maxSize = Options.reduced_sizes[Options.reduced_sizes.length - 1];
				if (width > height) {
					height = Math.round(height * maxSize / width);
					width = maxSize;
				} else {
					width = Math.round(width * maxSize / height);
					height = maxSize;
				}
				photoSrc = photoFloat.photoPath(currentAlbum, currentMedia, Options.reduced_sizes[Options.reduced_sizes.length - 1]);
				$('<img/>', { id: 'photo' }).appendTo('#media-box-inner')
					.attr("width", width).attr("height", height).attr("ratio", width / height)
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
				$(".metadata").hide();
				$(".metadata-show").show();
				$(".metadata-hide").hide();
			}
			
			if (currentAlbum.photos.length > 1) {
				i = currentMediaIndex;
				// following 2 iteration are needed with date album: the same photo could be present coming from different albums
				do {
					if (i == 0)
						i = currentAlbum.photos.length - 1;
					else
						i --;
					previousMedia = currentAlbum.photos[i];
				} while (previousMedia.byDateName == currentAlbum.photos[currentMediaIndex].byDateName && i != currentMediaIndex);
				
				i = currentMediaIndex;
				do {
					if (i == currentAlbum.photos.length - 1)
						i = 0;
					else
						i ++;
					nextMedia = currentAlbum.photos[i];
				} while (nextMedia.byDateName == currentAlbum.photos[currentMediaIndex].byDateName && i != currentMediaIndex);
				
				if (nextMedia.mediaType == "video") {
					$.preloadImages(photoFloat.videoPath(currentAlbum, nextMedia));
				} else {
					$.preloadImages(photoFloat.photoPath(currentAlbum, nextMedia, maxSize));
				}
				if (previousMedia.mediaType == "video") {
					$.preloadImages(photoFloat.videoPath(currentAlbum, previousMedia));
				} else {
					$.preloadImages(photoFloat.photoPath(currentAlbum, previousMedia, maxSize));
				}
			}
		}
		
		if (currentAlbum.photos.length == 1) {
			//nothing to do
		} else {
			nextLink = "#!/" + photoFloat.photoHash(currentAlbum, nextMedia);
			backLink = "#!/" + photoFloat.photoHash(currentAlbum, previousMedia)
			$("#next").show();
			$("#back").show();
			$(".next-media").off("click");
			$('#next').off("click");
			$('#back').off("click");
			$(".next-media").click(function(){ swipeLeft(nextLink); return false; });
			$('#next').click(function(){ swipeLeft(nextLink); return false; });
			$('#back').click(function(){ swipeRight(backLink); return false; });
			
			if (currentMedia.mediaType == "video")
				$("#video").load(detectswipe('media-box-inner',swipe));
			else
				$("#photo").load(detectswipe('media-box-inner',swipe));
		}
		$(".original-link").attr("target", "_blank").attr("href", photoFloat.originalPhotoPath(currentMedia));
		
		if (currentAlbum.path.indexOf(Options.by_date_string) === 0)
			changeViewLink = "#!/" + PhotoFloat.cachePath(currentMedia.foldersAlbum) + "/" + PhotoFloat.cachePath(currentMedia.name);
		else
			changeViewLink = "#!/" + PhotoFloat.cachePath(currentMedia.dayAlbum) + "/" + PhotoFloat.cachePath(currentMedia.name);
		$("#day-folders-view-link").attr("href", changeViewLink);
		
		text = "<table>";
		if (typeof currentMedia.make !== "undefined") text += "<tr><td>Camera Maker</td><td>" + currentMedia.make + "</td></tr>";
		if (typeof currentMedia.model !== "undefined") text += "<tr><td>Camera Model</td><td>" + currentMedia.model + "</td></tr>";
		if (typeof currentMedia.date !== "undefined") text += "<tr><td>Time Taken</td><td>" + currentMedia.date + "</td></tr>";
		if (typeof currentMedia.size !== "undefined") text += "<tr><td>Resolution</td><td>" + currentMedia.size[0] + " x " + currentMedia.size[1] + "</td></tr>";
		if (typeof currentMedia.aperture !== "undefined") text += "<tr><td>Aperture</td><td> f/" + getDecimal(currentMedia.aperture) + "</td></tr>";
		if (typeof currentMedia.focalLength !== "undefined") text += "<tr><td>Focal Length</td><td>" + getDecimal(currentMedia.focalLength) + " mm</td></tr>";
		if (typeof currentMedia.subjectDistanceRange !== "undefined") text += "<tr><td>Subject Distance Range</td><td>" + currentMedia.subjectDistanceRange + "</td></tr>";
		if (typeof currentMedia.iso !== "undefined") text += "<tr><td>ISO</td><td>" + currentMedia.iso + "</td></tr>";
		if (typeof currentMedia.sceneCaptureType !== "undefined") text += "<tr><td>Scene Capture Type</td><td>" + currentMedia.sceneCaptureType + "</td></tr>";
		if (typeof currentMedia.exposureTime !== "undefined") text += "<tr><td>Exposure Time</td><td>" + getDecimal(currentMedia.exposureTime) + " sec</td></tr>";
		if (typeof currentMedia.exposureProgram !== "undefined") text += "<tr><td>Exposure Program</td><td>" + currentMedia.exposureProgram + "</td></tr>";
		if (typeof currentMedia.exposureCompensation !== "undefined") text += "<tr><td>Exposure Compensation</td><td>" + getDecimal(currentMedia.exposureCompensation) + "</td></tr>";
		if (typeof currentMedia.spectralSensitivity !== "undefined") text += "<tr><td>Spectral Sensitivity</td><td>" + currentMedia.spectralSensitivity + "</td></tr>";
		if (typeof currentMedia.sensingMethod !== "undefined") text += "<tr><td>Sensing Method</td><td>" + currentMedia.sensingMethod + "</td></tr>";
		if (typeof currentMedia.lightSource !== "undefined") text += "<tr><td>Light Source</td><td>" + currentMedia.lightSource + "</td></tr>";
		if (typeof currentMedia.flash !== "undefined") text += "<tr><td>Flash</td><td>" + currentMedia.flash + "</td></tr>";
		if (typeof currentMedia.orientation !== "undefined") text += "<tr><td>Orientation</td><td>" + currentMedia.orientation + "</td></tr>";
		text += "</table>";
		$(".metadata").html(text);
		
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
		$("#photo-name").css("color", Options.title_image_name_color);
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
	
	function hashParsed(album, photo, photoIndex) {
		var populateAlbum;
		undie();
		$("#loading").hide();
		if (album === currentAlbum && photo === currentMedia)
			return;
		if (album != currentAlbum)
			currentAlbum = null;
		
		previousAlbum = currentAlbum;
		if (currentAlbum && currentAlbum.path.indexOf(Options.by_date_string) === 0 && photo !== null) {
			previousMedia = photo;
		}
		else {
			previousMedia = currentMedia;
		}
		currentAlbum = album;
		currentMedia = photo;
		currentMediaIndex = photoIndex;
		
		setOptions();
		if (currentMedia === null || typeof currentMedia === "object")
			setTitle();
		
		if (currentMedia !== null || currentAlbum !== null && ! currentAlbum.albums.length && currentAlbum.photos.length == 1)
		{
			if (currentMedia === null) {
				currentMedia = currentAlbum.photos[0];
				currentMediaIndex = 1;
			}
			$("#day-folders-view-container").show();
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
			$("#photo").load(socialButtons);
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
		console.log(e.keyCode);
		if (currentMedia === null || nextLink === undefined || backLink === undefined)
			return true;
		if (e.keyCode === 34 || e.keyCode === 39 || e.keyCode === 40) {
			swipeLeft(nextLink);
			return false;
		} else if (e.keyCode === 33 || e.keyCode === 37 || e.keyCode === 38) {
			swipeRight(backLink);
			return false;
		}
		return true;
	});
	$(document).mousewheel(function(event, delta) {
		
		if (currentMedia === null || nextLink === undefined || backLink === undefined)
			return true;
		if (delta < 0) {
			swipeLeft(nextLink);
			return false;
		} else if (delta > 0) {
			swipeRight(backLink);
			return false;
		}
		return true;
	});
	
	$("#media-view").mouseenter(function() {
		$(".links").stop().fadeTo("slow", 0.50).css("display", "inline");
	});
	$("#media-view").mouseleave(function() {
		$(".links").stop().fadeOut("slow");
	});
	$("#next, #back").mouseenter(function() {
		$(this).stop().fadeTo("slow", 1);
	});
	$("#next, #back").mouseleave(function() {
		$(this).stop().fadeTo("slow", 0.35);
	});
	if ($.support.fullscreen) {
		$(".fullscreen").show();
		$(".fullscreen").click(function(e) {
			e.preventDefault();
			if (currentMedia.mediaType == "video") {
				$('#video').off('loadstart');
				$("#media-box").fullScreen({
					callback: function(isFullscreen) {
						fullScreenStatus = isFullscreen;
						$(".enter-fullscreen").toggle();
						$(".exit-fullscreen").toggle();
						showMedia(currentAlbum);
					}
				});
			} else {
				$("#photo").unbind("load");
				$("#media-box").fullScreen({
					callback: function(isFullscreen) {
						fullScreenStatus = isFullscreen;
						$(".enter-fullscreen").toggle();
						$(".exit-fullscreen").toggle();
						showMedia(currentAlbum);
					}
				});
			}
		});
	}
	$(".metadata-show").click(function() {
		$(".metadata-show").hide();
		$(".metadata-hide").show();
		$(".metadata").stop()
			.css("height", 0)
			.css("padding-top", 0)
			.css("padding-bottom", 0)
			.show()
			.animate({ height: $(".metadata > table").height(), paddingTop: 3, paddingBottom: 3 }, "slow", function() {
				$(this).css("height", "auto");
			});
	});
	$(".metadata-hide").click(function() {
		$(".metadata-show").show();
		$(".metadata-hide").hide();
		$(".metadata").stop()
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
