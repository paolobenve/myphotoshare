(function() {
	/* constructor */
	function PhotoFloat() {
		this.albumCache = [];
	}
	
	/* public member functions */
	PhotoFloat.prototype.album = function(subalbum, callback, error) {
		var cacheKey, ajaxOptions, self;
		if (typeof subalbum.photos !== "undefined" && subalbum.photos !== null) {
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
		cacheFile = "cache/" + cacheKey + ".json";
		if (PhotoFloat.urlDoesntExist(cacheFile))
			cacheKey = "root";
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
	PhotoFloat.prototype.albumPhoto = function(subalbum, callback, error) {
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
	PhotoFloat.prototype.parseHash = function(hash, callback, error) {
		var index, album, photo;
		hash = PhotoFloat.cleanHash(hash);
		index = hash.lastIndexOf("/");
		if (!hash.length) {
			album = PhotoFloat.cachePath("root");
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
					if (PhotoFloat.cachePath(theAlbum.photos[i].name) === photo) {
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
	PhotoFloat.prototype.authenticate = function(password, result) {
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
	PhotoFloat.cachePath = function(path) {
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
	PhotoFloat.photoHash = function(album, media) {
		return PhotoFloat.albumHash(album) + "/" + PhotoFloat.cachePath(media.name);
	};
	PhotoFloat.photoHashFolder = function(album, media) {
		var hash;
		hash = PhotoFloat.photoHash(album, media);
		if (hash.indexOf(bydateStringWithTrailingDash) === 0) {
			hash = PhotoFloat.cachePath(media.completeName.substring(0, media.completeName.length - media.name.length - 1)) + "/" + PhotoFloat.cachePath(media.name);
		}
		return hash;
	};
	PhotoFloat.albumHash = function(album) {
		if (typeof album.photos !== "undefined" && album.photos !== null)
			return PhotoFloat.cachePath(album.path);
		return PhotoFloat.cachePath(album.parent.path + "/" + album.path);
	};
	PhotoFloat.photoPath = function(album, photo, size, square) {
		var suffix, hash;
		if (square)
			suffix = size.toString() + "s";
		else
			suffix = size.toString();
		hash = PhotoFloat.cachePath(PhotoFloat.photoHashFolder(album, photo) + "_" + suffix + ".jpg");
		var rootString = "root-";
		if (hash.indexOf(rootString) === 0)
			hash = hash.substring(rootString.length);
		else {
			var foldersString = "_folders-";
			if (hash.indexOf(foldersString) === 0)
				hash = hash.substring(foldersString.length);
			else {
				if (hash.indexOf(bydateStringWithTrailingDash) === 0)
				hash = hash.substring(bydateStringWithTrailingDash.length);
			}
		}
		return "cache/" + hash;
	};
	PhotoFloat.originalPhotoPath = function(photo) {
		return photo.albumName;
	};
	PhotoFloat.photoFoldersAlbum = function(photo) {
		return photo.foldersAlbum;
	};
	PhotoFloat.photoDayAlbum = function(photo) {
		return photo.dayAlbum;
	};
	PhotoFloat.photoMonthAlbum = function(photo) {
		return photo.monthAlbum;
	};
	PhotoFloat.photoYearAlbum = function(photo) {
		return photo.yearAlbum;
	};
	PhotoFloat.videoPath = function(album, video) {
		hash = PhotoFloat.cachePath(PhotoFloat.photoHashFolder(album, video) + ".mp4");
		var rootString = "root-";
		if (hash.indexOf(rootString) === 0)
			hash = hash.substring(rootString.length);
		else {
			var foldersString = "_folders-";
			if (hash.indexOf(foldersString) === 0)
				hash = hash.substring(foldersString.length);
			else {
				if (hash.indexOf(bydateStringWithTrailingDash) === 0)
				hash = hash.substring(bydateStringWithTrailingDash.length);
			}
		}
		return "cache/" + hash;
		
		//return "cache/" + PhotoFloat.cachePath(PhotoFloat.photoHash(album, video) + ".mp4");
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
	
	PhotoFloat.urlDoesntExist = function(url) {
		var http = new XMLHttpRequest();
		http.open('HEAD', url, false);
		http.send();
		return http.status == 404;
	};

	
	/* make static methods callable as member functions */
	PhotoFloat.prototype.cachePath = PhotoFloat.cachePath;
	PhotoFloat.prototype.photoHash = PhotoFloat.photoHash;
	PhotoFloat.prototype.photoHashFolder = PhotoFloat.photoHashFolder;
	PhotoFloat.prototype.albumHash = PhotoFloat.albumHash;
	PhotoFloat.prototype.photoPath = PhotoFloat.photoPath;
	PhotoFloat.prototype.videoPath = PhotoFloat.videoPath;
	PhotoFloat.prototype.originalPhotoPath = PhotoFloat.originalPhotoPath;
	PhotoFloat.prototype.photoFoldersAlbum = PhotoFloat.photoFoldersAlbum;
	PhotoFloat.prototype.photoDayAlbum = PhotoFloat.photoDayAlbum;
	PhotoFloat.prototype.photoMonthAlbum = PhotoFloat.photoMonthAlbum;
	PhotoFloat.prototype.photoYearAlbum = PhotoFloat.photoYearAlbum;
	PhotoFloat.prototype.trimExtension = PhotoFloat.trimExtension;
	PhotoFloat.prototype.cleanHash = PhotoFloat.cleanHash;
	PhotoFloat.prototype.urlDoesntExist = PhotoFloat.urlDoesntExist;
	/* expose class globally */
	window.PhotoFloat = PhotoFloat;
}());
