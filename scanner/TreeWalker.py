import os
import os.path
import sys
from datetime import datetime
from PhotoAlbum import Media, Album, PhotoAlbumEncoder
from CachePath import *
import json
import Options
import re
#~ from pprint import pprint

class TreeWalker:
	def __init__(self):
		self.save_json_options()
		self.all_cache_entries = ["options.json"]
		self.all_cache_entries_by_subdir = {}
		if (Options.config['thumbnail_generation_mode'] == "parallel"):
			message("method", "parallel thumbnail generation", 4)
		elif (Options.config['thumbnail_generation_mode'] == "mixed"):
			message("method", "mixed thumbnail generation", 4)
		elif (Options.config['thumbnail_generation_mode'] == "cascade"):
			message("method", "cascade thumbnail generation", 4)
			# be sure reduced_sizes array is correctly sorted 
			Options.config['reduced_sizes'].sort(reverse = True)
		message("Browsing", "start!", 3)
		self.all_albums = list()
		self.tree_by_date = {}
		self.all_media = list()
		origin_album = Album(Options.config['album_path'])
		origin_album.cache_base = cache_base(Options.config['album_path'])
		album_cache_base = Options.config['folders_string']
		[folders_album, num] = self.walk(Options.config['album_path'], album_cache_base, origin_album)
		folders_album.num_media_in_sub_tree = num
		if folders_album is None:
			message("WARNING", "ALBUMS ROOT EXCLUDED BY MARKER FILE", 2)
		else:
			self.all_cache_entries.append("all_media.json")
			self.all_cache_entries.append(Options.config['folders_string'] + ".json")
			self.save_all_media_json()
			by_date_album = self.generate_date_album(origin_album)
			origin_album.add_album(folders_album)
			self.all_albums.append(origin_album)
			if by_date_album is not None and not by_date_album.empty:
				self.all_cache_entries.append(Options.config['by_date_string'] + ".json")
				origin_album.add_album(by_date_album)
			if not origin_album.empty:
				origin_album.cache(Options.config['cache_path'])
		self.remove_stale()
		message("complete", "", 4)
	def generate_date_album(self, origin_album):
		# convert the temporary structure where media are organized by year, month, date to a set of albums
		by_date_path = os.path.join(Options.config['album_path'], Options.config['by_date_string'])
		by_date_album = Album(by_date_path)
		by_date_album.parent = origin_album
		by_date_album.cache_base = cache_base(by_date_path)
		for year, months in self.tree_by_date.iteritems():
			year_path = os.path.join(by_date_path, str(year))
			year_album = Album(year_path)
			year_album.parent = by_date_album
			year_album.cache_base = cache_base(year_path)
			by_date_album.add_album(year_album)
			for month, days in self.tree_by_date[year].iteritems():
				month_path = os.path.join(year_path, str(month))
				month_album = Album(month_path)
				month_album.parent = year_album
				month_album.cache_base = cache_base(month_path)
				year_album.add_album(month_album)
				for day, media in self.tree_by_date[year][month].iteritems():
					day_path = os.path.join(month_path, str(day))
					day_album = Album(day_path)
					day_album.parent = month_album
					day_album.cache_base = cache_base(day_path)
					month_album.add_album(day_album)
					for single_media in media:
						day_album.add_media(single_media)
						day_album.num_media_in_sub_tree += 1
						day_album.num_media_in_album += 1
						month_album.add_media(single_media)
						month_album.num_media_in_sub_tree += 1
						year_album.add_media(single_media)
						year_album.num_media_in_sub_tree += 1
						by_date_album.num_media_in_sub_tree += 1
					self.all_albums.append(day_album)
					#day_cache = os.path.join(Options.config['cache_path'], json_name_by_date(day_path))
					if not day_album.empty:
						day_album.cache(Options.config['cache_path'])
				self.all_albums.append(month_album)
				#month_cache = os.path.join(Options.config['cache_path'], json_name_by_date(month_path))
				if not month_album.empty:
					month_album.cache(Options.config['cache_path'])
			self.all_albums.append(year_album)
			#year_cache = os.path.join(Options.config['cache_path'], json_name_by_date(year_path))
			if not year_album.empty:
				year_album.cache(Options.config['cache_path'])
		self.all_albums.append(by_date_album)
		if not by_date_album.empty:
			by_date_album.cache(Options.config['cache_path'])
		return by_date_album
	def add_media_to_tree_by_date(self, media):
		# add the given media to a temporary structure where media are organazide by year, month, date
		if not media.year in self.tree_by_date.keys():
			self.tree_by_date[media.year] = {}
		if not media.month in self.tree_by_date[media.year].keys():
			self.tree_by_date[media.year][media.month] = {}
		if not media.day in self.tree_by_date[media.year][media.month].keys():
			self.tree_by_date[media.year][media.month][media.day] = list()
		if not any(media.media_file_name == _media.media_file_name for _media in self.tree_by_date[media.year][media.month][media.day]):
		#~ if not media in self.tree_by_date[media.year][media.month][media.day]:
			self.tree_by_date[media.year][media.month][media.day].append(media)
	def listdir_sorted_by_time(self, path):
		# this function returns the directory listing sorted by mtime
		mtime = lambda f: os.stat(os.path.join(path, f)).st_mtime
		return list(sorted(os.listdir(path), key=mtime))

	def walk(self, absolute_path, album_cache_base, parent_album = None):
		#~ trimmed_path = trim_base_custom(absolute_path, Options.config['album_path'])
		#~ absolute_path_with_marker = os.path.join(Options.config['album_path'], Options.config['folders_string'])
		#~ if trimmed_path:
			#~ absolute_path_with_marker = os.path.join(absolute_path_with_marker, trimmed_path)
		next_level()
		if not os.access(absolute_path, os.R_OK | os.X_OK):
			message("access denied", os.path.basename(absolute_path), 1)
			back_level()
			return [None, 0]
		message("Walking", os.path.basename(absolute_path), 3)
		if Options.config['exclude_tree_marker'] in os.listdir(absolute_path):
			next_level()
			message("excluded with subfolders by marker file", Options.config['exclude_tree_marker'], 4)
			back_level()
			back_level()
			return [None, 0]
		if Options.config['exclude_files_marker'] in os.listdir(absolute_path):
			next_level()
			message("files excluded by marker file", Options.config['exclude_files_marker'], 4)
			back_level()
		#~ trimmed_json_cache_file = json_name(absolute_path_with_marker)
		json_cache_file = os.path.join(Options.config['cache_path'], album_cache_base) + ".json"
		json_cache_OK = False
		cached_album = None
		#~ if os.path.exists(json_cache_file):
		json_message = json_cache_file + " (path: " + os.path.basename(absolute_path) + ")"
		try:
			cached_album = Album.from_cache(json_cache_file)
			if (
				file_mtime(absolute_path) <= file_mtime(json_cache_file) and
				hasattr(cached_album, "absolute_path") and
				cached_album.absolute_path == absolute_path
			):
				message(" json file OK", "  " + json_message, 4)
				json_cache_OK = True
				album = cached_album
				for media in album.media:
					#~ self.all_media.append(media)
					#~ self.add_media_to_tree_by_date(media)
					if not any(media.media_file_name == _media.media_file_name for _media in album.media):
					#~ found = False
					#~ for _media in album.media:
						#~ if media.media_file_name == _media.media_file_name:
							#~ found = True
					#~ if not found:
						self.all_media.append(media)
						self.add_media_to_tree_by_date(media)
			else:
				message(" json file invalid (old or invalid path)", json_message, 4)
				cached_album = None
		except KeyboardInterrupt:
			raise
		except IOError:
			message(" json file unexistent", json_message, 4)
		#~ except (ValueError, AttributeError, KeyError) as e:
			#~ message(" json file invalid", json_message, 4)
			#~ cached_album = None
		
		if not json_cache_OK:
			album = Album(absolute_path)
		if parent_album is not None:
			album.parent = parent_album
		album.cache_base = album_cache_base
		
		message("  subdir", " " + album.subdir, 3)
		
		#~ for entry in sorted(os.listdir(absolute_path)):
		for entry in self.listdir_sorted_by_time(absolute_path):
			if entry[0] == '.':
				continue
			
			try:
				entry = entry.decode(sys.getfilesystemencoding())
			except KeyboardInterrupt:
				raise
			except:
				next_level()
				message("unicode error", entry.decode(sys.getfilesystemencoding(), "replace"), 1)
				back_level()
				continue
			
			entry_with_path = os.path.join(absolute_path, entry)
			if os.path.isdir(entry_with_path):
				trimmed_path = trim_base_custom(absolute_path, Options.config['album_path'])
				entry_for_cache_base = os.path.join(Options.config['folders_string'], trimmed_path, entry)
				found = False
				#~ if json_cache_OK:
					#~ # let's search it's cache base in cached album
					#~ for _subalbum in album.albums:
						#~ if _subalbum.path == entry:
							#~ next_album_cache_base = _subalbum.cache_base
							#~ found = True
							#~ break
				#~ if not found:
				next_album_cache_base = cache_base(entry_for_cache_base, True)
				# let's avoid that different album names have the same cache base
				distinguish_suffix = 0
				while True:
					_next_album_cache_base = next_album_cache_base
					if distinguish_suffix:
						_next_album_cache_base += "_" + str(distinguish_suffix)
					cache_name_absent = True
					if any(_next_album_cache_base == _album.cache_base and absolute_path != _album.absolute_path for _album in album.albums_list):
						distinguish_suffix += 1
					#~ for _album in album.albums_list:
						#~ if _next_album_cache_base == _album.cache_base and absolute_path != _album.absolute_path:
							#~ cache_name_absent = False
							#~ distinguish_suffix += 1
							#~ break
					#~ if cache_name_absent:
					else:
						next_album_cache_base = _next_album_cache_base
						break
				[next_walked_album, num] = self.walk(entry_with_path, next_album_cache_base, album)
				album.num_media_in_sub_tree += num
				if next_walked_album is not None:
					album.add_album(next_walked_album)
			elif os.path.isfile(entry_with_path):
				if Options.config['exclude_files_marker'] in os.listdir(absolute_path):
					continue
				next_level()
				cache_hit = False
				if cached_album:
					cached_media = cached_album.media_from_path(entry_with_path)
					if (
						cached_media and
						file_mtime(entry_with_path) <= cached_media.attributes["dateTimeFile"]
					):
						cache_files = cached_media.image_caches
						# check if the cache files actually exist and are not old
						cache_hit = True
						for cache_file in cache_files:
							absolute_cache_file = os.path.join(Options.config['cache_path'], cache_file)
							if (
								Options.config['recreate_fixed_height_thumbnails'] and
								os.path.exists(absolute_cache_file) and file_mtime(absolute_cache_file) < file_mtime(json_cache_file)
							):
								# remove wide images, in order not to have blurred thumbnails
								fixed_height_thumbnail_re = "_" + str(Options.config['media_thumb_size']) + "tf\.jpg$"
								match = re.search(fixed_height_thumbnail_re, cache_file)
								if match and cached_media._attributes["metadata"]["size"][0] > cached_media._attributes["metadata"]["size"][1]:
									try:
										os.unlink(os.path.join(Options.config['cache_path'], cache_file))
										message("deleted, re-creating fixed height thumbnail", os.path.join(Options.config['cache_path'], cache_file), 3)
									except OSError:
										message("error deleting fixed height thumbnail", os.path.join(Options.config['cache_path'], cache_file), 1)
								
							#~ if not os.path.exists(absolute_cache_file) or file_mtime(absolute_cache_file) > file_mtime(json_cache_file):
							if (
								not os.path.exists(absolute_cache_file) or 
								file_mtime(absolute_cache_file) < cached_media._attributes["dateTimeFile"] or
								json_cache_OK and file_mtime(absolute_cache_file) > file_mtime(json_cache_file) or
								(Options.config['recreate_reduced_photos'] or Options.config['recreate_thumbnails'])
							):
								cache_hit = False
								break
						if cache_hit:
							message("all reduced size and thumbnails OK", os.path.basename(entry_with_path), 4)
							media = cached_media
				if not cache_hit:
					message(" processing image/video", os.path.basename(entry_with_path), 4)
					next_level()
					if not json_cache_OK:
						message("json file isn't OK", json_cache_file, 4)
					elif not os.path.exists(absolute_cache_file):
						message("unexistent", absolute_cache_file, 4)
					elif cached_media is None:
						message("file is not cached", absolute_cache_file, 4)
					elif file_mtime(absolute_cache_file) < cached_media._attributes["dateTimeFile"]:
						message("reduction/thumbnail older than media", absolute_cache_file, 4)
					elif json_cache_OK and file_mtime(absolute_cache_file) > file_mtime(json_cache_file):
						message("reduction/thumbnail newer than json file", absolute_cache_file, 4)
					
					if Options.config['recreate_reduced_photos']:
						message("reduced photo recreation requested", "", 4)
					if Options.config['recreate_thumbnails']:
						message("thumbnail recreation requested", "", 4)
					back_level()
					media = Media(album, entry_with_path, Options.config['cache_path'])
				
				if media.is_valid:
					album.num_media_in_sub_tree += 1
					album.num_media_in_album += 1
					album.add_media(media)
					#~ found = False
					#~ for _media in self.all_media:
						#~ if media.media_file_name == _media.media_file_name:
							#~ found = True
					#~ if not found:
					if not any(media.media_file_name == _media.media_file_name for _media in self.all_media):
						self.all_media.append(media)
					# following function has a check on media already present
					self.add_media_to_tree_by_date(media)
				elif not media.is_valid:
					next_level()
					message("unreadable file", entry, 1)
					back_level()
				back_level()
		if not album.empty:
			next_level()
			message("saving json file for album", os.path.basename(absolute_path), 4)
			next_level()
			message("json file name", json_cache_file, 5)
			back_level()
			back_level()
			album.cache(Options.config['cache_path'])
			self.all_albums.append(album)
		else:
			next_level()
			message("empty", os.path.basename(absolute_path), 4)
			back_level()
		back_level()
		
		
		return [album, album.num_media_in_sub_tree]
	
	def save_all_media_json(self):
		media_list = []
		self.all_media.sort()
		for media in self.all_media:
			media_list.append(media.path)
		message("caching", "all media path list", 4)
		fp = open(os.path.join(Options.config['cache_path'], "all_media.json"), 'w')
		json.dump(media_list, fp, cls=PhotoAlbumEncoder)
		fp.close()
	def save_json_options(self):
		try:
			json_options_file = os.path.join(Options.config['index_html_path'], 'options.json')
			fp = open(json_options_file, 'w')
			message("saving json options file", json_options_file, 4)
		except IOError:
			json_options_file_old = json_options_file
			json_options_file = os.path.join(Options.config['cache_path'], 'options.json')
			message("saving json options file", json_options_file + " (couldn not save " + json_options_file_old + ")", 4)
			fp = open(json_options_file, 'w')
		json.dump(Options.config, fp)
		fp.close()
	def remove_stale(self, subdir = "", cache_list = {}):
		if not subdir:
			message("Cleanup", "be patient!", 3)
			next_level()
			message("building stale list", "", 4)
			for album in self.all_albums:
				self.all_cache_entries.append(album.json_file)
			for media in self.all_media:
				album_subdir = media.album.subdir
				for entry in media.image_caches:
					entry_without_subdir = entry[len(album_subdir) + 1:]
					try:
						self.all_cache_entries_by_subdir[album_subdir].append(entry_without_subdir)
					except KeyError:
						self.all_cache_entries_by_subdir[album_subdir] = list()
						self.all_cache_entries_by_subdir[album_subdir].append(entry_without_subdir)
		if subdir:
			info = "in subdir " + subdir
			deletable_files_suffixes_re = "_transcoded(_([1-9][0-9]{0,3}[kKmM]|[1-9][0-9]{3,10})(_[1-5]?[0-9])?)?\.mp4$"
			# reduced sizes, thumbnails, old style thumbnails
			deletable_files_suffixes_re += "|_[1-9][0-9]{1,4}(a|t|s|[at][sf])?\.jpg$"
		else:
			info = "in cache path"
			deletable_files_suffixes_re ="\.json$"
		message("searching", info, 4)
		
		next_level()
		
		for cache_file in sorted(os.listdir(os.path.join(Options.config['cache_path'], subdir))):
			if os.path.isdir(os.path.join(Options.config['cache_path'], cache_file)):
				if cache_file == "album":
					continue
				next_level()
				self.remove_stale(cache_file)
				if not os.listdir(os.path.join(Options.config['cache_path'], cache_file)):
					next_level()
					message("empty subdir, deleting", "xxxx", 4)
					back_level()
					file_to_delete = os.path.join(Options.config['cache_path'], cache_file)
					os.rmdir(os.path.join(Options.config['cache_path'], file_to_delete))
				back_level()
			else:
				# only delete json's, transcoded videos, reduced images and thumbnails
				found = False
				match = re.search(deletable_files_suffixes_re, cache_file)
				if match:
					try:
						cache_file = cache_file.decode(sys.getfilesystemencoding())
					except KeyboardInterrupt:
						raise
					#~ except:
						#~ pass
					if subdir:
						if subdir in self.all_cache_entries_by_subdir:
							cache_list = self.all_cache_entries_by_subdir[subdir]
						else:
							cache_list = list()
					else:
						cache_list = self.all_cache_entries
					if cache_file not in cache_list:
						message("cleanup", cache_file, 3)
						file_to_delete = os.path.join(Options.config['cache_path'], subdir, cache_file)
						os.unlink(file_to_delete)
				else:
					message("not deleting", cache_file, 2)
					continue
				
		if not subdir:
			back_level()
		back_level()
