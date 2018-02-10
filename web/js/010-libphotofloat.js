(function() {
	/* constructor */
	function PhotoFloat() {
		this.albumCache = [];
		this.geotaggedPhotosFound = null;
		this.searchesCount = 0;
		this.searchWordsFromJsonFile = [];
		// expose variable
		window.searchWordsFromJsonFile = this.searchWordsFromJsonFile;
	}

	/* public member functions */

	PhotoFloat.prototype.getAlbum = function(album, callback, error) {
		var self;
		if (this.searchWordsFromJsonFile.length == 0 && album != Options.by_search_string) {
			self = this;
			// get search root album before every album
			this.getAlbumSuccess(
				Options.by_search_string,
				function() {
					self.getAlbumSuccess(album, callback, error)
				},
				error
			);
		} else {
			this.getAlbumSuccess(album, callback, error);
		}


	};

	PhotoFloat.prototype.getAlbumSuccess = function(thisAlbum, callback, error) {
		var cacheKey, ajaxOptions, self;

		if (typeof thisAlbum.media !== "undefined" && thisAlbum.media !== null) {
			callback(thisAlbum);
			return;
		}
		if (Object.prototype.toString.call(thisAlbum).slice(8, -1) === "String")
			cacheKey = thisAlbum;
		else
			cacheKey = thisAlbum.cacheBase;

		if (this.albumCache.hasOwnProperty(cacheKey)) {
			callback(this.albumCache[cacheKey]);
		} else {
			var cacheFile = PhotoFloat.pathJoin([Options.server_cache_path, cacheKey + ".json"]);
			self = this;
			ajaxOptions = {
				type: "GET",
				dataType: "json",
				url: cacheFile,
				success: function(theAlbum) {
					var i;
					if (cacheKey == Options.by_search_string) {
						// root of search albums: build the word list
						for (i = 0; i < theAlbum.albums.length; ++i)
							self.searchWordsFromJsonFile.push(theAlbum.albums[i].path);
					} else if (cacheKey.indexOf(Options.by_search_string) == -1) {
						for (i = 0; i < theAlbum.albums.length; ++i)
							theAlbum.albums[i].parent = theAlbum;
						for (i = 0; i < theAlbum.media.length; ++i)
							theAlbum.media[i].parent = theAlbum;
					}

					self.albumCache[cacheKey] = theAlbum;

					callback(theAlbum);
				}
			};
			if (typeof error !== "undefined" && error !== null) {
				ajaxOptions.error = function(jqXHR, textStatus, errorThrown) {
					error(jqXHR.status);
				};
			}
			$.ajax(ajaxOptions);
		}
	}

	PhotoFloat.prototype.AddClickToByGpsButton = function(link) {
		// this function returns true if the root album has the by gps subalbum
		if (this.geotaggedPhotosFound !== null) {
			if (this.geotaggedPhotosFound) {
				$("#by-gps-view").off("click");
				$("#by-gps-view").removeClass("hidden").addClass("active").on("click", function(ev) {
					window.location.href = link;
					return false;
				});
			} else {
				$("#by-gps-view").addClass("hidden");
			}
		} else {
			self = this;
			this.getAlbum(
				Options.by_gps_string,
				function() {
					self.geotaggedPhotosFound = true;
					$("#by-gps-view").off("click");
					$("#by-gps-view").removeClass("hidden").addClass("active").on("click", function(ev) {
						window.location.href = link;
						return false;
					});
				},
				function() {
					$("#by-gps-view").addClass("hidden");
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

	PhotoFloat.prototype.intersect = function(a, b) {
		if (b.length > a.length) {
			// indexOf to loop over shorter
			var t;
			t = b, b = a, a = t;
		}
		return a.filter(function (e) {
			for (var i = 0; i < b.length; i ++)
				if (b[i].albumName == e.albumName)
					return true;
			return false;
		});
	};

	// PhotoFloat.prototype.union = function(a, b) {
	// 	if (b.length > a.length) {
	// 		// indexOf to loop over shorter
	// 		var t;
	// 		t = b, b = a, a = t;
	// 	}
	// 	return a.filter(function (e) {
	// 		for (var i = 0; i < b.length; i ++)
	// 			if (b[i].albumName == e.albumName)
	// 				return true;
	// 		return false;
	// 	});
	// };

	PhotoFloat.prototype.parseHash = function(hash, callback, error) {
		// this vars are defined here and not at the beginning of the file because the options must have been read
		PhotoFloat.foldersStringWithTrailingSeparator = Options.folders_string + Options.cache_folder_separator;
		PhotoFloat.byDateStringWithTrailingSeparator = Options.by_date_string + Options.cache_folder_separator;
		PhotoFloat.byGpsStringWithTrailingSeparator = Options.by_gps_string + Options.cache_folder_separator;
		PhotoFloat.bySearchStringWithTrailingSeparator = Options.by_search_string + Options.cache_folder_separator;

		var hashParts, lastSlashPosition, slashCount, albumHash, albumHashes, mediaHash = null, foldersHash = null, media = null, i;
		$("#error-too-many-images").hide();
		hash = PhotoFloat.cleanHash(hash);
		// count the number of slashes in hash, by date hashes have 2, folders ones 1
		if (! hash.length) {
			albumHash = Options.folders_string;
			mediaHash = null;
		} else {
			hashParts = hash.split("/");
			slashCount = hashParts.length -1;
			lastSlashPosition = hash.lastIndexOf("/");

			if (slashCount == 1) {
				// folders hash: album and media
				albumHash = hashParts[0];
				mediaHash = hashParts[1];
			} else if (slashCount == 0) {
				// folders or by date hash: album only
				albumHash = hash;
			} else if (slashCount == 2) {
				// by date hash: by date album, folders album, media
				albumHash = hashParts[0];
				mediaHash = hashParts[2];
				foldersHash = hashParts[1];
			}
		}

		albumHashes = [];
		if (albumHash) {
			albumHash = decodeURI(albumHash);
			if (slashCount == 0 && albumHash.indexOf(Options.by_search_string) === 0) {
				var wordsString = albumHash.substring(Options.by_search_string.length + 1);
				$("ul#right-menu").addClass("expand");
				$("ul#right-menu #search-field").attr("value", wordsString.replace(/_/g, ' '));
				if (selectedSearchWords.length == 0) {
					selectedSearchWords = wordsString.split('_');
				}
				for (i = 0; i < selectedSearchWords.length; i ++)
					albumHashes[i] = Options.by_search_string + Options.cache_folder_separator + selectedSearchWords[i];
				if (! Options.search_any_word) {
					// getting the first album is enough, media that do not match the other words will be escluded later
					albumHashes = [albumHashes[0]];
				}
			}
		}
		if (mediaHash)
			mediaHash = decodeURI(mediaHash);
		if (foldersHash)
			foldersHash = decodeURI(foldersHash);

		if (albumHash && albumHashes.length > 0) {
			var searchResultsAlbum = "";
			this.searchesCount = 0;
			self = this;
			for (i = 0; i < albumHashes.length; i ++) {
				this.getAlbum(
					albumHashes[i],
					function(theAlbum) {
						var i, j;
						if (searchResultsAlbum === "") {
							searchResultsAlbum = theAlbum;
						} else {
							// for (i = 0; i < theAlbum.media.length; i ++)
							// 	delete theAlbum.media[i].parent;
							searchResultsAlbum.media = self.intersect(searchResultsAlbum.media, theAlbum.media);
						}
						self.searchesCount ++;
						if (self.searchesCount == albumHashes.length) {
							if (! Options.search_any_word && albumHashes.length > 1) {
								// we still have to filter out media that do not match the words after the first
								var matchingMedia = [];
								for (j = 0; j < searchResultsAlbum.media.length; j ++) {
									for (i = 1; i < selectedSearchWords.length; i ++) {
										if (Options.search_inside_words) {
											if (searchResultsAlbum.media[j].name.indexOf(selectedSearchWords[i]) != -1) {
												matchingMedia.push(searchResultsAlbum.media[j]);
												break;
											}
										} else {
											// not inside words
											if (searchResultsAlbum.media[j].words.indexOf(selectedSearchWords[i]) != -1) {
												matchingMedia.push(searchResultsAlbum.media[j]);
												break;
											}
										}
									}
								}
								searchResultsAlbum.media = matchingMedia;
							}
							var searchTerms = location.hash.substring(("#!/" + Options.by_search_string + Options.cache_folder_separator).length);
							searchResultsAlbum.numMediaInAlbum = searchResultsAlbum.media.length;
							searchResultsAlbum.numMediaInSubTree = searchResultsAlbum.media.length;
							searchResultsAlbum.cacheBase = Options.by_search_string + Options.cache_folder_separator + searchTerms;
							searchResultsAlbum.path = PhotoFloat.pathJoin([Options.by_search_string, searchTerms]);
							searchResultsAlbum.physicalPath = searchResultsAlbum.path;
							searchResultsAlbum.ancestorsCacheBase[searchResultsAlbum.ancestorsCacheBase.length - 1] = searchResultsAlbum.cacheBase;
							callback(searchResultsAlbum, null, -1);
						}
					},
					error
				);
			}
		} else
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
							window.location.hash = theAlbum.cacheBase;
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

	PhotoFloat.isByDateAlbum = function(string) {
		return string == Options.by_date_string || string.indexOf(PhotoFloat.byDateStringWithTrailingSeparator) === 0;
	};

	PhotoFloat.isByGpsAlbum = function(string) {
		return string == Options.by_gps_string || string.indexOf(PhotoFloat.byGpsStringWithTrailingSeparator) === 0;
	};

	PhotoFloat.isFolderAlbum = function(string) {
		return string == Options.folders_string || string.indexOf(PhotoFloat.foldersStringWithTrailingSeparator) === 0;
	};

	PhotoFloat.isSearchAlbum = function(string) {
		return string == Options.by_search_string || string.indexOf(PhotoFloat.bySearchStringWithTrailingSeparator) === 0;
	};


	PhotoFloat.mediaHashURIEncoded = function(album, media) {
		var hash;
		if (PhotoFloat.isByDateAlbum(album.cacheBase) || PhotoFloat.isByGpsAlbum(album.cacheBase))
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
		if (PhotoFloat.isByDateAlbum(hash) || PhotoFloat.isByGpsAlbum(hash)) {
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
			if (PhotoFloat.isFolderAlbum(hash))
				hash = hash.substring(PhotoFloat.foldersStringWithTrailingSeparator.length);
			else if (PhotoFloat.isByDateAlbum(hash))
				hash = hash.substring(PhotoFloat.byDateStringWithTrailingSeparator.length);
			else if (PhotoFloat.isByGpsAlbum(hash))
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
