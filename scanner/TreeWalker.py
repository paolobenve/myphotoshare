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
	def __init__(self, album_path, cache_path):
		if (Options.config['thumbnail_generation_mode'] == "parallel"):
			message("method", "parallel thumbnail generation")
		elif (Options.config['thumbnail_generation_mode'] == "mixed"):
			message("method", "mixed thumbnail generation")
		elif (Options.config['thumbnail_generation_mode'] == "cascade"):
			message("method", "cascade thumbnail generation")
			# be sure reduced_sizes array is correctly sorted 
			Options.config['reduced_sizes'].sort(reverse = True)
		self.album_path = os.path.abspath(album_path).decode(sys.getfilesystemencoding())
		self.cache_path = os.path.abspath(cache_path).decode(sys.getfilesystemencoding())
		set_cache_path_base(self.album_path)
		self.all_albums = list()
		self.tree_by_date = {}
		self.all_media = list()
		self.save_json_options()
		folders_album = self.walk(self.album_path)
		self.big_lists()
		by_date_album = self.generate_date_album()
		origin_album = Album(self.album_path)
		origin_album.add_album(folders_album)
		origin_album.add_album(by_date_album)
		self.all_albums.append(origin_album)
		#origin_cache = os.path.join(self.cache_path, json_name_by_date(self.album_path))
		if not origin_album.empty:
			origin_album.cache(self.cache_path)
		self.remove_stale()
		message("complete", "")
	def generate_date_album(self):
		# convert the temporary structure where media are organized by year, month, date to a set of albums
		by_date_path = os.path.join(self.album_path, Options.config['by_date_string'])
		by_date_album = Album(by_date_path)
		for year, months in self.tree_by_date.iteritems():
			year_path = os.path.join(by_date_path, str(year))
			year_album = Album(year_path)
			by_date_album.add_album(year_album)
			for month, days in self.tree_by_date[year].iteritems():
				month_path = os.path.join(year_path, str(month))
				month_album = Album(month_path)
				year_album.add_album(month_album)
				for day, media in self.tree_by_date[year][month].iteritems():
					day_path = os.path.join(month_path, str(day))
					day_album = Album(day_path)
					month_album.add_album(day_album)
					for single_media in media:
						day_album.add_media(single_media)
						month_album.add_media(single_media)
						year_album.add_media(single_media)
					self.all_albums.append(day_album)
					#day_cache = os.path.join(self.cache_path, json_name_by_date(day_path))
					if not day_album.empty:
						day_album.cache(self.cache_path)
				self.all_albums.append(month_album)
				#month_cache = os.path.join(self.cache_path, json_name_by_date(month_path))
				if not month_album.empty:
					month_album.cache(self.cache_path)
			self.all_albums.append(year_album)
			#year_cache = os.path.join(self.cache_path, json_name_by_date(year_path))
			if not year_album.empty:
				year_album.cache(self.cache_path)
		self.all_albums.append(by_date_album)
		root_cache = os.path.join(self.cache_path, json_name(self.album_path))
		if not by_date_album.empty:
			by_date_album.cache(self.cache_path)
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
	def walk(self, path):
		trimmed_path = trim_base_custom(path, self.album_path)
		path_with_marker = os.path.join(self.album_path, Options.config['folders_string'])
		if trimmed_path:
			path_with_marker = os.path.join(path_with_marker, trimmed_path)
		next_level()
		if not os.access(path, os.R_OK | os.X_OK):
			message("access denied", os.path.basename(path))
			back_level()
			return None
		message("Next level folder:", os.path.basename(path))
		cache = os.path.join(self.cache_path, json_name(path))
		json_cache_file = json_name(path_with_marker)
		json_cache_file = os.path.join(self.cache_path, json_cache_file)
		path_is_cached = False
		cached_album = None
		if os.path.exists(json_cache_file):
			try:
				#~ cached_album = Album.from_cache(json_cache_file)
				#~ if False and file_mtime(path) <= file_mtime(cache):
				if False and self.max_mtime_in_tree(path) <= file_mtime(json_cache_file):
					message("full cache", os.path.basename(path))
					path_is_cached = True
					album = cached_album
					for media in album.media:
						self.all_media.append(media)
						self.add_media_to_tree_by_date(media)
				else:
					message("partial cache", os.path.basename(path))
			except KeyboardInterrupt:
				raise
			#~ except (ValueError, AttributeError) as e:
				#~ message("corrupt cache", os.path.basename(path))
				#~ cached_album = None
		if not path_is_cached:
			album = Album(path_with_marker)
		for entry in sorted(os.listdir(path)):
			if entry[0] == '.':
				continue
			try:
				entry = entry.decode(sys.getfilesystemencoding())
			except KeyboardInterrupt:
				raise
			except:
				next_level()
				message("unicode error", entry.decode(sys.getfilesystemencoding(), "replace"))
				back_level()
				continue
			entry = os.path.join(path, entry)
			if os.path.isdir(entry):
				next_walked_album = self.walk(entry)
				if next_walked_album is not None:
					album.add_album(next_walked_album)
			elif not path_is_cached and os.path.isfile(entry):
				next_level()
				cache_hit = False
				if cached_album:
					cached_media = cached_album.media_from_path(entry)
					if (
						cached_media and
						file_mtime(entry) <= cached_media.attributes["dateTimeFile"]
					):
						cache_files = list()
						if "mediaType" in cached_media.attributes and cached_media.attributes["mediaType"] == "video":
							# video
							cache_files.append(os.path.join(self.cache_path, video_cache_with_subdir(entry)))
						else:
							# image
							for thumb_size in Options.config['reduced_sizes']:
								cache_files.append(os.path.join(self.cache_path, path_with_subdir(entry, thumb_size)))
							for thumb_size in (Options.config['album_thumb_size'], Options.config['media_thumb_size']):
								cache_files.append(os.path.join(self.cache_path, path_with_subdir(entry, thumb_size)))
						# at this point we have full path to cache image/video
						# check if it actually exists
						cache_hit = True
						for cache_file in cache_files:
							if not os.path.exists(cache_file):
								cache_hit = False
								break
						if cache_hit:
							message("cache hit", os.path.basename(entry))
							media = cached_media
				if not cache_hit:
					message(" processing image/video", os.path.basename(entry))
					media = Media(entry, self.cache_path)
				if media.is_valid:
					self.all_media.append(media)
					album.add_media(media)
					self.add_media_to_tree_by_date(media)
				else:
					next_level()
					message("unreadable", ":-(")
					back_level()
				back_level()
		if not album.empty:
			next_level()
			message("caching folder:", os.path.basename(path))
			back_level()
			album.cache(self.cache_path)
			self.all_albums.append(album)
		else:
			message("empty", os.path.basename(path))
		back_level()
		return album
	
	def max_mtime_in_tree(self, path):
		max_time = max(file_mtime(root) for root,_,_ in os.walk(path))
		return max_time
	
	def big_lists(self):
		media_list = []
		self.all_media.sort()
		for media in self.all_media:
			media_list.append(media.path)
		message("caching", "all media path list")
		fp = open(os.path.join(self.cache_path, "all_media.json"), 'w')
		json.dump(media_list, fp, cls=PhotoAlbumEncoder)
		fp.close()
	def save_json_options(self):
		next_level()
		try:
			json_options_file = os.path.join(Options.config['index_html_path'], 'options.json')
			fp = open(json_options_file, 'w')
			message("saving json options file", json_options_file)
		except IOError:
			json_options_file_old = json_options_file
			json_options_file = os.path.join(self.cache_path, 'options.json')
			message("saving json options file", json_options_file + " (couldn not save " + json_options_file_old + ")")
			fp = open(json_options_file, 'w')
		back_level()
		json.dump(Options.config, fp)
		fp.close()
	def remove_stale(self, subdir = "", cache_list = {}):
		if not subdir:
			message("cleanup", "building stale list")
			all_cache_entries = { "all_media.json": True, "latest_media.json": True, "options.json": True }
			for album in self.all_albums:
				all_cache_entries[album.json_file] = True
			for media in self.all_media:
				for entry in media.image_caches:
					all_cache_entries[entry] = True
			next_level()
		else:
			all_cache_entries = cache_list
		info = "in cache path"
		if subdir:
			info = "in subdir " + subdir
		message("searching", info)
		deletable_files_suffixes_re ="\.json$"
		deletable_files_suffixes_re += "|_transcoded\.mp4$"
		# reduced sizes, thumbnails, old style thumbnails
		deletable_files_suffixes_re += "|_[1-9][0-9]{1,4}(s|[at][sf])?\.jpg$"
		next_level()
		for cache in sorted(os.listdir(os.path.join(self.cache_path, subdir))):
			if os.path.isdir(os.path.join(Options.config['cache_path'], cache)):
				if not cache == "album":
					next_level()
					self.remove_stale(cache, all_cache_entries)
					if not os.listdir(os.path.join(self.cache_path, cache)):
						message("empty subdir, deleting", "xxxx")
						file_to_delete = os.path.join(self.cache_path, cache)
						os.rmdir(os.path.join(self.cache_path, file_to_delete))
					back_level()
			else:
				cache_with_subdir = os.path.join(subdir, cache)
				# only delete json's, transcoded videos, reduced images and thumbnails
				found = False
				match = re.search(deletable_files_suffixes_re, cache)
				if match:
					try:
						cache = cache.decode(sys.getfilesystemencoding())
					except KeyboardInterrupt:
						raise
					except:
						pass
					if cache_with_subdir not in all_cache_entries:
						message("cleanup", cache_with_subdir)
						file_to_delete = os.path.join(self.cache_path, cache_with_subdir)
						os.unlink(os.path.join(self.cache_path, file_to_delete))
				else:
					message("not deleting", cache_with_subdir)
					continue
				
		if not subdir:
			back_level()
		back_level()
