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
			cacheKey = PhotoFloat.cachePath(subalbum.parent.path + "/" + subalbum.path);
		if (this.albumCache.hasOwnProperty(cacheKey)) {
			callback(this.albumCache[cacheKey]);
			return;
		}
		var cacheFile = Options.server_cache_path + cacheKey + ".json";
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
				$("#album-view").fadeOut(200);
				$("#media-view").fadeOut(200);
				$("#album-view").fadeIn(3500);
				$("#media-view").fadeIn(3500);
				$("#error-text-folder").fadeIn(200);
				$("#error-text-folder, #error-overlay, #auth-text").fadeOut(2500);
				window.location.hash = "!/" + Options.folders_string;
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
		var index, album, photo;
		hash = PhotoFloat.cleanHash(hash);
		index = hash.lastIndexOf("/");
		if (! hash.length) {
			album = PhotoFloat.cachePath(Options.folders_string);
			photo = null;
		} else if (index !== -1 && index !== hash.length - 1) {
			photo = hash.substring(index + 1);
			album = hash.substring(0, index);
		} else {
			album = hash;
			photo = null;
		}
		this.getAlbum(album, function(theAlbum) {
			var i = -1;
			if (photo !== null) {
				for (i = 0; i < theAlbum.media.length; ++i) {
					if (PhotoFloat.cachePath(theAlbum.media[i].name) === photo) {
						photo = theAlbum.media[i];
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
			callback(theAlbum, photo, i);
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
		return PhotoFloat.albumHash(album) + "/" + PhotoFloat.cachePath(media.name);
	};
	PhotoFloat.mediaHashFolder = function(album, media) {
		var hash;
		hash = PhotoFloat.mediaHash(album, media);
		var bydateStringWithTrailingSeparator = Options.by_date_string + Options.cache_folder_separator;
		if (hash.indexOf(bydateStringWithTrailingSeparator) === 0) {
			media.completeName = media.foldersAlbum + '/' + media.name;
			hash = PhotoFloat.cachePath(media.foldersAlbum) + "/" +
			//~ hash = PhotoFloat.cachePath(media.completeName.substring(0, media.completeName.length - media.name.length - 1)) + "/" +
				PhotoFloat.cachePath(media.name);
		}
		return hash;
	};
	PhotoFloat.albumHash = function(album) {
		if (typeof album.media !== "undefined" && album.media !== null)
			return PhotoFloat.cachePath(album.path);
		return PhotoFloat.cachePath(album.parent.path + "/" + album.path);
	};
	PhotoFloat.videoPath = function(album, video) {
		var hashFolder = PhotoFloat.mediaHashFolder(album, video) + "_transcoded.mp4";
		var hash = PhotoFloat.cachePath(hashFolder);
		var rootString = "root-";
		if (hash.indexOf(rootString) === 0)
			hash = hash.substring(rootString.length);
		else {
			var bydateStringWithTrailingSeparator = Options.by_date_string + Options.cache_folder_separator;
			var foldersStringWithTrailingSeparator = Options.folders_string + Options.cache_folder_separator;
			if (hash.indexOf(foldersStringWithTrailingSeparator) === 0)
				hash = hash.substring(foldersStringWithTrailingSeparator.length);
			else {
				bydateStringWithTrailingSeparator = Options.by_date_string + Options.cache_folder_separator;
				if (hash.indexOf(bydateStringWithTrailingSeparator) === 0)
				hash = hash.substring(bydateStringWithTrailingSeparator.length);
			}
		}
		if (video.cacheSubdir)
			return Options.server_cache_path + video.cacheSubdir + "/" + hash;
		else
			return Options.server_cache_path + hash;
	};
	PhotoFloat.thumbPath = function(album, photo, thumb_size) {
		return PhotoFloat.photoPath(album, photo, thumb_size);
	}
	PhotoFloat.photoPath = function(album, photo, thumb_size) {
		var suffix, hash;
		suffix = thumb_size.toString();
		if (thumb_size == Options.album_thumb_size) {
			suffix += "a";
			if (Options.album_thumb_type == "square")
				suffix += "s";
			else if (Options.album_thumb_type == "fit")
				suffix += "f";
		}
		else if (thumb_size == Options.media_thumb_size) {
			suffix += "t";
			if (Options.media_thumb_type == "square")
				suffix += "s";
			else if (Options.media_thumb_type == "fixed_height")
				suffix += "f";
		}
		else
			suffix = thumb_size.toString();
		hash = PhotoFloat.cachePath(PhotoFloat.mediaHashFolder(album, photo) + "_" + suffix + ".jpg");
		var rootString = "root-";
		if (hash.indexOf(rootString) === 0)
			hash = hash.substring(rootString.length);
		else {
			var foldersStringWithTrailingSeparator = Options.folders_string + Options.cache_folder_separator;
			if (hash.indexOf(foldersStringWithTrailingSeparator) === 0)
				hash = hash.substring(foldersStringWithTrailingSeparator.length);
			else {
				var bydateStringWithTrailingSeparator = Options.by_date_string + Options.cache_folder_separator;
				if (hash.indexOf(bydateStringWithTrailingSeparator) === 0)
				hash = hash.substring(bydateStringWithTrailingSeparator.length);
			}
		}
		if (photo.cacheSubdir)
			return Options.server_cache_path + photo.cacheSubdir + "/" + hash;
		else
			return Options.server_cache_path + hash;
	};
	PhotoFloat.originalPhotoPath = function(photo) {
		return photo.albumName;
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
	PhotoFloat.prototype.albumHash = PhotoFloat.albumHash;
	PhotoFloat.prototype.thumbPath = PhotoFloat.thumbPath;
	PhotoFloat.prototype.photoPath = PhotoFloat.photoPath;
	PhotoFloat.prototype.videoPath = PhotoFloat.videoPath;
	PhotoFloat.prototype.originalPhotoPath = PhotoFloat.originalPhotoPath;
	PhotoFloat.prototype.trimExtension = PhotoFloat.trimExtension;
	PhotoFloat.prototype.cleanHash = PhotoFloat.cleanHash;
	/* expose class globally */
	window.PhotoFloat = PhotoFloat;
}());
