(function() {
	/* constructor */
	function PhotoFloat() {
		this.albumCache = [];
		PhotoFloat.firstAlbumPopulation = true;
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
			cacheKey = PhotoFloat.cachePath(PhotoFloat.pathJoin([subalbum.parent.path, subalbum.path]));
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
				var rootHash = "!/" + Options.folders_string;
				
				$("#album-view").fadeOut(200);
				$("#media-view").fadeOut(200);
				
				if (window.location.hash == "#" + rootHash) {
					$("#loading").hide();
					$("#error-text-folder").stop();
					$("#error-root-folder").fadeIn(2000);
					$("#powered-by").show();
				} else {
					$("#error-text-folder").fadeIn(200);
					$("#error-text-folder, #error-overlay, #auth-text").fadeOut(2500);
					$("#album-view").fadeIn(3500);
					$("#media-view").fadeIn(3500);
					window.location.hash = rootHash;
				}
			};
		}
		$.ajax(ajaxOptions);
	};
	
	PhotoFloat.prototype.pickRandomMedia = function(subalbum, container, callback, error) {
		var nextAlbum, self;
		self = this;
		nextAlbum = function(album) {
			var index = Math.floor(Math.random() * (album.media.length + album.albums.length));
			if (index >= album.media.length) {
				index -= album.media.length;
				self.getAlbum(album.albums[index], nextAlbum, error);
			} else
				callback(album, album.media[index], container);
		};
		if (typeof subalbum.media !== "undefined" && subalbum.media !== null)
			nextAlbum(subalbum);
		else
			this.getAlbum(subalbum, nextAlbum, error);
	};
	
	PhotoFloat.prototype.parseHash = function(hash, callback, error) {
		var index, albumHash, mediaHash, media = null, self = this;
		hash = PhotoFloat.cleanHash(hash);
		index = hash.lastIndexOf("/");
		if (! hash.length) {
			albumHash = PhotoFloat.cachePath(Options.folders_string);
			mediaHash = null;
		} else if (index !== -1 && index !== hash.length - 1) {
			mediaHash = hash.substring(index + 1);
			albumHash = hash.substring(0, index);
		} else {
			albumHash = hash;
			mediaHash = null;
		}
		this.getAlbum(albumHash, function(theAlbum) {
			var i = -1;
			if (mediaHash !== null) {
				for (i = 0; i < theAlbum.media.length; ++i) {
					if (PhotoFloat.cachePath(theAlbum.media[i].name) === mediaHash) {
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
					window.location.hash = album;
					i = -1;
				}
			}
			if (theAlbum.parentAlbumPath) {
				self.getAlbum(PhotoFloat.cachePath(theAlbum.parentAlbumPath), function(theParentAlbum) {
					theAlbum.parent = theParentAlbum;
					callback(theAlbum, media, i);
				});
			}
			
		}, error);
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
	
	/* static functions */
	PhotoFloat.cachePath = function(path) {
		if (path === "")
			return "root";
		if (path.charAt(0) === "/")
			path = path.substring(1);
		path = path
			.replace(/ /g, "_")
			.replace(/\//g, Options.cache_folder_separator)
			.replace(/\(/g, "")
			.replace(/\)/g, "")
			.replace(/#/g, "")
			.replace(/&/g, "")
			.replace(/,/g, "")
			.replace(/\[/g, "")
			.replace(/\]/g, "")
			.replace(/"/g, "")
			.replace(/'/g, "")
			.replace(/_-_/g, "-")
			.toLowerCase();
		while (path.indexOf("--") !== -1)
			path = path.replace(/--/g, "-");
		while (path.indexOf("__") !== -1)
			path = path.replace(/__/g, "_");
		return path;
	};
	PhotoFloat.mediaHash = function(album, media) {
		return PhotoFloat.pathJoin([PhotoFloat.albumHash(album), PhotoFloat.cachePath(media.name)]);
	};
	PhotoFloat.mediaHashFolder = function(album, media) {
		var hash;
		hash = PhotoFloat.mediaHash(album, media);
		var bydateStringWithTrailingSeparator = Options.by_date_string + Options.cache_folder_separator;
		if (hash.indexOf(bydateStringWithTrailingSeparator) === 0) {
			media.completeName = PhotoFloat.pathJoin([media.foldersAlbum, media.name]);
			hash = PhotoFloat.pathJoin([PhotoFloat.cachePath(media.foldersAlbum), PhotoFloat.cachePath(media.name)]);
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
			result += pathArr[i]
		}
		return result;
	}
	PhotoFloat.albumHash = function(album) {
		if (typeof album.media !== "undefined" && album.media !== null)
			return PhotoFloat.cachePath(album.path);
		return PhotoFloat.cachePath(PhotoFloat.pathJoin([album.parent.path, album.path]));
	};
	PhotoFloat.mediaPath = function(album, media, size) {
		var suffix = "_", hash, rootString = "root-";
		var bydateStringWithTrailingSeparator = Options.by_date_string + Options.cache_folder_separator;
		var foldersStringWithTrailingSeparator = Options.folders_string + Options.cache_folder_separator;
		if (
			media.mediaType == "photo" ||
			media.mediaType == "video" && [Options.album_thumb_size, Options.media_thumb_size].indexOf(size) != -1
		) {
			suffix += size.toString();
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
			suffix += "transcoded_" + Options.video_transcode_bitrate + ".mp4";
		}
		hash = PhotoFloat.cachePath(PhotoFloat.mediaHashFolder(album, media) + suffix);
		if (hash.indexOf(rootString) === 0)
			hash = hash.substring(rootString.length);
		else {
			if (hash.indexOf(foldersStringWithTrailingSeparator) === 0)
				hash = hash.substring(foldersStringWithTrailingSeparator.length);
			else {
				if (hash.indexOf(bydateStringWithTrailingSeparator) === 0)
				hash = hash.substring(bydateStringWithTrailingSeparator.length);
			}
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
	PhotoFloat.prototype.cachePath = PhotoFloat.cachePath;
	PhotoFloat.prototype.mediaHash = PhotoFloat.mediaHash;
	PhotoFloat.prototype.mediaHashFolder = PhotoFloat.mediaHashFolder;
	PhotoFloat.prototype.pathJoin = PhotoFloat.pathJoin;
	PhotoFloat.prototype.albumHash = PhotoFloat.albumHash;
	PhotoFloat.prototype.mediaPath = PhotoFloat.mediaPath;
	PhotoFloat.prototype.originalMediaPath = PhotoFloat.originalMediaPath;
	PhotoFloat.prototype.trimExtension = PhotoFloat.trimExtension;
	PhotoFloat.prototype.cleanHash = PhotoFloat.cleanHash;
	/* expose class globally */
	window.PhotoFloat = PhotoFloat;
}());
