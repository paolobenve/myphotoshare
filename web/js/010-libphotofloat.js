(function() {
	/* constructor */
	function PhotoFloat() {
		this.albumCache = [];
		this.geotaggedPhotosFound = null;
	}

	/* public member functions */
	PhotoFloat.prototype.getAlbum = function(subalbum, callback, error) {
		var cacheKey, ajaxOptions, self;

		if (typeof subalbum.media !== "undefined" && subalbum.media !== null) {
			callback(subalbum);
			return;
		}
		if (Object.prototype.toString.call(subalbum).slice(8, -1) === "String")
			cacheKey = subalbum;
		else
			cacheKey = subalbum.cacheBase;

		if (this.albumCache.hasOwnProperty(cacheKey)) {
			callback(this.albumCache[cacheKey]);
			return;
		}
		var cacheFile = PhotoFloat.pathJoin([Options.server_cache_path, cacheKey + ".json"]);
		self = this;
		ajaxOptions = {
			type: "GET",
			dataType: "json",
			url: cacheFile,
			success: function(album) {
				var i;
				for (i = 0; i < album.albums.length; ++i)
					album.albums[i].parent = album;
				for (i = 0; i < album.media.length; ++i)
					album.media[i].parent = album;
				self.albumCache[cacheKey] = album;

				callback(album);
			}
		};
		if (typeof error !== "undefined" && error !== null) {
			ajaxOptions.error = function(jqXHR, textStatus, errorThrown) {
				error(jqXHR.status);
			};
		}
		$.ajax(ajaxOptions);
	};

	PhotoFloat.prototype.showByGpsButton = function() {
		// this function returns true if the root album has the by gps subalbum
		if (this.geotaggedPhotosFound !== null) {
			if (this.geotaggedPhotosFound) {
				$("#by-gps-view-container").show();
			}
		} else {
			self = this;
			this.getAlbum(
				Options.by_gps_string,
				function() {
					self.geotaggedPhotosFound = true;
					$("#by-gps-view-container").show();
				},
				function() {
					self.geotaggedPhotosFound = false;
				}
			);
		}
	}

	PhotoFloat.prototype.pickRandomMedia = function(subalbum, container, callback, error) {
		var nextAlbum, self;
		self = this;
		nextAlbum = function(album) {
			var index = Math.floor(Math.random() * (album.numMediaInSubTree));
			if (index >= album.media.length) {
				index -= album.media.length;
				for (var i = 0; i < album.albums.length; i ++) {
					if (index >= album.albums[i].numMediaInSubTree)
						index -= album.albums[i].numMediaInSubTree;
					else
						break;
				}
				self.getAlbum(album.albums[i], nextAlbum, error);
			} else
				callback(album, album.media[index], container, subalbum);
		};
		if (typeof subalbum.media !== "undefined" && subalbum.media !== null)
			nextAlbum(subalbum);
		else
			this.getAlbum(subalbum, nextAlbum, error);
	};

	PhotoFloat.prototype.parseHash = function(hash, callback, error) {
		// this vars are defined here and not at the beginning of the file because the options must have been read
		PhotoFloat.foldersStringWithTrailingSeparator = Options.folders_string + Options.cache_folder_separator;
		PhotoFloat.byDateStringWithTrailingSeparator = Options.by_date_string + Options.cache_folder_separator;
		PhotoFloat.byGpsStringWithTrailingSeparator = Options.by_gps_string + Options.cache_folder_separator;

		var hashParts, lastSlashPosition, slashNumber, albumHash, mediaHash = null, foldersHash = null, media = null;
		$("#error-too-many-images").hide();
		hash = PhotoFloat.cleanHash(hash);
		// count the number of slashes in hash, by date hashes have 2, folders ones 1
		if (! hash.length) {
			albumHash = Options.folders_string;
			mediaHash = null;
		} else {
			hashParts = hash.split("/");
			slashNumber = hashParts.length -1;
			lastSlashPosition = hash.lastIndexOf("/");

			if (slashNumber == 1) {
				// folders hash: album and media
				albumHash = hashParts[0];
				mediaHash = hashParts[1];
			} else if (slashNumber == 0) {
				// folders or by date hash: album only
				albumHash = hash;
			} else if (slashNumber == 2) {
				// by date hash: by date album, folders album, media
				albumHash = hashParts[0];
				mediaHash = hashParts[2];
				foldersHash = hashParts[1];
			}
		}
		if (albumHash)
			albumHash = decodeURI(albumHash);
		if (mediaHash)
			mediaHash = decodeURI(mediaHash);
		if (foldersHash)
			foldersHash = decodeURI(foldersHash);
		this.getAlbum(
			albumHash,
			function(theAlbum) {
				var i = -1;
				if (mediaHash !== null) {
					for (i = 0; i < theAlbum.media.length; ++i) {
						if (
							theAlbum.media[i].cacheBase === mediaHash &&
							(foldersHash === null || theAlbum.media[i].foldersCacheBase === foldersHash)
						) {
							media = theAlbum.media[i];
							break;
						}
					}
					if (i >= theAlbum.media.length) {
						$("#album-view").fadeOut(200);
						$("#media-view").fadeOut(200);
						$("#album-view").fadeIn(3500);
						$("#error-text-image").fadeIn(200);
						$("#error-text-image, #error-overlay, #auth-text").fadeOut(2500);
						window.location.hash = theAlbum;
						i = -1;
					}
				}
				callback(theAlbum, media, i);
			},
			error
		);
	};
	PhotoFloat.prototype.authenticate = function(password, result) {
		var ajaxOptions = {
			type: "GET",
			dataType: "text",
			url: "auth?username=photos&password=" + password,
			success: function() {
				result(true);
			},
			error: function() {
				result(false);
			}
		};
		$.ajax(ajaxOptions);
	};

	PhotoFloat.mediaHash = function(album, media) {
		return media.cacheBase;
	};
	PhotoFloat.mediaHashURIEncoded = function(album, media) {
		var hash;
		if (album.cacheBase.indexOf(PhotoFloat.byDateStringWithTrailingSeparator) === 0 || album.cacheBase.indexOf(PhotoFloat.byGpsStringWithTrailingSeparator) === 0)
			hash = PhotoFloat.pathJoin([
				encodeURIComponent(album.cacheBase),
				encodeURIComponent(media.foldersCacheBase),
				encodeURIComponent(media.cacheBase)
			]);
		else
			hash = PhotoFloat.pathJoin([
				encodeURIComponent(album.cacheBase),
				encodeURIComponent(media.cacheBase)
			]);
		return hash;
	};
	PhotoFloat.mediaHashFolder = function(album, media) {
		var hash;
		hash = media.cacheBase;
		if (hash.indexOf(PhotoFloat.byDateStringWithTrailingSeparator) === 0 || hash.indexOf(PhotoFloat.byGpsStringWithTrailingSeparator) === 0) {
			media.completeName = PhotoFloat.pathJoin([media.foldersAlbum, media.name]);
			hash = PhotoFloat.pathJoin([media.foldersAlbum.cacheBase, media.cacheBase]);
		}
		return hash;
	};
	PhotoFloat.pathJoin = function(pathArr) {
		var result = '';
		for (var i = 0; i < pathArr.length; ++i) {
			if (i < pathArr.length - 1 &&  pathArr[i] && pathArr[i][pathArr[i].length - 1] != "/")
				pathArr[i] += '/';
			if (i && pathArr[i] && pathArr[i][0] == "/")
				pathArr[i] = pathArr[i].slice(1);
			result += pathArr[i];
		}
		return result;
	};
	PhotoFloat.mediaPath = function(album, media, size) {
		var suffix = "_", hash, rootString = "root-";
		if (
			media.mediaType == "photo" ||
			media.mediaType == "video" && [Options.album_thumb_size, Options.media_thumb_size].indexOf(size) != -1
		) {
			actualSize = size;
			albumThumbSize = Options.album_thumb_size;
			mediaThumbSize = Options.media_thumb_size;
			if ((size == albumThumbSize || size == mediaThumbSize) && screenRatio > 1) {
				actualSize = Math.round(actualSize * Options.mobile_thumbnail_factor);
				albumThumbSize = Math.round(albumThumbSize * Options.mobile_thumbnail_factor);
				mediaThumbSize = Math.round(mediaThumbSize * Options.mobile_thumbnail_factor);
		  }
			suffix += actualSize.toString();
			if (size == Options.album_thumb_size) {
				suffix += "a";
				if (Options.album_thumb_type == "square")
					suffix += "s";
				else if (Options.album_thumb_type == "fit")
					suffix += "f";
			}
			else if (size == Options.media_thumb_size) {
				suffix += "t";
				if (Options.media_thumb_type == "square")
					suffix += "s";
				else if (Options.media_thumb_type == "fixed_height")
					suffix += "f";
			}
			suffix += ".jpg";
		} else if (media.mediaType == "video") {
			suffix += "transcoded_" + Options.video_transcode_bitrate + "_" + Options.video_crf + ".mp4";
		}

		hash = media.foldersCacheBase + Options.cache_folder_separator + media.cacheBase + suffix;
		if (hash.indexOf(rootString) === 0)
			hash = hash.substring(rootString.length);
		else {
			if (hash.indexOf(PhotoFloat.foldersStringWithTrailingSeparator) === 0)
				hash = hash.substring(PhotoFloat.foldersStringWithTrailingSeparator.length);
			else if (hash.indexOf(PhotoFloat.byDateStringWithTrailingSeparator) === 0)
				hash = hash.substring(PhotoFloat.byDateStringWithTrailingSeparator.length);
			else if (hash.indexOf(PhotoFloat.byGpsStringWithTrailingSeparator) === 0)
				hash = hash.substring(PhotoFloat.byGpsStringWithTrailingSeparator.length);
		}
		if (media.cacheSubdir)
			return PhotoFloat.pathJoin([Options.server_cache_path, media.cacheSubdir, hash]);
		else
			return PhotoFloat.pathJoin([Options.server_cache_path, hash]);
	};
	PhotoFloat.originalMediaPath = function(media) {
		return media.albumName;
	};
	PhotoFloat.trimExtension = function(name) {
		var index = name.lastIndexOf(".");
		if (index !== -1)
			return name.substring(0, index);
		return name;
	};
	PhotoFloat.cleanHash = function(hash) {
		while (hash.length) {
			if (hash.charAt(0) === "#")
				hash = hash.substring(1);
			else if (hash.charAt(0) === "!")
				hash = hash.substring(1);
			else if (hash.charAt(0) === "/")
				hash = hash.substring(1);
			else if (hash.substring(0, 3) === "%21")
				hash = hash.substring(3);
			else if (hash.charAt(hash.length - 1) === "/")
				hash = hash.substring(0, hash.length - 1);
			else
				break;
		}
		return hash;
	};

	/* make static methods callable as member functions */
	PhotoFloat.prototype.cacheBase = PhotoFloat.cacheBase;
	PhotoFloat.prototype.mediaHash = PhotoFloat.mediaHash;
	PhotoFloat.prototype.mediaHashURIEncoded = PhotoFloat.mediaHashURIEncoded;
	PhotoFloat.prototype.mediaHashFolder = PhotoFloat.mediaHashFolder;
	PhotoFloat.prototype.pathJoin = PhotoFloat.pathJoin;
	PhotoFloat.prototype.mediaPath = PhotoFloat.mediaPath;
	PhotoFloat.prototype.originalMediaPath = PhotoFloat.originalMediaPath;
	PhotoFloat.prototype.trimExtension = PhotoFloat.trimExtension;
	PhotoFloat.prototype.cleanHash = PhotoFloat.cleanHash;
	/* expose class globally */
	window.PhotoFloat = PhotoFloat;
}());
