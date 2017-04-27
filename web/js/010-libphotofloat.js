(function() {
	/* constructor */
	function PhotoPaolo() {
		this.albumCache = [];
	}
	
	/* public member functions */
	PhotoPaolo.prototype.album = function(subalbum, callback, error) {
		var cacheKey, ajaxOptions, self;
		if (typeof subalbum.photos !== "undefined" && subalbum.photos !== null) {
			callback(subalbum);
			return;
		}
		if (Object.prototype.toString.call(subalbum).slice(8, -1) === "String")
			cacheKey = subalbum;
		else
			cacheKey = PhotoPaolo.cachePath(subalbum.parent.path + "/" + subalbum.path);
		if (this.albumCache.hasOwnProperty(cacheKey)) {
			callback(this.albumCache[cacheKey]);
			return;
		}
		self = this;
		ajaxOptions = {
			type: "GET",
			dataType: "json",
			url: "cache/" + cacheKey + ".json",
			success: function(album) {
				var i;
				for (i = 0; i < album.albums.length; ++i)
					album.albums[i].parent = album;
				for (i = 0; i < album.photos.length; ++i)
					album.photos[i].parent = album;
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
	PhotoPaolo.prototype.albumPhoto = function(subalbum, callback, error) {
		var nextAlbum, self;
		self = this;
		nextAlbum = function(album) {
			var index = Math.floor(Math.random() * (album.photos.length + album.albums.length));
			if (index >= album.photos.length) {
				index -= album.photos.length;
				self.album(album.albums[index], nextAlbum, error);
			} else
				callback(album, album.photos[index]);
		};
		if (typeof subalbum.photos !== "undefined" && subalbum.photos !== null)
			nextAlbum(subalbum);
		else
			this.album(subalbum, nextAlbum, error);
	};
	PhotoPaolo.prototype.parseHash = function(hash, callback, error) {
		var index, album, photo;
		hash = PhotoPaolo.cleanHash(hash);
		index = hash.lastIndexOf("/");
		if (!hash.length) {
			album = PhotoPaolo.cachePath("root");
			photo = null;
		} else if (index !== -1 && index !== hash.length - 1) {
			photo = hash.substring(index + 1);
			album = hash.substring(0, index);
		} else {
			album = hash;
			photo = null;
		}
		this.album(album, function(theAlbum) {
			var i = -1;
			if (photo !== null) {
				for (i = 0; i < theAlbum.photos.length; ++i) {
					if (PhotoPaolo.cachePath(theAlbum.photos[i].name) === photo) {
						photo = theAlbum.photos[i];
						break;
					}
				}
				if (i >= theAlbum.photos.length) {
					photo = null;
					i = -1;
				}
			}
			callback(theAlbum, photo, i);
		}, error);
	};
	PhotoPaolo.prototype.authenticate = function(password, result) {
		$.ajax({
			type: "GET",
			dataType: "text",
			url: "auth?username=photos&password=" + password,
			success: function() {
				result(true);
			},
			error: function() {
				result(false);
			}
		});
	};
	
	/* static functions */
	PhotoPaolo.cachePath = function(path) {
		if (path === "")
			return "root";
		if (path.charAt(0) === "/")
			path = path.substring(1);
		path = path
			.replace(/ /g, "_")
			.replace(/\//g, "-")
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
	PhotoPaolo.photoHash = function(album, photo) {
		return PhotoPaolo.albumHash(album) + "/" + PhotoPaolo.cachePath(photo.name);
	};
	PhotoPaolo.albumHash = function(album) {
		if (typeof album.photos !== "undefined" && album.photos !== null)
			return PhotoPaolo.cachePath(album.path);
		return PhotoPaolo.cachePath(album.parent.path + "/" + album.path);
	};
	PhotoPaolo.photoPath = function(album, photo, size, square) {
		var suffix, hash;
		if (square)
			suffix = size.toString() + "s";
		else
			suffix = size.toString();
		hash = PhotoPaolo.cachePath(PhotoPaolo.photoHash(album, photo) + "_" + suffix + ".jpg");
		if (hash.indexOf("root-") === 0)
			hash = hash.substring(5);
		return "cache/" + hash;
	};
	PhotoPaolo.originalPhotoPath = function(album, photo) {
		return "albums/" + album.path + "/" + photo.name;
	};
	PhotoPaolo.trimExtension = function(name) {
		var index = name.lastIndexOf(".");
		if (index !== -1)
			return name.substring(0, index);
		return name;
	};
	PhotoPaolo.cleanHash = function(hash) {
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
	PhotoPaolo.prototype.cachePath = PhotoPaolo.cachePath;
	PhotoPaolo.prototype.photoHash = PhotoPaolo.photoHash;
	PhotoPaolo.prototype.albumHash = PhotoPaolo.albumHash;
	PhotoPaolo.prototype.photoPath = PhotoPaolo.photoPath;
	PhotoPaolo.prototype.originalPhotoPath = PhotoPaolo.originalPhotoPath;
	PhotoPaolo.prototype.trimExtension = PhotoPaolo.trimExtension;
	PhotoPaolo.prototype.cleanHash = PhotoPaolo.cleanHash;
	
	/* expose class globally */
	window.PhotoPaolo = PhotoPaolo;
}());
