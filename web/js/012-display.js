var Options = {};
var byDateRegex;

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
	var maxSizeSet = false;
	var fullScreenStatus = false;
	
	
	/* Displays */
	
	function getLanguage() {
		var language = "en";
		if (Options.language && translations[Options.language] !== undefined)
			language = Options.language;
		else {
			var userLang = navigator.language || navigator.userLanguage;
			language = userLang.split('-')[0];
		}
		return language;
	}
	
	function translate() {
		var language = getLanguage();
		var selector;
		for (var key in translations[language]) {
			selector = $("#" + key);
			if (selector.length) {
				selector.html(translations[language][key]);
			}
		}
	}
	
	function _t(id) {
		var language = getLanguage();
		return translations[language][id];
	}
	
	function setTitle() {
		var title = "", documentTitle = "", last = "", components, i, dateTitle;
		var originalTitle = Options.page_title;
		translate();
		
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
					title += "(" + _t("by-date") + ")";
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
		else {
			// the arrows for changing sort
			if (currentAlbum.albums.length > 1)
				title += "<a id=\"album-sort-arrows\" class=\"arrows\" href=\"javascript:void(0)\">" +
						"<img title=\"albums sort\" height=\"15px\" id=\"album-sort-icon\" width=\"15px\" src=\"img/Folder_6_icon-72a7cf.png\">" +
						"<span id=\"album-arrow-up\">🠙</span>" +
						"<span id=\"album-arrow-down\">🠛</span>" +
					"</a>";
			if (currentAlbum.photos.length > 1)
				title += "<a id=\"media-sort-arrows\" class=\"arrows\" href=\"javascript:void(0)\">" +
						"<img title=\"media sort\" height=\"15px\" id=\"media-sort-icon\" width=\"15px\" src=\"img/Creative-Tail-People-man.png\">" +
						"<span id=\"media-arrow-up\">🠙</span>" +
						"<span id=\"media-arrow-down\">🠛</span>" +
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
				documentTitle += " (" + _t("by-date") + ")";
			}
			else if (i > 1) {
				documentTitle = textComponents[i] + documentTitle;
				if (i < components.length - 1 || currentMedia !== null)
					documentTitle = " \u00ab " + documentTitle;
			}
		}
		if (currentMedia !== null)
			documentTitle = photoFloat.trimExtension(currentMedia.name) + documentTitle;
		
		document.title = documentTitle;
		$("#title-string	").html(title);
		if (currentMedia === null) {
			$("body").on('mouseenter', "#title-container", function() {
				if (currentAlbum.albums.length > 1) {
					$("#album-sort-arrows").show();
					if (getBooleanCookie("albumReverseSortRequested")) {
						$("#album-sort-arrows").attr("title", _t("sort-normal"));
						$("#album-sort-icon").removeAttr("title");
						$("#album-arrow-up").hide();
						$("#album-arrow-down").show();
					} else {
						$("#album-sort-arrows").attr("title", _t("sort-reverse"));
						$("#album-sort-icon").removeAttr("title");
						$("#album-arrow-up").show();
						$("#album-arrow-down").hide();
					}
				}
				if (currentAlbum.photos.length > 1 && ! (currentAlbum.path.match(byDateRegex) && currentAlbum.photos.length >= Options.big_date_folders_threshold)) {
					$("#media-sort-arrows").show();
					if (getBooleanCookie("mediaReverseSortRequested")) {
						$("#media-sort-arrows").attr("title", _t("sort-normal"));
						$("#media-sort-icon").removeAttr("title");
					} else {
						$("#media-sort-arrows").attr("title", _t("sort-reverse"));
						$("#media-sort-icon").removeAttr("title");
					}
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
						$("#album-arrow-up").show();
						$("#album-arrow-down").hide();
					} else {
						setBooleanCookie("albumReverseSortRequested", true);
						$("#album-arrow-up").hide();
						$("#album-arrow-down").show();
					}
					showAlbum("conditional");
					setOptions();
				});
			}
			if (currentAlbum.photos.length > 1) {
				$("#title").on('click', "#media-sort-arrows", function() {
					if (currentMedia !== null)
						currentMediaIndex = currentAlbum.photos.lenght - 1 - currentMediaIndex;
					currentAlbum.photo = currentAlbum.photos.reverse();
					
					if (getBooleanCookie("mediaReverseSortRequested")) {
						setBooleanCookie("mediaReverseSortRequested", false);
						$("#media-arrow-up").show();
						$("#media-arrow-down").hide();
					} else {
						setBooleanCookie("mediaReverseSortRequested", true);
						$("#media-arrow-up").hide();
						$("#media-arrow-down").show();
					}
					showAlbum("conditional");
					setOptions();
				});
			}
		}
		if (getBooleanCookie("albumReverseSortRequested")) {
			$("#album-arrow-up").hide();
			$("#album-arrow-down").show();
		} else {
			$("#album-arrow-up").show();
			$("#album-arrow-down").hide();
		}
		if (getBooleanCookie("mediaReverseSortRequested")) {
			$("#media-arrow-up").hide();
			$("#media-arrow-down").show();
		} else {
			$("#media-arrow-up").show();
			$("#media-arrow-down").hide();
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
								"\" src=\"" +  thumbHash;
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
						imageString += 			"width: " + Options.album_thumb_size + "px;";
						imageString += 			" height: " + Options.album_thumb_size + "px;";
						if (! Options.albums_slide_style)
							imageString +=		" background-color: " + Options.album_button_background_color + ";";
						imageString += 			"\"";
						imageString += ">";
						imageString += "</div>";
						image = $(imageString);
						link.append(image);
						subalbums.push(link);
						(function(theContainer, theAlbum, theImage, theLink) {
							photoFloat.pickRandomPhoto(theAlbum, theContainer, function(randomAlbum, randomPhoto, originalAlbum) {
								var distance = 0;
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
								var htmlText = "<img " +
										"title=\"" + randomPhoto.albumName.substr(7) + "\"" +
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
			$("#photo-view").hide();
			$("#video-box-inner").empty();
			$("#video-box").hide();
			$("#thumbs").show();
			
			if (currentAlbum.path == Options.folders_string) {
				$("#folders-view-container").hide();
				$("#day-view-container").show();
				$("#day-view").attr("href", "#!/" + Options.by_date_string);
			}
			else if (currentAlbum.path == Options.by_date_string) {
				$("#folders-view-container").show();
				$("#day-view-container").hide();
				$("#folders-view").attr("href", "#!/" + Options.folders_string);
			}
			$("#powered-by").show();
		} else {
			if (currentAlbum.photos.length == 1)
				$("#thumbs").hide();
			else
				$("#thumbs").show();
			$("#powered-by").hide();
		}
		$("#title").width($(window).width() - $("#buttons-container").width());
		setTimeout(scrollToThumb, 1);
	}
	function getDecimal(fraction) {
		if (fraction[0] < fraction[1])
			return fraction[0] + "/" + fraction[1];
		return (fraction[0] / fraction[1]).toString();
	}
	function scaleImageFullscreen() {
		var image, bottom;
		image = $("#photo");
		if (image.get(0) === this) {
			$(window).unbind("resize", scaleVideoNormal);
			$(window).unbind("resize", scaleVideoFullscreen);
			$(window).unbind("resize", scaleImageNormal);
			$(window).bind("resize", scaleImageFullscreen);
		}
		
		$("#photo-view").css("top", "0");
		$("#photo-view").css("height", "100%");
		$("#photo-view").css("bottom", 0);
		container = $(window);
		if (image.css("width") !== "100%" && image.attr("ratio") > container.width() / container.height()) {
			image.css("width", "100%").css("height", "auto");
			bottom = ((container.height() - image.height()) / 2).toString() + "px";
		}
		else if (image.css("height") !== "100%") {
			bottom = "0";
			image.css("height", "100%").css("width", "auto");
		}
		image.css("position", "absolute").css("bottom", bottom);
		
		$("#photo-bar").css("bottom", bottom);
	}
	function scaleImageNormal() {
		var image, imageBottom, container, containerBottom, bottomNumber, bottomBar, containerHeight;
		image = $("#photo");
		if (image.get(0) === this) {
			$(window).unbind("resize", scaleVideoNormal);
			$(window).unbind("resize", scaleVideoFullscreen);
			$(window).bind("resize", scaleImageNormal);
			$(window).unbind("resize", scaleImageFullscreen);
		}
		container = $("#photo-view");
		container.css("height", "");
		containerHeight = (window.innerHeight - $("#album-view").outerHeight(true)) - $("#title").outerHeight(true);
		if (image.css("width") !== "100%" && image.attr("ratio") > container.width() / container.height()) {
			imageBottom = ((containerHeight - image.height()) / 2) + "px";
			image.css("width", "100%").css("height", "auto").css("bottom", imageBottom);
			$("#photo-bar").css("bottom", imageBottom);
		}
		else if (image.css("height") !== "100%") {
			image.css("height", "100%").css("width", "auto").css("bottom", 0);
			$("#photo-bar").css("bottom", 0);
		}
		if (! $("#album-view").is(":visible"))
			container.css("bottom", "0");
		else
			container.css("bottom", $("#album-view").outerHeight(true) + "px");
		container.css("top", ($("#title").outerHeight(true)) + "px");
		$("#title").width($(window).width() - $("#buttons-container").width());
	}
	function scaleVideoFullscreen() {
		var video, container;
		$("#video");
		video = $("#video");
		container = $(window);
		if (video.get(0) === this) {
			$(window).unbind("resize", scaleVideoNormal);
			$(window).bind("resize", scaleVideoFullscreen);
			$(window).unbind("resize", scaleImageNormal);
			$(window).unbind("resize", scaleImageFullscreen);
		}
		if (video.attr("width") > container.width() && video.attr("ratio") > container.width() / container.height()) {
			var height = container.width() / video.attr("ratio");
			video.css("width", container.width()).
				css("height", height).
				parent().
					css("height", height).
					css("margin-top", - height / 2).
					css("top", "50%");
		}
		else if (video.attr("height") > container.height() && video.attr("ratio") < container.width() / container.height())
			video.css("height", container.height()).
				css("width", container.height() * video.attr("ratio")).
				parent().
					css("height", "100%").
					css("margin-top", "0").
					css("top", "0");
		else
			video.css("height", "").css("width", "").
				parent().
					css("height", video.attr("height")).
					css("margin-top", - video.attr("height") / 2).
					css("top", "50%");

		$("#title").width($(window).width() - $("#buttons-container").width());
	}
	function scaleVideoNormal() {
		var video, container;
		video = $("#video");
		container = $("#photo-view")
		if (video.get(0) === this) {
			$(window).bind("resize", scaleVideoNormal);
			$(window).unbind("resize", scaleVideoFullscreen);
			$(window).unbind("resize", scaleImageNormal);
			$(window).unbind("resize", scaleImageFullscreen);
		}
		if (video.attr("width") > container.width() && video.attr("ratio") > container.width() / container.height()) {
			var height = container.width() / video.attr("ratio");
			video.css("width", container.width()).
				css("height", height).
				parent().
					css("height", height).
					css("margin-top", - height / 2).
					css("top", "50%");
		}
		else if (video.attr("height") > container.height() && video.attr("ratio") < container.width() / container.height())
			video.css("height", container.height()).
				css("width", container.height() * video.attr("ratio")).
				parent().
					css("height", "100%").
					css("margin-top", "0").
					css("top", "0");
		else
			video.css("height", "").css("width", "").
				parent().
					css("height", video.attr("height")).
					css("margin-top", - video.attr("height") / 2).
					css("top", "50%");
		$("#title").width($(window).width() - $("#buttons-container").width());
	}
	function showMedia(album) {
		var width, height, photoSrc, videoSrc, previousMedia, nextMedia, nextLink, text, mediaOrientation, thumbnailSize, j;
		var maxSize, maxSizeSet, mediaMaxSize, mediaMinSize, imageRatio, windowMaxSize, windowMinSize, reducedMinSize, reducedMaxSize;
		var windowWidth, windowHeight, windowOrientation;
		width = currentMedia.size[0];
		height = currentMedia.size[1];

		windowWidth = $(window).width();
		windowHeight = $(window).height();
		if (windowWidth > windowHeight)
			windowOrientation = "landscape";
		else
			windowOrientation = "portrait";
		windowMaxSize = Math.max(windowWidth, windowHeight);
		windowMinSize = Math.min(windowWidth, windowHeight);


		if (width > height)
			mediaOrientation = "landscape";
		else
			mediaOrientation = "portrait";
			
		mediaMaxSize = Math.max(width, height);
		mediaMinSize = Math.min(width, height);
		imageRatio = mediaMaxSize / mediaMinSize;
		
		if (fullScreenStatus) {
			maxSize = Options.reduced_sizes[0];
			maxSizeSet = true;
		}
		if (! maxSizeSet) {
			maxSize = Options.reduced_sizes[0];
			for (var i = 0; i < Options.reduced_sizes.length; i++) {
				reducedMinSize = Options.reduced_sizes[i] / imageRatio;
				reducedMaxSize = Options.reduced_sizes[i];
				if (mediaOrientation == windowOrientation &&
						(reducedMinSize < windowMinSize && reducedMaxSize < windowMaxSize) ||
					mediaOrientation !== windowOrientation &&
						(reducedMinSize < windowMaxSize && reducedMaxSize < windowMinSize))
					break;
				maxSize = Options.reduced_sizes[i];
				maxSizeSet = true;
			}
		}
		
		if (currentMedia.mediaType == "video") {
			$("#video-box-inner").empty();
			if (! Modernizr.video) {
				$('<div id="video-unsupported"><p>Sorry, your browser doesn\'t support the HTML5 &lt;video&gt; element!</p><p>Here\'s a <a href="http://caniuse.com/video">list of which browsers do</a>.</p></div>').appendTo('#video-box-inner');
			}
			else if (! Modernizr.video.h264) {
				$('<div id="video-unsupported"><p>Sorry, your browser doesn\'t support the H.264 video format!</p></div>').appendTo('#video-box-inner');
			} else {
				if (fullScreenStatus) {
					$(window).unbind("resize", scaleVideoNormal);
					$(window).bind("resize", scaleVideoFullscreen);
					$(window).unbind("resize", scaleImageNormal);
					$(window).unbind("resize", scaleImageFullscreen);
				} else {
					$(window).bind("resize", scaleVideoNormal);
					$(window).unbind("resize", scaleVideoFullscreen);
					$(window).unbind("resize", scaleImageNormal);
					$(window).unbind("resize", scaleImageFullscreen);
				}
				if (fullScreenStatus) {
					videoSrc = currentMedia.albumName;
				} else {
					videoSrc = photoFloat.videoPath(currentAlbum, currentMedia);
				}
				$('<video/>', { id: 'video', controls: true }).appendTo('#video-box-inner')
					.attr("width", width).attr("height", height).attr("ratio", currentMedia.size[0] / currentMedia.size[1])
					.attr("src", videoSrc)
					.attr("alt", currentMedia.name)
					//~ .on('loadstart', scaleVideo);
					;
			}
			$("head").append("<link rel=\"video_src\" href=\"" + videoSrc + "\" />");
			$("#video-box-inner").css('height', height + 'px').css('margin-top', - height / 2);
			if (fullScreenStatus)
				$("#photo-view").load(scaleVideoFullscreen);
			else
				$("#photo-view").load(scaleVideoNormal);
			$("#photo-box").hide();
			$("#video-box").show();
		} else {
			if (width > height) {
				height = Math.round(height * maxSize / width);
				width = maxSize;
			} else {
				width = Math.round(width * maxSize / height);
				height = maxSize;
			}
			if (fullScreenStatus) {
				$(window).unbind("resize", scaleVideoNormal);
				$(window).unbind("resize", scaleVideoFullscreen);
				$(window).unbind("resize", scaleImageNormal);
				$(window).bind("resize", scaleImageFullscreen);
			} else {
				$(window).unbind("resize", scaleVideoNormal);
				$(window).unbind("resize", scaleVideoFullscreen);
				$(window).bind("resize", scaleImageNormal);
				$(window).unbind("resize", scaleImageFullscreen);
			}
			photoSrc = photoFloat.photoPath(currentAlbum, currentMedia, maxSize);
			$("#photo")
				.attr("width", width).attr("height", height).attr("ratio", currentMedia.size[0] / currentMedia.size[1])
				.attr("src", photoSrc)
				.attr("alt", currentMedia.name)
				.attr("title", currentMedia.date);
			if (fullScreenStatus)
				$("#photo").load(scaleImageFullscreen);
			else
				$("#photo").load(scaleImageNormal);
			$("head").append("<link rel=\"image_src\" href=\"" + photoSrc + "\" />");
			$("#video-box-inner").empty();
			$("#video-box").hide();
			$("#photo-box").show();
			if (! Options.persistent_metadata) {
				$("#metadata").hide();
				$("#metadata-show").show();
				$("#metadata-hide").hide();
			}
		}
		if (currentAlbum.photos.length > 1) {
			j = currentMediaIndex;
			do {
				j == 0 ? j = currentAlbum.photos.length - 1: j --;
				previousMedia = currentAlbum.photos[j];
			} while (previousMedia.byDateName == currentAlbum.photos[currentMediaIndex].byDateName);
			j = currentMediaIndex;
			do {
				j == currentAlbum.photos.length - 1 ? j = 0 : j ++;
				nextMedia = currentAlbum.photos[j];
			} while (nextMedia.byDateName == currentAlbum.photos[currentMediaIndex].byDateName);
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
		if (currentAlbum.path == photoFloat.photoFoldersAlbum(currentMedia)) {
			$("#folders-view-container").hide();
			$("#day-view-container").show();
		}
		else {
			$("#folders-view-container").show();
			$("#day-view-container").hide();
		}
		
		thumbnailSize = Options.media_thumb_size;
		if (currentAlbum.photos.length == 1) {
			$("#next").hide();
			$("#back").hide();
			$(".next-media").removeAttr("href");
			$("#next").removeAttr("href");
			$("#back").removeAttr("href");
			$("#photo-view").addClass("no-bottom-space");
			$("#album-view").addClass("no-bottom-space");
		} else {
			nextLink = "#!/" + photoFloat.photoHash(currentAlbum, nextMedia);
			$("#next").show();
			$("#back").show();
			$(".next-media").attr("href", nextLink);
			$("#next").attr("href", nextLink);
			$("#back").attr("href", "#!/" + photoFloat.photoHash(currentAlbum, previousMedia));
			$("#photo-view").removeClass("no-bottom-space");
			$("#album-view").removeClass("no-bottom-space");
			$("#photo-view").css("bottom", (thumbnailSize + 15).toString() + "px");
			$("#album-view").css("height", (thumbnailSize + 20).toString() + "px");
			$("#album-view").addClass("photo-view-container");
			$("#album-view.photo-view-container").css("height", (thumbnailSize + 22).toString() + "px");
		}
		$("#original-link").attr("target", "_blank").attr("href", photoFloat.originalPhotoPath(currentMedia));
		
		$("#folders-view").attr("href", "#!/" + PhotoFloat.cachePath(currentMedia.foldersAlbum) + "/" + PhotoFloat.cachePath(currentMedia.name));
		$("#day-view").attr("href", "#!/" + PhotoFloat.cachePath(currentMedia.dayAlbum) + "/" + PhotoFloat.cachePath(currentMedia.name));
		
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
		$("#metadata").html(text);
		
		$("#subalbums").hide();
		$("#photo-view").show();
	}
	
	function setOptions() {
		var albumThumbnailSize, mediaThumbnailSize;
		albumThumbnailSize = Options.album_thumb_size;
		mediaThumbnailSize = Options.media_thumb_size;
		$("body").css("background-color", Options.background_color);
		$("#day-view-container").css("color", Options.switch_button_color);
		$("#day-view-container").hover(function() {
			//mouse over
			$(this).css("color", Options.switch_button_color_hover);
		}, function() {
			//mouse out
			$(this).css("color", Options.switch_button_color);
		});
		$("#folders-view-container").css("color", Options.switch_button_color);
		$("#folders-view-container").hover(function() {
			//mouse over
			$(this).css("color", Options.switch_button_color_hover);
		}, function() {
			//mouse out
			$(this).css("color", Options.switch_button_color);
		});
		$("#day-view-container").css("background-color", Options.switch_button_background_color);
		$("#day-view-container").hover(function() {
			//mouse over
			$(this).css("background-color", Options.switch_button_background_color_hover);
		}, function() {
			//mouse out
			$(this).css("background-color", Options.switch_button_background_color);
		});
		$("#folders-view-container").css("background-color", Options.switch_button_background_color);
		$("#folders-view-container").hover(function() {
			//mouse over
			$(this).css("background-color", Options.switch_button_background_color_hover);
		}, function() {
			//mouse out
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
		$(".album-button").css("width", albumThumbnailSize.toString() + "px");
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
		
		if (currentMedia === null || typeof currentMedia === "object")
			setTitle();
		if (currentMedia !== null || currentAlbum !== null && ! currentAlbum.albums.length && currentAlbum.photos.length == 1)
		{
			if (currentMedia === null) {
				currentMedia = currentAlbum.photos[0];
				currentMediaIndex = 1;
			}
			showMedia(currentAlbum);
		}
		else {
			$("#folders-view-container").hide();
			$("#day-view-container").hide();
		}
		populateAlbum = previousAlbum !== currentAlbum || previousMedia !== currentMedia;
		showAlbum(populateAlbum);
		if (currentMedia !== null || ! Options.show_media_names_below_thumbs_in_albums)
			$(".media-caption").hide();
		else
			$(".media-caption").show();
		
		setOptions();
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
					
					if (getBooleanCookie("albumReverseSortRequested") === null)
						setBooleanCookie("albumReverseSortRequested", Options.default_album_reverse_sort);
					if (getBooleanCookie("mediaReverseSortRequested") === null)
						setBooleanCookie("mediaReverseSortRequested", Options.default_media_reverse_sort);
					
					byDateRegex = "^" + Options.by_date_string + "\/[1-2][0-9]{1,3}";
					
					callback(location.hash, hashParsed, die);
				},
				error: function(jqXHR, textStatus, errorThrown) {
					if (errorThrown == "Not Found" && ! cacheSubDir)
						getOptions(Options.server_cache_path, callback);
					else {
						$("#album-view").fadeOut(200);
						$("#photo-view").fadeOut(200);
						$("#album-view").fadeIn(3500);
						$("#photo-view").fadeIn(3500);
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
			return true;
		if (e.keyCode === 39) {
			window.location.href = $("#next").attr("href");
			return false;
		} else if (e.keyCode === 37) {
			window.location.href = $("#back").attr("href");
			return false;
		}
		return true;
	});
	$(document).mousewheel(function(event, delta) {
		
		if (currentMedia === null || $("#next").attr('href') === undefined)
			return true;
		if (delta < 0) {
			window.location.href = $("#next").attr("href");
			return false;
		} else if (delta > 0) {
			window.location.href = $("#back").attr("href");
			return false;
		}
		return true;
	});
	
	$("#photo-view").mouseenter(function() {
		$("#photo-links").stop().fadeTo("slow", 0.50).css("display", "inline");
	});
	$("#photo-view").mouseleave(function() {
		$("#photo-links").stop().fadeOut("slow");
	});
	$("#next, #back").mouseenter(function() {
		$(this).stop().fadeTo("slow", 1);
	});
	$("#next, #back").mouseleave(function() {
		$(this).stop().fadeTo("slow", 0.35);
	});
	if ($.support.fullscreen) {
		$("#fullscreen").show();
		$("#fullscreen").click(function(e) {
			e.preventDefault();
			$("#photo-view").fullScreen({callback: function(isFullscreen) {
				if (isFullscreen) {
					$("#photo-view").css("position", "initial");
					if (currentMedia.mediaType == "video") {
						$(window).unbind("resize", scaleVideoNormal);
						$(window).bind("resize", scaleVideoFullscreen);
						$(window).unbind("resize", scaleImageNormal);
						$(window).unbind("resize", scaleImageFullscreen);
					} else {
						$(window).unbind("resize", scaleVideoNormal);
						$(window).unbind("resize", scaleVideoFullscreen);
						$(window).unbind("resize", scaleImageNormal);
						$(window).bind("resize", scaleImageFullscreen);
					}
				}
				else {
					$("#photo-view").css("position", "absolute");
					if (currentMedia.mediaType == "video") {
						$(window).bind("resize", scaleVideoNormal);
						$(window).unbind("resize", scaleVideoFullscreen);
						$(window).unbind("resize", scaleImageNormal);
						$(window).unbind("resize", scaleImageFullscreen);
					} else {
						$(window).unbind("resize", scaleVideoNormal);
						$(window).unbind("resize", scaleVideoFullscreen);
						$(window).bind("resize", scaleImageNormal);
						$(window).unbind("resize", scaleImageFullscreen);
					}
				}
				maxSizeSet = false;
				fullScreenStatus = isFullscreen;
				$("#enter-fullscreen").toggle();
				$("#exit-fullscreen").toggle();
				showMedia(currentAlbum);
			}});
		});
	}
	$("#metadata-show").click(function() {
		$("#metadata-show").hide();
		$("#metadata-hide").show();
		$("#metadata").stop()
			.css("height", 0)
			.css("padding-top", 0)
			.css("padding-bottom", 0)
			.show()
			.animate({ height: $("#metadata > table").height(), paddingTop: 3, paddingBottom: 3 }, "slow", function() {
				$(this).css("height", "auto");
			});
	});
	$("#metadata-hide").click(function() {
		$("#metadata-show").show();
		$("#metadata-hide").hide();
		$("#metadata").stop()
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
