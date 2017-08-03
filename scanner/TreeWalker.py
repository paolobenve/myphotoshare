import os
import os.path
import sys
from datetime import datetime
from PhotoAlbum import Media, Album, PhotoAlbumEncoder
from CachePath import *
import json
import Options
import re

class TreeWalker:
	def __init__(self):
		self.save_json_options()
		self.all_cache_entries= ["options.json"]
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
		[folders_album, num] = self.walk(Options.config['album_path'])
		folders_album.num_media_in_sub_tree = num
		if folders_album is None:
			message("WARNING", "ALBUMS ROOT EXCLUDED BY MARKER FILE", 2)
		else:
			self.all_cache_entries.append("all_media.json")
			self.all_cache_entries.append(Options.config['folders_string'] + ".json")
			self.save_all_media_json()
			by_date_album = self.generate_date_album()
			origin_album.add_album(folders_album)
			self.all_albums.append(origin_album)
			if by_date_album is not None and not by_date_album.empty:
				self.all_cache_entries.append(Options.config['by_date_string'] + ".json")
				origin_album.add_album(by_date_album)
			if not origin_album.empty:
				origin_album.cache(Options.config['cache_path'])
		self.remove_stale()
		message("complete", "", 4)
	def generate_date_album(self):
		# convert the temporary structure where media are organized by year, month, date to a set of albums
		by_date_path = os.path.join(Options.config['album_path'], Options.config['by_date_string'])
		by_date_album = Album(by_date_path)
		for year, months in self.tree_by_date.iteritems():
			year_path = os.path.join(by_date_path, str(year))
			year_album = Album(year_path)
			year_album.parent = by_date_album
			by_date_album.add_album(year_album)
			for month, days in self.tree_by_date[year].iteritems():
				month_path = os.path.join(year_path, str(month))
				month_album = Album(month_path)
				month_album.parent = year_album
				year_album.add_album(month_album)
				for day, media in self.tree_by_date[year][month].iteritems():
					day_path = os.path.join(month_path, str(day))
					day_album = Album(day_path)
					day_album.parent = month_album
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
		root_cache = os.path.join(Options.config['cache_path'], json_name(Options.config['album_path']))
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
		self.tree_by_date[media.year][media.month][media.day].append(media)
	def walk(self, absolute_path, parent_album = None):
		trimmed_path = trim_base_custom(absolute_path, Options.config['album_path'])
		absolute_path_with_marker = os.path.join(Options.config['album_path'], Options.config['folders_string'])
		if trimmed_path:
			absolute_path_with_marker = os.path.join(absolute_path_with_marker, trimmed_path)
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
		trimmed_json_cache_file = json_name(absolute_path_with_marker)
		json_cache_file = os.path.join(Options.config['cache_path'], trimmed_json_cache_file)
		json_cache_OK = False
		cached_album = None
		if os.path.exists(json_cache_file):
			json_message = json_cache_file + " for " + os.path.basename(absolute_path)
			try:
				cached_album = Album.from_cache(json_cache_file)
				if file_mtime(absolute_path) <= file_mtime(json_cache_file):
					message("  json cache file OK", "  " + json_message, 4)
					json_cache_OK = True
					album = cached_album
					for media in album.media:
						self.all_media.append(media)
						self.add_media_to_tree_by_date(media)
				else:
					message("  json cache file invalid (old)", json_message, 4)
			except KeyboardInterrupt:
				raise
			except (ValueError, AttributeError, KeyError) as e:
				message("  json cache file invalid", json_message, 4)
				cached_album = None
		
		if not json_cache_OK:
			album = Album(absolute_path_with_marker)
		if parent_album is not None:
			album.parent = parent_album
		message("  subdir", "  " + album.subdir, 5)
		
		for entry in sorted(os.listdir(absolute_path)):
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
				[next_walked_album, num] = self.walk(entry_with_path, album)
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
							if not os.path.exists(absolute_cache_file) or file_mtime(absolute_cache_file) > file_mtime(json_cache_file):
								cache_hit = False
								break
						if cache_hit:
							message("all reduced size and thumbnails OK", os.path.basename(entry_with_path), 4)
							media = cached_media
				if not cache_hit:
					message(" processing image/video", os.path.basename(entry_with_path), 4)
					media = Media(album, entry_with_path, Options.config['cache_path'])
				
				if media.is_valid:
					album.num_media_in_sub_tree += 1
					album.num_media_in_album += 1
					if not json_cache_OK:
						self.all_media.append(media)
						album.add_media(media)
						self.add_media_to_tree_by_date(media)
				elif not media.is_valid:
					next_level()
					message("unreadable file", ":-(", 1)
					back_level()
				back_level()
		if not album.empty:
			next_level()
			message("saving json cache file", os.path.basename(absolute_path), 4)
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
			message("cleanup", "building stale list", 4)
			for album in self.all_albums:
				self.all_cache_entries.append(album.json_file)
			for media in self.all_media:
				for entry in media.image_caches:
					self.all_cache_entries.append(entry)
		else:
			self.all_cache_entries = cache_list
		info = "in cache path"
		if subdir:
			info = "in subdir " + subdir
		message("searching", info, 4)
		deletable_files_suffixes_re ="\.json$"
		deletable_files_suffixes_re += "|_transcoded(_([1-9][0-9]{0,3}[kKmM]|[1-9][0-9]{3,10}))?\.mp4$"
		# reduced sizes, thumbnails, old style thumbnails
		deletable_files_suffixes_re += "|_[1-9][0-9]{1,4}(a|t|s|[at][sf])?\.jpg$"
		next_level()
		
		for cache_file in sorted(os.listdir(os.path.join(Options.config['cache_path'], subdir))):
			if os.path.isdir(os.path.join(Options.config['cache_path'], cache_file)):
				if not cache_file == "album":
					next_level()
					self.remove_stale(cache_file, self.all_cache_entries)
					if not os.listdir(os.path.join(Options.config['cache_path'], cache_file)):
						next_level()
						message("empty subdir, deleting", "xxxx", 4)
						back_level()
						file_to_delete = os.path.join(Options.config['cache_path'], cache_file)
						os.rmdir(os.path.join(Options.config['cache_path'], file_to_delete))
					back_level()
			else:
				cache_with_subdir = os.path.join(subdir, cache_file)
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
					if cache_with_subdir not in self.all_cache_entries:
						message("cleanup", cache_with_subdir, 4)
						file_to_delete = os.path.join(Options.config['cache_path'], cache_with_subdir)
						os.unlink(os.path.join(Options.config['cache_path'], file_to_delete))
				else:
					message("not deleting", cache_with_subdir, 2)
					continue
				
		if not subdir:
			back_level()
		back_level()
