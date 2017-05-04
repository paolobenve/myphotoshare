import os
import os.path
import sys
from datetime import datetime
from PhotoAlbum import Photo, Album, PhotoAlbumEncoder
from CachePath import *
import json

class TreeWalker:
	def __init__(self, album_path, cache_path):
		self.album_path = os.path.abspath(album_path).decode(sys.getfilesystemencoding())
		self.cache_path = os.path.abspath(cache_path).decode(sys.getfilesystemencoding())
		set_cache_path_base(self.album_path)
		self.all_albums = list()
		self.tree_by_date = {}
		self.all_photos = list()
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
		# convert the temporary structure where photos are organazide by year, month, date to a set of albums
		by_date_path = os.path.join(self.album_path, "_by_date")
		by_date_album = Album(by_date_path)
		for year, months in self.tree_by_date.iteritems():
			year_path = os.path.join(by_date_path, str(year))
			year_album = Album(year_path)
			by_date_album.add_album(year_album)
			for month, days in self.tree_by_date[year].iteritems():
				month_path = os.path.join(year_path, str(month))
				month_album = Album(month_path)
				year_album.add_album(month_album)
				for day, photos in self.tree_by_date[year][month].iteritems():
					day_path = os.path.join(month_path, str(day))
					day_album = Album(day_path)
					month_album.add_album(day_album)
					for photo in photos:
						day_album.add_photo(photo)
					self.all_albums.append(day_album)
					#day_cache = os.path.join(self.cache_path, json_name_by_date(day_path))
					if not day_album.empty:
						message("cache_path", day_path)
						day_album.cache(self.cache_path)
				self.all_albums.append(month_album)
				#month_cache = os.path.join(self.cache_path, json_name_by_date(month_path))
				if not month_album.empty:
					message("cache_path", month_path)
					month_album.cache(self.cache_path)
			self.all_albums.append(year_album)
			#year_cache = os.path.join(self.cache_path, json_name_by_date(year_path))
			if not year_album.empty:
				message("cache_path", year_path)
				year_album.cache(self.cache_path)
		self.all_albums.append(by_date_album)
		root_cache = os.path.join(self.cache_path, json_name(self.album_path))
		if not by_date_album.empty:
			#message("cache_path1", self.cache_path + "   " + os.path.basename(self.cache_path))
			by_date_album.cache(self.cache_path)
		return by_date_album
	def add_photo_to_tree_by_date(self, photo):
		# add the given photo to a temporary structure where photos are organazide by year, month, date
		if not photo.year in self.tree_by_date.keys():
			self.tree_by_date[photo.year] = {}
		if not photo.month in self.tree_by_date[photo.year].keys():
			self.tree_by_date[photo.year][photo.month] = {}
		if not photo.day in self.tree_by_date[photo.year][photo.month].keys():
			self.tree_by_date[photo.year][photo.month][photo.day] = list()
		self.tree_by_date[photo.year][photo.month][photo.day].append(photo)
	def walk(self, path):
		trimmed_path = trim_base_custom(path, self.album_path)
		path_with_marker = os.path.join(self.album_path, "_folders")
		if trimmed_path:
			path_with_marker = os.path.join(path_with_marker, trimmed_path)
		next_level()
		if not os.access(path, os.R_OK | os.X_OK):
			message("access denied", os.path.basename(path))
			back_level()
			return None
		message("walking", os.path.basename(path))
		cache = os.path.join(self.cache_path, json_name(path))
		cached = False
		cached_album = None
		if os.path.exists(cache):
			try:
				cached_album = Album.from_cache(cache)
				if file_mtime(path) <= file_mtime(cache):
					message("full cache", os.path.basename(path))
					cached = True
					album = cached_album
					for photo in album.photos:
						self.all_photos.append(photo)
						self.add_photo_to_tree_by_date(photo)
				else:
					message("partial cache", os.path.basename(path))
			except KeyboardInterrupt:
				raise
			except (ValueError, AttributeError) as e:
				message("corrupt cache", os.path.basename(path))
				cached_album = None
		if not cached:
			message("path with marker", path_with_marker)
			album = Album(path_with_marker)
		for entry in os.listdir(path):
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
			elif not cached and os.path.isfile(entry):
				next_level()
				cache_hit = False
				if cached_album:
					cached_photo = cached_album.photo_from_path(entry)
					if cached_photo and file_mtime(entry) <= cached_photo.attributes["dateTimeFile"] and file_mtime(path) <= cached_photo.attributes["dateTimeFile"]:
						message("cache hit", os.path.basename(entry))
						cache_hit = True
						photo = cached_photo
				if not cache_hit:
					message("metainfo", os.path.basename(entry))
					photo = Photo(entry, self.cache_path)
				if photo.is_valid:
					self.all_photos.append(photo)
					album.add_photo(photo)
					self.add_photo_to_tree_by_date(photo)
				else:
					message("unreadable", os.path.basename(entry))
				back_level()
		if not album.empty:
			message("caching", os.path.basename(path))
			album.cache(self.cache_path)
			self.all_albums.append(album)
		else:
			message("empty", os.path.basename(path))
		back_level()
		return album
	def big_lists(self):
		photo_list = []
		self.all_photos.sort()
		for photo in self.all_photos:
			photo_list.append(photo.path)
		message("caching", "all photos path list")
		fp = open(os.path.join(self.cache_path, "all_photos.json"), 'w')
		json.dump(photo_list, fp, cls=PhotoAlbumEncoder)
		fp.close()
	def remove_stale(self):
		message("cleanup", "building stale list")
		all_cache_entries = { "all_photos.json": True, "latest_photos.json": True }
		for album in self.all_albums:
			all_cache_entries[album.json_file] = True
		for photo in self.all_photos:
			for entry in photo.image_caches:
				all_cache_entries[entry] = True
		message("cleanup", "searching for stale cache entries")
		for cache in os.listdir(self.cache_path):
			try:
				cache = cache.decode(sys.getfilesystemencoding())
			except KeyboardInterrupt:
				raise
			except:
				pass
			if cache not in all_cache_entries:
				message("cleanup", os.path.basename(cache))
				os.unlink(os.path.join(self.cache_path, cache))
