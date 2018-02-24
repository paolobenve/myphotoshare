(function() {
	/* constructor */
	function PhotoFloat() {
		this.albumCache = [];
		this.geotaggedPhotosFound = null;
		this.searchWordsFromJsonFile = [];
		this.searchCacheBase = '';

		PhotoFloat.searchCacheBase = this.searchCacheBase;
		PhotoFloat.searchWordsFromJsonFile = this.searchWordsFromJsonFile;
	}

	/* public member functions */
	PhotoFloat.prototype.getAlbum = function(thisAlbum, callback, error, thisIndexWords, thisIndexAlbums) {
		var cacheKey, ajaxOptions, self;

		if (typeof thisAlbum.media !== "undefined" && thisAlbum.media !== null) {
			callback(thisAlbum);
			return;
		}
		if (Object.prototype.toString.call(thisAlbum).slice(8, -1) === "String") {
			if (PhotoFloat.isSearchCacheBase(thisAlbum) && thisAlbum.indexOf('/') != -1)
				cacheKey = thisAlbum.substr(thisAlbum.indexOf('/') + 1);
			else
				cacheKey = thisAlbum;
		} else
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
							PhotoFloat.searchWordsFromJsonFile.push(theAlbum.subalbums[i].path);
					} else if (! PhotoFloat.isSearchCacheBase(cacheKey)) {
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
	};

	PhotoFloat.prototype.addClickToByGpsButton = function(link) {
		var self;
		// this function returns true if the root album has the by gps subalbum
		if (this.geotaggedPhotosFound !== null) {
			if (this.geotaggedPhotosFound) {
				$("#by-gps-view").off("click");
				$("#by-gps-view").removeClass("hidden").addClass("active").on("click", function(ev) {
					$(".search-failed").hide();
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
						$(".search-failed").hide();
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
	};

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

	PhotoFloat.noResults = function(id) {
		// no media found, show the "no results" line
		$("#album-view").addClass("hidden");
		if (typeof id === "undefined")
			id = 'no-results';
		$(".search-failed").hide();
		$("#" + id).fadeIn(2000);
	};

	PhotoFloat.prototype.parseHash = function(hash, callback, error) {
		var hashParts, lastSlashPosition, slashCount, albumHash, albumHashes, mediaHash = null, foldersHash = null, media = null;
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

			if (slashCount === 0) {
				// folders only or root of a virtual folders: album only
				albumHash = hash;
			} else if (slashCount == 1) {
				// folders hash: album and media
				// or: search album and folder
				albumHash = hashParts[0];
				if (PhotoFloat.isFolderCacheBase(hashParts[1])) {
					foldersHash = hashParts[1];
				} else {
					mediaHash = hashParts[1];
				}
			} else if (slashCount == 2) {
				// virtual folder hash: by date/gps/search album, folders album, media
				if (PhotoFloat.isFolderCacheBase(hashParts[1])) {
					albumHash = hashParts[0];
					foldersHash = hashParts[1];
					mediaHash = hashParts[2];
				} else {
					albumHash = hashParts[0];
					foldersHash = hashParts[1];
					mediaHash = hashParts[2];
				}
			}
		}

		if (PhotoFloat.isSearchCacheBase(albumHash)) {
			albumHashToGet = PhotoFloat.pathJoin([albumHash, foldersHash]);
			PhotoFloat.searchCacheBase = encodeURIComponent(albumHash);
		} else {
			albumHashToGet = albumHash;
			PhotoFloat.searchCacheBase = '';
		}

		albumHashes = [];
		SearchWordsFromUser = [];
		SearchWordsFromUserNormalized = [];
		if (albumHash) {
			albumHash = decodeURI(albumHash);
			if (slashCount === 0 && PhotoFloat.isSearchCacheBase(albumHash) && albumHash != Options.by_search_string) {
				var wordsWithOptionsString = albumHash.substring(Options.by_search_string.length + 1);
				var wordsAndOptions = wordsWithOptionsString.split(Options.search_options_separator);
				var wordsString = wordsAndOptions[wordsAndOptions.length - 1];
				var wordsStringOriginal = wordsString.replace(/_/g, ' ');
				// the normalized words are needed in order to compare with the search cache json files names, which are normalized
				var wordsStringNormalized = PhotoFloat.removeAccents(wordsString.toLowerCase());
				if (wordsAndOptions.length > 1) {
					var searchOptions = wordsAndOptions.slice(0, -1);
					Options.search_regex = searchOptions.indexOf('r') > -1;
					Options.search_inside_words = searchOptions.indexOf('i') > -1;
					Options.search_any_word = searchOptions.indexOf('n') > -1;
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

		if (albumHash && foldersHash === null && SearchWordsFromUser.length > 0) {
			self = this;
			// get the search root album before getting the search words ones
			this.getAlbum(
				Options.by_search_string,
				// success:
				function(bySearchRootAlbum) {
					var lastIndex, i, j, wordHashes, numSearchAlbumsReady = 0, numSubAlbumsToGet = 0, normalizedWords, albumToGet;
					var searchResultsMedia = [];
					var searchResultsSubalbums = [];
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
					// PhotoFloat.searchCacheBase = albumHash;
					if (! Options.search_any_word)
						// when serching all the words, getting the first album is enough, media that do not match the other words will be escluded later
						lastIndex = 0;
					else
						lastIndex = SearchWordsFromUser.length - 1;
					if (Options.search_inside_words) {
						// we must determine the albums that could match the words given by the user, word by word
						for (i = 0; i <= lastIndex; i ++) {
							wordHashes = [];
							for (j = 0; j < PhotoFloat.searchWordsFromJsonFile.length; j ++) {
								if (PhotoFloat.searchWordsFromJsonFile[j].indexOf(SearchWordsFromUserNormalized[i]) > -1) {
								 	wordHashes.push(Options.by_search_string + Options.cache_folder_separator + PhotoFloat.searchWordsFromJsonFile[j]);
									numSubAlbumsToGet ++;
								}
							}
							if (wordHashes.length)
								albumHashes.push(wordHashes);
						}
					} else {
						// whole words
						for (i = 0; i <= lastIndex; i ++)
							if (PhotoFloat.searchWordsFromJsonFile.indexOf(SearchWordsFromUserNormalized[i]) > -1) {
								albumHashes.push([Options.by_search_string + Options.cache_folder_separator + SearchWordsFromUserNormalized[i]]);
								numSubAlbumsToGet ++;
							}
					}

					if (numSubAlbumsToGet === 0) {
						PhotoFloat.noResults();
						callback(searchResultsAlbumFinal, null, -1);
					} else if (numSubAlbumsToGet > Options.max_search_album_number) {
						PhotoFloat.noResults('search-too-wide');
						callback(searchResultsAlbumFinal, null, -1);
					} else {
						$("#album-view").removeClass("hidden");
						$(".search-failed").hide();
						for (indexWords = 0; indexWords <= lastIndex; indexWords ++) {
							// console.log("n. album to get", albumHashes[indexWords].length);
							for (indexAlbums = 0; indexAlbums < albumHashes[indexWords].length; indexAlbums ++) {
								// getAlbum is called here with 2 more parameters, indexAlbums and indexWords, in order to know their ValueError
								// if they are not passed as arguments, the success function will see their values updates (getAlbum is an asyncronous function)
								// console.log("ialbum", indexAlbums);
								self.getAlbum(
									albumHashes[indexWords][indexAlbums],
									// success:
									function(theAlbum, thisIndexWords, thisIndexAlbums) {
										var matchingMedia = [], matchingSubalbums = [], match, indexMedia, indexSubalbums, indexWordsLeft, resultAlbum, indexWords1;

										resultAlbum = PhotoFloat.cloneObject(theAlbum);
										// media in the album still has to be filtered according to search criteria
										if (! Options.search_inside_words) {
											// whole word
											for (indexMedia = 0; indexMedia < theAlbum.media.length; indexMedia ++) {
												if (PhotoFloat.normalize(theAlbum.media[indexMedia].words).indexOf(SearchWordsFromUser[thisIndexWords]) > -1)
													matchingMedia.push(theAlbum.media[indexMedia]);
											}
											for (indexSubalbums = 0; indexSubalbums < theAlbum.subalbums.length; indexSubalbums ++) {
												if (PhotoFloat.normalize(theAlbum.subalbums[indexSubalbums].words).indexOf(SearchWordsFromUser[thisIndexWords]) > -1)
													matchingSubalbums.push(theAlbum.subalbums[indexSubalbums]);
											}
										} else {
											// inside words
											for (indexMedia = 0; indexMedia < theAlbum.media.length; indexMedia ++) {
												normalizedWords = PhotoFloat.normalize(theAlbum.media[indexMedia].words);
												if (normalizedWords.some(function(element) {
													return element.indexOf(SearchWordsFromUser[thisIndexWords]) > -1;
												}))
													matchingMedia.push(theAlbum.media[indexMedia]);
											}
											for (indexSubalbums = 0; indexSubalbums < theAlbum.subalbums.length; indexSubalbums ++) {
												normalizedWords = PhotoFloat.normalize(theAlbum.subalbums[indexSubalbums].words);
												if (normalizedWords.some(function(element) {
													return element.indexOf(SearchWordsFromUser[thisIndexWords]) > -1;
												}))
													matchingSubalbums.push(theAlbum.subalbums[indexSubalbums]);
											}
										}
										resultAlbum.media = matchingMedia;
										resultAlbum.subalbums = matchingSubalbums;

										if (! (thisIndexWords in searchResultsMedia)) {
											searchResultsMedia[thisIndexWords] = resultAlbum.media;
											searchResultsSubalbums[thisIndexWords] = resultAlbum.subalbums;
										} else {
											searchResultsMedia[thisIndexWords] = PhotoFloat.union(searchResultsMedia[thisIndexWords], resultAlbum.media);
											searchResultsSubalbums[thisIndexWords] = PhotoFloat.union(searchResultsSubalbums[thisIndexWords], resultAlbum.subalbums);
										}
										// the following instruction makes me see that numSearchAlbumsReady never reaches numSubAlbumsToGet when numSubAlbumsToGet is > 1000,
										// numSearchAlbumsReady remains < 1000
										// console.log(thisIndexAlbums, searchResultsMedia[thisIndexWords].length, numSearchAlbumsReady + 1, numSubAlbumsToGet);

										numSearchAlbumsReady ++;
										if (numSearchAlbumsReady >= numSubAlbumsToGet) {
											// all the albums have been got, we can merge the results
											searchResultsAlbumFinal.media = searchResultsMedia[0];
											searchResultsAlbumFinal.subalbums = searchResultsSubalbums[0];
											for (indexWords1 = 1; indexWords1 <= lastIndex; indexWords1 ++) {
												searchResultsAlbumFinal.media = Options.search_any_word ?
													PhotoFloat.union(searchResultsAlbumFinal.media, searchResultsMedia[indexWords1]) :
													PhotoFloat.intersect(searchResultsAlbumFinal.media, searchResultsMedia[indexWords1]);
												searchResultsAlbumFinal.subalbums = Options.search_any_word ?
													PhotoFloat.union(searchResultsAlbumFinal.subalbums, searchResultsSubalbums[indexWords1]) :
													PhotoFloat.intersect(searchResultsAlbumFinal.subalbums, searchResultsSubalbums[indexWords1]);
											}

											if (lastIndex != SearchWordsFromUser.length - 1) {
												// we still have to filter out the media that do not match the words after the first
												// we are in all words search mode
												matchingMedia = [];
												for (indexMedia = 0; indexMedia < searchResultsAlbumFinal.media.length; indexMedia ++) {
													match = true;
													if (! Options.search_inside_words) {
														// whole word
														normalizedWords = PhotoFloat.normalize(searchResultsAlbumFinal.media[indexMedia].words);
														if (SearchWordsFromUser.some(function(element, index) {
															return index > lastIndex && normalizedWords.indexOf(element) == -1;
														}))
															match = false;
													} else {
														// inside words
														for (indexWordsLeft = lastIndex + 1; indexWordsLeft < SearchWordsFromUser.length; indexWordsLeft ++) {
															normalizedWords = PhotoFloat.normalize(searchResultsAlbumFinal.media[indexMedia].words);
															if (! normalizedWords.every(function(element) {
																return normalizedWords.indexOf(SearchWordsFromUser[indexWordsLeft]) > -1;
															})) {
																match = false;
																break;
															}
														}
													}
													if (match && matchingMedia.indexOf(searchResultsAlbumFinal.media[indexMedia]) == -1)
														matchingMedia.push(searchResultsAlbumFinal.media[indexMedia]);
												}
												searchResultsAlbumFinal.media = matchingMedia;

												matchingSubalbums = [];
												for (indexSubalbums = 0; indexSubalbums < searchResultsAlbumFinal.subalbums.length; indexSubalbums ++) {
													match = true;
													if (! Options.search_inside_words) {
														// whole word
														normalizedWords = PhotoFloat.normalize(searchResultsAlbumFinal.subalbums[indexSubalbums].words);
														if (SearchWordsFromUser.some(function(element, index) {
															return index > lastIndex && normalizedWords.indexOf(element) == -1;
														}))
															match = false;
													} else {
														// inside words
														for (indexWordsLeft = lastIndex + 1; indexWordsLeft < SearchWordsFromUser.length; indexWordsLeft ++) {
															normalizedWords = PhotoFloat.normalize(searchResultsAlbumFinal.subalbums[indexSubalbums].words);
															if (! normalizedWords.every(function(element) {
																return normalizedWords.indexOf(SearchWordsFromUser[indexWordsLeft]) > -1;
															})) {
																match = false;
																break;
															}
														}
													}
													if (match && matchingSubalbums.indexOf(searchResultsAlbumFinal.subalbums[indexSubalbums]) == -1)
														matchingSubalbums.push(searchResultsAlbumFinal.subalbums[indexSubalbums]);
												}
												searchResultsAlbumFinal.subalbums = matchingSubalbums;
											}
											if (searchResultsAlbumFinal.media.length === 0 && searchResultsAlbumFinal.subalbums.length === 0) {
												PhotoFloat.noResults();
											} else if (searchResultsAlbumFinal.media.length > Options.big_virtual_folders_threshold) {
												PhotoFloat.noResults('search-too-wide');
											} else {
												$("#album-view").removeClass("hidden");
												$(".search-failed").hide();
											}
											searchResultsAlbumFinal.numMediaInAlbum = searchResultsAlbumFinal.media.length;
											searchResultsAlbumFinal.numMediaInSubTree = searchResultsAlbumFinal.media.length;
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
		} else {

			this.getAlbum(
				albumHashToGet,
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
		}
	};

	PhotoFloat.cloneObject = function(object) {
		return Object.assign({}, object);
	};

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
	};

	PhotoFloat.removeAccents = function(string) {
		return string.latinise();
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

	PhotoFloat.isByDateCacheBase = function(string) {
		return string == Options.by_date_string || string.indexOf(PhotoFloat.byDateStringWithTrailingSeparator) === 0;
	};

	PhotoFloat.isByGpsCacheBase = function(string) {
		return string == Options.by_gps_string || string.indexOf(PhotoFloat.byGpsStringWithTrailingSeparator) === 0;
	};

	PhotoFloat.isFolderCacheBase = function(string) {
		return string == Options.folders_string || string.indexOf(PhotoFloat.foldersStringWithTrailingSeparator) === 0;
	};

	PhotoFloat.isSearchCacheBase = function(string) {
		return string == Options.by_search_string || string.indexOf(PhotoFloat.bySearchStringWithTrailingSeparator) === 0;
	};


	PhotoFloat.mediaHashURIEncoded = function(album, media) {
		var hash;
		if (PhotoFloat.isByDateCacheBase(album.cacheBase) || PhotoFloat.isByGpsCacheBase(album.cacheBase))
			hash = PhotoFloat.pathJoin([
				album.cacheBase,
				media.foldersCacheBase,
				media.cacheBase
			]);
		else if (PhotoFloat.isSearchCacheBase(album.cacheBase))
			hash = PhotoFloat.pathJoin([
				PhotoFloat.searchCacheBase,
				media.foldersCacheBase,
				media.cacheBase
			]);
		else
			hash = PhotoFloat.pathJoin([
				album.cacheBase,
				media.cacheBase
			]);
		return hash;
	};
	PhotoFloat.mediaHashFolder = function(album, media) {
		var hash;
		hash = media.cacheBase;
		if (PhotoFloat.isByDateCacheBase(hash) || PhotoFloat.isByGpsCacheBase(hash)) {
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
			var actualSize = size;
			var albumThumbSize = Options.album_thumb_size;
			var mediaThumbSize = Options.media_thumb_size;
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
			if (PhotoFloat.isFolderCacheBase(hash))
				hash = hash.substring(PhotoFloat.foldersStringWithTrailingSeparator.length);
			else if (PhotoFloat.isByDateCacheBase(hash))
				hash = hash.substring(PhotoFloat.byDateStringWithTrailingSeparator.length);
			else if (PhotoFloat.isByGpsCacheBase(hash))
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
