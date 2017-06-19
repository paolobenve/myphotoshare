var windowWidth = $(window).width();
var windowHeight = $(window).height();
var windowOrientation;
if (windowWidth > windowHeight)
	windowOrientation = "landscape";
else
	windowOrientation = "portrait";
windowMaxSize = Math.max(windowWidth, windowHeight);
windowMinSize = Math.min(windowWidth, windowHeight);

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
	
	currentAlbum = null;
	var currentMedia = null;
	var currentMediaIndex = -1;
	var previousAlbum = null;
	var previousMedia = null;
	var originalTitle = document.title;
	var photoFloat = new PhotoFloat();
	var maxSizeSet = false;
	bydateString = "_by_date";
	bydateStringWithTrailingDash = bydateString + "-";
	foldersString = "_folders";
	foldersStringWithTrailingDash = foldersString + "-";
	
	
	/* Displays */
	
	function language() {
		var userLang = navigator.language || navigator.userLanguage;
		return userLang.split('-')[0];
	}
	
	function translate() {
		
		if($('.translation-' + language()).length) {
			$('.translation').removeClass('translation-active');
			$('.translation-' + language()).addClass('translation-active');
		} else {
			$('.translation-en').addClass('translation-active');
		}
	}
	
	function translationsToTranslatedString(translations) {
		translationsLines = translations.split("\n");
		for (var i in translationsLines) {
			if (translationsLines[i].indexOf("translation-active") != -1)
				return translationsLines[i].replace(/<\/?[^>]+(>|$)/g, "").trim();
		}
	}


	function setTitle() {
		var title = "", documentTitle = "", last = "", components, i;
		var originalTitle = translationsToTranslatedString($("#title-translation").html());
		var documentTitleAdd = "";
		
		if (! currentAlbum.path.length)
			components = [originalTitle];
		else {
			components = currentAlbum.path.split("/");
			components.unshift(originalTitle);
		}
		if (currentMedia !== null)
			documentTitle += photoFloat.trimExtension(currentMedia.name);
		for (i = 0; i < components.length; ++i) {
			if (i)
				last += "/" + components[i];
			if (i != 1 || components[i] != foldersString) {
				if (i < components.length - 1 || currentMedia !== null)
					title += "<a href=\"#!/" + (i ? photoFloat.cachePath(last.substring(1)) : "") + "\">";
				if (i == 1 && components[i] == bydateString)
					components[i] = translationsToTranslatedString($("#by-date-translation").html());
				title += components[i];
				if (i < components.length - 1 || currentMedia !== null)
					title += "</a>";
				
				if (i || currentMedia !== null)
					documentTitle += " \u00ab ";
				documentTitle += components[components.length - 1 - i];
			}
			if ((i < components.length - 1 || currentMedia !== null) && (i == components.length - 1 || components[i + 1] != foldersString))
				title += " &raquo; ";
		}
		if (currentMedia !== null)
			title += "<span id=\"photo-name\">" + photoFloat.trimExtension(currentMedia.name) + "</div>";
		
		$("#title").html(title);
		document.title = documentTitle;
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
		var i, link, image, photos, thumbsElement, subalbums, subalbumsElement, hash, thumbHash;
		if (currentMedia === null && previousMedia === null)
			$("html, body").stop().animate({ scrollTop: 0 }, "slow");
		if (populate) {
			photos = [];
			for (i = 0; i < currentAlbum.photos.length; ++i) {
				hash = photoFloat.photoHash(currentAlbum, currentAlbum.photos[i]);
				thumbHash = photoFloat.photoPath(currentAlbum, currentAlbum.photos[i], 150, true);
				if (thumbHash.indexOf(bydateStringWithTrailingDash) === 0) {
					thumbHash =
						PhotoFloat.cachePath(currentAlbum.photos[i].completeName.substring(0, currentAlbum.photos[i].completeName.length - currentAlbum.photos[i].name.length - 1)) +
						"/" +
						PhotoFloat.cachePath(currentAlbum.photos[i].name);
				}
				link = $("<a href=\"#!/" + hash + "\"></a>");
				image = $("<div class=\"thumb-container\">" +
							"<img title=\"" + currentAlbum.photos[i].name +
							"\" alt=\"" + photoFloat.trimExtension(currentAlbum.photos[i].name) +
							"\" src=\"" + thumbHash +
							"\" height=\"150\" width=\"150\" />" +
							"<div class=\"thumb-caption\">" +
							currentAlbum.photos[i].name.replace(/ /g, "</span> <span style=\"white-space: nowrap;\">") +
							"</div>" +
							"</div>");

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
			
			if (currentMedia === null) {
				subalbums = [];
				for (i = 0; i < currentAlbum.albums.length; ++i) {
					link = $("<a href=\"#!/" + photoFloat.albumHash(currentAlbum.albums[i]) + "\"></a>");
					var imageTextAdd = currentAlbum.albums[i].path;
					imageTextAdd = imageTextAdd.replace(bydateString, $("#by-date-translation").html());
					imageTextAdd = imageTextAdd.replace(foldersString, $("#folders-translation").html());
					image = $("<div title=\"" + currentAlbum.albums[i].date + "\" class=\"album-button\">" +
								imageTextAdd +
								"</div>");
					link.append(image);
					subalbums.push(link);
					(function(theContainer, theAlbum, theImage, theLink) {
						photoFloat.albumPhoto(theAlbum, function(album, photo) {
							theImage.css("background-image", "url(" + photoFloat.photoPath(album, photo, 150, true) + ")");
						}, function error() {
							theContainer.albums.splice(currentAlbum.albums.indexOf(theAlbum), 1);
							theLink.remove();
							subalbums.splice(subalbums.indexOf(theLink), 1);

						});
					})(currentAlbum, currentAlbum.albums[i], image, link);
				}
				subalbumsElement = $("#subalbums");
				subalbumsElement.empty();
				subalbumsElement.append.apply(subalbumsElement, subalbums);
				subalbumsElement.insertBefore(thumbsElement);
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
		} else {
			if (currentAlbum.photos.length == 1)
				$("#thumbs").hide();
			else
				$("#thumbs").show();
		}
		setTimeout(scrollToThumb, 1);
		translate();
	}
	function getDecimal(fraction) {
		if (fraction[0] < fraction[1])
			return fraction[0] + "/" + fraction[1];
		return (fraction[0] / fraction[1]).toString();
	}
	function scaleImageFullscreen() {
		var image;
		image = $("#photo");
		if (image.get(0) === this) {
			$(window).unbind("resize", scaleImageNormal);
			$(window).bind("resize", scaleImageFullscreen);
		}
		scaleImage($(window), image);
	}
	function scaleImageNormal() {
		var image;
		image = $("#photo");
		if (image.get(0) === this) {
			$(window).unbind("resize", scaleImageFullscreen);
			$(window).bind("resize", scaleImageNormal);
		}
		scaleImage($("#photo-view"), image);
	}
	function scaleImage(container, image) {
		if (image.css("width") !== "100%" && container.height() * image.attr("ratio") > container.width())
			image.css("width", "100%").css("height", "auto").css("position", "absolute").css("bottom", 0);
		else if (image.css("height") !== "100%")
			image.css("height", "100%").css("width", "auto").css("position", "").css("bottom", "");
	}
	function scaleVideo() {
		var video, container;
		video = $("#video");
		if (video.get(0) === this)
			$(window).bind("resize", scaleVideo);
		container = $("#photo-view");
		if (video.attr("width") > container.width() && container.height() * video.attr("ratio") > container.width())
			video.css("width", container.width()).css("height", container.width() / video.attr("ratio")).parent().css("height", container.width() / video.attr("ratio")).css("margin-top", - container.width() / video.attr("ratio") / 2).css("top", "50%");
		else if (video.attr("height") > container.height() && container.height() * video.attr("ratio") < container.width())
			video.css("height", container.height()).css("width", container.height() * video.attr("ratio")).parent().css("height", "100%").css("margin-top", "0").css("top", "0");
		else
			video.css("height", "").css("width", "").parent().css("height", video.attr("height")).css("margin-top", - video.attr("height") / 2).css("top", "50%");
	}
	function showMedia(album, fullscreen = false) {
		var width, height, photoSrc, videoSrc, previousMedia, nextMedia, nextLink, text, mediaOrientation;
		width = currentMedia.size[0];
		height = currentMedia.size[1];
		if (width > height)
			mediaOrientation = "landscape";
		else
			mediaOrientation = "portrait";
			
		mediaMaxSize = Math.max(width, height);
		mediaMinSize = Math.min(width, height);
		imageRatio = mediaMaxSize / mediaMinSize;
		
		if (fullscreen) {
			maxSize = album.thumbSizes[0][0];
			maxSizeSet = true;
		}
		if (! maxSizeSet) {
			maxSize = album.thumbSizes[0][0];
			for (var i = 0; i < album.thumbSizes.length; i++)
				if (! album.thumbSizes[i][1]) {
					thumbnailMinSize = album.thumbSizes[i][0] / imageRatio;
					thumbnailMaxSize = album.thumbSizes[i][0];
					if (mediaOrientation == windowOrientation &&
							(thumbnailMinSize < windowMinSize && thumbnailMaxSize < windowMaxSize) ||
						mediaOrientation !== windowOrientation &&
							(thumbnailMinSize < windowMaxSize && thumbnailMaxSize < windowMinSize))
					//~ if (maxSizeSet && album.thumbSizes[i][0] < Math.max($(window).width(), $(window).height()))
						break;
					maxSize = album.thumbSizes[i][0];
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
				$(window).unbind("resize", scaleVideo);
				$(window).unbind("resize", scaleImageNormal);
				$(window).unbind("resize", scaleImageFullscreen);
				videoSrc = photoFloat.videoPath(currentAlbum, currentMedia);
				$('<video/>', { id: 'video', controls: true }).appendTo('#video-box-inner')
					.attr("width", width).attr("height", height).attr("ratio", currentMedia.size[0] / currentMedia.size[1])
					.attr("src", videoSrc)
					.attr("alt", currentMedia.name)
					.on('loadstart', scaleVideo);
			}
			$("head").append("<link rel=\"video_src\" href=\"" + videoSrc + "\" />");
			$("#video-box-inner").css('height', height + 'px').css('margin-top', - height / 2);
			$("#photo-box").hide();
			$("#video-box").show();
		} else {
			if (width > height) {
				height = height / width * maxSize;
				width = maxSize;
			} else {
				width = width / height * maxSize;
				height = maxSize;
			}
			$(window).unbind("resize", scaleVideo);
			$(window).unbind("resize", scaleImageNormal);
			photoSrc = photoFloat.photoPath(currentAlbum, currentMedia, maxSize, false);
			$("#photo")
				.attr("width", width).attr("height", height).attr("ratio", currentMedia.size[0] / currentMedia.size[1])
				.attr("src", photoSrc)
				.attr("alt", currentMedia.name)
				.attr("title", currentMedia.date);
			if (fullscreen)
				$("#photo").load(scaleImageFullscreen)
			else
				$("#photo").load(scaleImageNormal)
			$("head").append("<link rel=\"image_src\" href=\"" + photoSrc + "\" />");
			$("#video-box-inner").empty();
			$("#video-box").hide();
			$("#photo-box").show();
			$("#metadata").hide();
			$("#metadata-show").show();
			$("#metadata-hide").hide();
		}
		if (currentAlbum.photos.length > 1) {
			var i = currentMediaIndex;
			do {
				i == 0 ? i = currentAlbum.photos.length - 1: i --;
				previousMedia = currentAlbum.photos[i];
			} while (previousMedia.byDateName == currentAlbum.photos[currentMediaIndex].byDateName);
			i = currentMediaIndex;
			do {
				i == currentAlbum.photos.length - 1 ? i = 0 : i ++
				nextMedia = currentAlbum.photos[i];
			} while (nextMedia.byDateName == currentAlbum.photos[currentMediaIndex].byDateName);
			if (nextMedia.mediaType == "video") {
				$.preloadImages(photoFloat.videoPath(currentAlbum, nextMedia));
			} else {
				$.preloadImages(photoFloat.photoPath(currentAlbum, nextMedia, maxSize, false))
			}
			if (previousMedia.mediaType == "video") {
				$.preloadImages(photoFloat.videoPath(currentAlbum, previousMedia));
			} else {
				$.preloadImages(photoFloat.photoPath(currentAlbum, previousMedia, maxSize, false));
			}
		}
		if (currentMedia.mediaType != "video") {
			if (currentAlbum.path == photoFloat.photoFoldersAlbum(currentMedia)) {
				$("#folders-view-container").hide();
				$("#day-view-container").show();
			}
			else {
				$("#folders-view-container").show();
				$("#day-view-container").hide();
			}
			$("#title").width($(window).width() - $("#buttons-container").width() - em2px("#photo-name", 2) - 2 * parseInt($("#title").css("padding")));
		}
		
		if (currentAlbum.photos.length == 1) {
			$("#next").hide();
			$("#back").hide();
			$("#next-photo").removeAttr("href");
			$("#next").removeAttr("href");
			$("#back").removeAttr("href");
			$("#photo-view").addClass("no-bottom-space");
			$("#album-view").addClass("no-bottom-space");
		} else {
			nextLink = "#!/" + photoFloat.photoHash(currentAlbum, nextMedia);
			$("#next").show();
			$("#back").show();
			$("#next-photo").attr("href", nextLink);
			$("#next").attr("href", nextLink);
			$("#back").attr("href", "#!/" + photoFloat.photoHash(currentAlbum, previousMedia));
			$("#photo-view").removeClass("no-bottom-space");
			$("#album-view").removeClass("no-bottom-space");
		}
		$("#original-link").attr("target", "_blank").attr("href", photoFloat.originalPhotoPath(currentMedia));
		if (currentMedia.mediaType != "video") {
			$("#folders-view").attr("href", "#!/" + PhotoFloat.cachePath(currentMedia.foldersAlbum) + "/" + PhotoFloat.cachePath(currentMedia.name));
			$("#day-view").attr("href", "#!/" + PhotoFloat.cachePath(currentMedia.dayAlbum) + "/" + PhotoFloat.cachePath(currentMedia.name));
		}
		
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
		
		$("#album-view").addClass("photo-view-container");
		$("#subalbums").hide();
		$("#photo-view").show();
	}
	
	function em2px(selector, em) {
		var emSize = parseFloat($(selector).css("font-size"));
		return (em * emSize);
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
		undie();
		$("#loading").hide();
		if (album === currentAlbum && photo === currentMedia)
			return;
		if (album != currentAlbum)
			currentAlbum = null;
		if (currentAlbum && currentAlbum.path.indexOf(bydateString) === 0 && photo !== null) {
			previousAlbum = currentAlbum;
			album = currentAlbum;
			previousMedia = photo;
			currentMedia = photo;
			currentMediaIndex = photoIndex;
		}
		else {
			previousAlbum = currentAlbum;
			previousMedia = currentMedia;
			currentAlbum = album;
			currentMedia = photo;
			currentMediaIndex = photoIndex;
		}
		
		setTitle();
		if (currentMedia !== null)
			showMedia(currentAlbum);
		var populateAlbum = previousAlbum !== currentAlbum || previousMedia !== currentMedia;
		showAlbum(populateAlbum);
		if (currentMedia !== null)
			$(".thumb-caption").hide();
		else
			$(".thumb-caption").show();
		
	}
	
	/* Event listeners */
	
	$(window).hashchange(function() {
		$("#loading").show();
		$("link[rel=image_src]").remove();
		$("link[rel=video_src]").remove();
		photoFloat.parseHash(location.hash, hashParsed, die);
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
	$("#photo-box").mouseenter(function() {
		$("#photo-links").stop().fadeTo("slow", 0.50).css("display", "inline");
	});
	$("#photo-box").mouseleave(function() {
		$("#photo-links").stop().fadeOut("slow");
	});
	$("#next, #back").mouseenter(function() {
		$(this).stop().fadeTo("slow", 1);
	});
	$("#next, #back").mouseleave(function() {
		$(this).stop().fadeTo("slow", 0.35);
	});
	if ($.support.fullscreen) {
		$("#fullscreen-divider").show();
		$("#fullscreen").show().click(function() {
			$("#photo").fullScreen({callback: function(isFullscreen) {
				maxSizeSet = false;
				showMedia(currentAlbum, isFullscreen);
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
	
	translate();

});
