(function() {
	/* constructor */
	function PhotoFloat() {
		this.albumCache = [];
		this.geotaggedPhotosFound = null;
		this.searchWordsFromJsonFile = [];
		// expose variable
		window.searchWordsFromJsonFile = this.searchWordsFromJsonFile;
	}

	/* public member functions */
	PhotoFloat.prototype.getAlbum = function(thisAlbum, callback, error, thisIndexWords, thisIndexAlbums) {
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
			if (typeof thisIndexWords === "undefined" && typeof thisIndexAlbums === "undefined")
				callback(this.albumCache[cacheKey]);
			else
				callback(this.albumCache[cacheKey], thisIndexWords, thisIndexAlbums);
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
						for (i = 0; i < theAlbum.subalbums.length; ++i)
							self.searchWordsFromJsonFile.push(theAlbum.subalbums[i].path);
					} else if (cacheKey.indexOf(Options.by_search_string) !== 0) {
						for (i = 0; i < theAlbum.subalbums.length; ++i)
							theAlbum.subalbums[i].parent = theAlbum;
						for (i = 0; i < theAlbum.media.length; ++i)
							theAlbum.media[i].parent = theAlbum;
					}

					self.albumCache[cacheKey] = theAlbum;

					if (typeof thisIndexWords === "undefined" && typeof thisIndexAlbums === "undefined")
						callback(theAlbum);
					else
						callback(theAlbum, thisIndexWords, thisIndexAlbums);
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

	PhotoFloat.prototype.addClickToByGpsButton = function(link) {
		// this function returns true if the root album has the by gps subalbum
		if (this.geotaggedPhotosFound !== null) {
			if (this.geotaggedPhotosFound) {
				$("#by-gps-view").off("click");
				$("#by-gps-view").removeClass("hidden").addClass("active").on("click", function(ev) {
					$("#no-results").hide();
					$("#album-view").removeClass("hidden");
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
						$("#no-results").hide();
						$("#album-view").removeClass("hidden");
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
				for (var i = 0; i < album.subalbums.length; i ++) {
					if (index >= album.subalbums[i].numMediaInSubTree)
						index -= album.subalbums[i].numMediaInSubTree;
					else
						break;
				}
				self.getAlbum(album.subalbums[i], nextAlbum, error);
			} else
				callback(album, album.media[index], container, subalbum);
		};
		if (typeof subalbum.media !== "undefined" && subalbum.media !== null)
			nextAlbum(subalbum);
		else
			this.getAlbum(subalbum, nextAlbum, error);
	};

	PhotoFloat.noResults = function() {
		// no media found, show the "no results line below search field"
		$("#album-view").addClass("hidden");
		$("#no-results").fadeIn(2000);
	}

	PhotoFloat.prototype.parseHash = function(hash, callback, error) {
		var hashParts, lastSlashPosition, slashCount, albumHash, albumHashes, mediaHash = null, foldersHash = null, media = null, i;
		var SearchWordsFromUser, SearchWordsFromUserNormalized;
		var indexWords, indexAlbums;
		// this vars are defined here and not at the beginning of the file because the options must have been read
		PhotoFloat.foldersStringWithTrailingSeparator = Options.folders_string + Options.cache_folder_separator;
		PhotoFloat.byDateStringWithTrailingSeparator = Options.by_date_string + Options.cache_folder_separator;
		PhotoFloat.byGpsStringWithTrailingSeparator = Options.by_gps_string + Options.cache_folder_separator;
		PhotoFloat.bySearchStringWithTrailingSeparator = Options.by_search_string + Options.cache_folder_separator;

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
		SearchWordsFromUser = [];
		SearchWordsFromUserNormalized = [];
		if (albumHash) {
			albumHash = decodeURI(albumHash);
			if (slashCount == 0 && albumHash.indexOf(Options.by_search_string) === 0 && albumHash != Options.by_search_string) {
				var wordsWithOptionsString = albumHash.substring(Options.by_search_string.length + 1);
				var wordsAndOptions = wordsWithOptionsString.split(Options.cache_folder_separator);
				var wordsString = wordsAndOptions[wordsAndOptions.length - 1];
				var wordsStringOriginal = wordsString.replace(/_/g, ' ');
				// the normalized words are needed in order to compare with the search cache json files names, which are normalized
				var wordsStringNormalized = PhotoFloat.removeAccents(wordsString.toLowerCase());
				if (wordsAndOptions.length > 1) {
					var searchOptions = wordsAndOptions.slice(0, -1);
					Options.search_regex = searchOptions.indexOf('r') > -1;
					Options.search_inside_words = searchOptions.indexOf('i') > -1;
					Options.search_any_word = searchOptions.indexOf('w') > -1;
					Options.search_case_sensitive = searchOptions.indexOf('c') > -1;
					Options.search_accent_sensitive = searchOptions.indexOf('a') > -1;
				}

				$("ul#right-menu #search-field").attr("value", wordsStringOriginal);
				wordsString = PhotoFloat.normalize(wordsString);
				$("ul#right-menu").addClass("expand");
				SearchWordsFromUser = wordsString.split('_');
				SearchWordsFromUserNormalized = wordsStringNormalized.split('_');
			}
		}
		if (mediaHash)
			mediaHash = decodeURI(mediaHash);
		if (foldersHash)
			foldersHash = decodeURI(foldersHash);

		if (albumHash && SearchWordsFromUser.length > 0) {
			self = this;
			// get the search root album before getting the search words ones
			this.getAlbum(
				Options.by_search_string,
				// success:
				function(bySearchRootAlbum) {
					var last_index, i, j, wordHashes, numSearchAlbumsReady = 0, numSubAlbumsToGet = 0;
					var searchResultsMedia = [];
					var searchResultsAlbumFinal = {};
					searchResultsAlbumFinal.media = [];
					searchResultsAlbumFinal.subalbums = [];
					searchResultsAlbumFinal.numMediaInAlbum = 0;
					searchResultsAlbumFinal.numMediaInSubTree = 0;
					searchResultsAlbumFinal.cacheBase = albumHash;
					searchResultsAlbumFinal.ancestorsCacheBase = bySearchRootAlbum.ancestorsCacheBase.slice();
					searchResultsAlbumFinal.ancestorsCacheBase.push(wordsWithOptionsString);
					searchResultsAlbumFinal.path = searchResultsAlbumFinal.cacheBase.replace(Options.cache_folder_separator, "/");
					searchResultsAlbumFinal.physicalPath = searchResultsAlbumFinal.path;
					if (! Options.search_any_word)
						// getting the first album is enough, media that do not match the other words will be escluded later
						last_index = 0;
					else
						last_index = SearchWordsFromUser.length - 1;
					if (Options.search_inside_words) {
						// we must determine the albums that could match the words given by the user, word by word
						for (i = 0; i <= last_index; i ++) {
							wordHashes = [];
							for (j = 0; j < searchWordsFromJsonFile.length; j ++) {
								if (searchWordsFromJsonFile[j].indexOf(SearchWordsFromUserNormalized[i]) > -1) {
								 	wordHashes.push(Options.by_search_string + Options.cache_folder_separator + encodeURIComponent(searchWordsFromJsonFile[j]));
									numSubAlbumsToGet ++;
								}
							}
							if (wordHashes.length)
								albumHashes.push(wordHashes);
						}
					} else {
						// whole words
						for (i = 0; i < SearchWordsFromUser.length; i ++)
							if (searchWordsFromJsonFile.indexOf(SearchWordsFromUserNormalized[i]) > -1) {
								albumHashes.push([Options.by_search_string + Options.cache_folder_separator + encodeURIComponent(SearchWordsFromUserNormalized[i])]);
								numSubAlbumsToGet ++;
							}
					}

					if (albumHashes.length == 0){
						PhotoFloat.noResults();
						callback(searchResultsAlbumFinal, null, -1);
					} else {
						$("#album-view").removeClass("hidden");
						$("#no-results").hide();
						for (indexWords = 0; indexWords <= last_index; indexWords ++) {
							for (indexAlbums = 0; indexAlbums < albumHashes[indexWords].length; indexAlbums ++) {
								// getAlbum is called here with 2 more parameters, indexAlbums and indexWords, in order to know their ValueError
								// if they are not passed as arguments, the success function will see their values updates (getAlbum is an asyncronous function)
								self.getAlbum(
									albumHashes[indexWords][indexAlbums],
									// success:
									function(theAlbum, thisIndexWords, thisIndexAlbums) {
										var matchingMedia = [], match, matchMediaWord, mediaNameFromSearch, arrayWordsFromMedia, indexMedia, indexWordsLeft, resultAlbum;

										resultAlbum = PhotoFloat.cloneObject(theAlbum);
										// media in the album still has to be filtered according to search criteria
										for (indexMedia = 0; indexMedia < theAlbum.media.length; indexMedia ++) {
											if (! Options.search_inside_words) {
												// whole word
												if (PhotoFloat.normalize(theAlbum.media[indexMedia].words).indexOf(SearchWordsFromUser[thisIndexWords]) > -1)
													matchingMedia.push(theAlbum.media[indexMedia]);
											} else {
												// inside words
												for (indexMediaWords = 0; indexMediaWords < theAlbum.media[indexMedia].words.length; indexMediaWords ++) {
													if (PhotoFloat.normalize(theAlbum.media[indexMedia].words[indexMediaWords]).indexOf(SearchWordsFromUser[thisIndexWords]) > -1) {
														matchingMedia.push(theAlbum.media[indexMedia]);
														break;
													}
												}
											}
										}
										resultAlbum.media = matchingMedia;

										if (! (thisIndexWords in searchResultsMedia)) {
											searchResultsMedia[thisIndexWords] = resultAlbum.media;
										} else {
											searchResultsMedia[thisIndexWords] = PhotoFloat.union(searchResultsMedia[thisIndexWords], resultAlbum.media);
										}

										if (++ numSearchAlbumsReady >= numSubAlbumsToGet) {
											// all the albums have been got, we can merge the results
											searchResultsAlbumFinal.media = searchResultsMedia[0];
											for (indexWords1 = 1; indexWords1 <= last_index; indexWords1 ++) {
												searchResultsAlbumFinal.media = Options.search_any_word ?
													PhotoFloat.union(searchResultsAlbumFinal.media, searchResultsMedia[indexWords1]):
													PhotoFloat.intersect(searchResultsAlbumFinal.media, searchResultsMedia[indexWords1]);
											}

											if (last_index != SearchWordsFromUser.length - 1) {
												// we still have to filter out the media that do not match the words after the first
												// we are in all words search mode
												matchingMedia = [];
												for (indexMedia = 0; indexMedia < searchResultsAlbumFinal.media.length; indexMedia ++) {
													match = true;
													for (indexWordsLeft = last_index + 1; indexWordsLeft < SearchWordsFromUser.length; indexWordsLeft ++) {
														if (! Options.search_inside_words) {
															// whole word
															if (PhotoFloat.normalize(searchResultsAlbumFinal.media[indexMedia].words).indexOf(SearchWordsFromUser[indexWordsLeft]) == -1) {
																match = false;
																break;
															}
														} else {
															// inside words
															matchMediaWord = false;
															for (indexMediaWords = 0; indexMediaWords < searchResultsAlbumFinal.media[indexMedia].words.length; indexMediaWords ++) {
																if (PhotoFloat.normalize(searchResultsAlbumFinal.media[indexMedia].words[indexMediaWords]).indexOf(SearchWordsFromUser[indexWordsLeft]) > -1) {
																	matchMediaWord = true;
																	break;
																}
															}
															if (! matchMediaWord) {
																match = false;
																break;
															}
														}
													}
													if (match)
														matchingMedia.push(searchResultsAlbumFinal.media[indexMedia]);
												}
												searchResultsAlbumFinal.media = matchingMedia;
											}
											if (! searchResultsAlbumFinal.media.length) {
												PhotoFloat.noResults();
											} else {
												$("#album-view").removeClass("hidden");
												$("#no-results").hide();
												searchResultsAlbumFinal.numMediaInAlbum = searchResultsAlbumFinal.media.length;
												searchResultsAlbumFinal.numMediaInSubTree = searchResultsAlbumFinal.media.length;
												// searchResultsAlbumFinal.cacheBase = Options.by_search_string + Options.cache_folder_separator + wordsWithOptionsString;
												// searchResultsAlbumFinal.path = searchResultsAlbumFinal.cacheBase.replace(Options.cache_folder_separator, "/");
												// searchResultsAlbumFinal.physicalPath = searchResultsAlbumFinal.path;
												// searchResultsAlbumFinal.ancestorsCacheBase[searchResultsAlbumFinal.ancestorsCacheBase.length - 1] = searchResultsAlbumFinal.cacheBase;
											}
											self.albumCache[searchResultsAlbumFinal.cacheBase] = searchResultsAlbumFinal;
											callback(searchResultsAlbumFinal, null, -1);
										}
									},
									error,
									indexWords,
									indexAlbums
								);
							}
						}
					}
				},
				error
			);
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

	PhotoFloat.cloneObject = function(object) {
		return Object.assign({}, object);
	}

	PhotoFloat.intersect = function(a, b) {
		if (b.length > a.length) {
			// indexOf to loop over shorter
			var t;
			t = b, b = a, a = t;
		}
		return a.filter(function (e) {
			for (var i = 0; i < b.length; i ++) {
				if (PhotoFloat.normalize(b[i].albumName) == PhotoFloat.normalize(e.albumName))
					return true;
			}
			return false;
		});
	};

	PhotoFloat.union = function(a, b) {
		// begin cloning the first array
		var union = a.slice(0);
		for (var i = 0; i < b.length; i ++) {
			if (! a.some(
				function (e) {
					return PhotoFloat.normalize(b[i].albumName) == PhotoFloat.normalize(e.albumName);
				})
			)
				union.push(b[i]);
		}
		return union;
	};


	PhotoFloat.checkResult = function(searchStringFromUser) {
		var found, i, j;
		var arrayWordsFromUser = searchStringFromUser.split(' ');
		var arraySearchAlbums = [];
		if (! Options.search_any_word) {
			// AND search
			for (i = 0; i < arrayWordsFromUser.length; i ++) {
				if (! Options.search_inside_words) {
					if (window.searchWordsFromJsonFile.indexOf(arrayWordsFromUser[i]) > -1) {
						arraySearchAlbums.push(arrayWordsFromUser[i]);
					} else {
						arraySearchAlbums = [];
						break;
					}
				} else {
					// search inside words
					found = false;
					for (j = 0; j < window.searchWordsFromJsonFile.length; j ++) {
						if (window.searchWordsFromJsonFile[j].includes(arrayWordsFromUser[i])) {

						} else {
							found = false;
						}
					}
					if (! found)
						arraySearchAlbums.push(window.searchWordsFromJsonFile[j]);
				}
			}
		} else {
			// OR search
			// still to be worked
			found = false;
			for (i = 0; i < arrayWordsFromUser.length; i ++) {
				if (! Options.search_inside_words) {
					if (window.searchWordsFromJsonFile.indexOf(arrayWordsFromUser[i]) > -1)
						arraySearchAlbums.push(arrayWordsFromUser[i]);
				} else if (Options.search_inside_words) {
					for (j = 0; j < window.searchWordsFromJsonFile.length; j ++) {
						if (window.searchWordsFromJsonFile[j].includes(arrayWordsFromUser[i])) {
							found = true;
							break;
						}
					}
				}
			}
		}
		return arraySearchAlbums;
	}

	PhotoFloat.normalize = function(object) {
		var string = object;
		if (typeof object === "object")
			string = string.join('|');

		if (! Options.search_case_sensitive)
			string = string.toLowerCase();
		if (! Options.search_accent_sensitive)
			string = PhotoFloat.removeAccents(string);

		if (typeof object === "object")
			object = string.split('|');
		else
			object = string;

		return object;
	}

	PhotoFloat.removeAccents = function(string) {
		return string.latinise();
	}

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
		if (PhotoFloat.isByDateAlbum(album.cacheBase) || PhotoFloat.isByGpsAlbum(album.cacheBase) || PhotoFloat.isSearchAlbum(album.cacheBase))
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
		var suffix = Options.cache_folder_separator, hash, rootString = "root-";
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
