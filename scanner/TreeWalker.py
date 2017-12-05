import os
import os.path
import sys
from datetime import datetime
from PhotoAlbum import Media, Album, PhotoAlbumEncoder
from CachePath import *
from Geonames import *
import json
import Options
import re
import time
import random
import math
from PIL import Image
from pprint import pprint
import pprint

class TreeWalker:
	def __init__(self):
		random.seed()
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
		self.media_with_gps_data_list = list()
		self.media_with_gps_data_list_is_sorted = True
		self.gps_cluster_list = list()
		self.all_media = list()
		self.all_album_composite_images = list()
		self.album_cache_path = os.path.join(Options.config['cache_path'], Options.config['cache_album_subdir'])
		if os.path.exists(self.album_cache_path):
			if not os.access(self.album_cache_path, os.W_OK):
				message("FATAL ERROR", self.album_cache_path + " not writable, quitting")
				sys.exit(-97)
		else:
			message("creating still unexistent album cache subdir", self.album_cache_path, 4)
			os.makedirs(self.album_cache_path)
			next_level()
			message("created still unexistent subdir", "", 5)
			back_level()

		self.origin_album = Album(Options.config['album_path'])
		self.origin_album.cache_base = cache_base(Options.config['album_path'])
		album_cache_base = Options.config['folders_string']
		[folders_album, num, max_file_date] = self.walk(Options.config['album_path'], album_cache_base, self.origin_album)
		if folders_album is None:
			message("WARNING", "ALBUMS ROOT EXCLUDED BY MARKER FILE", 2)
		else:
			message("saving all media json file...", "", 4)
			self.save_all_media_json()
			next_level()
			message("saved all media json file", "", 5)
			back_level()

			self.all_cache_entries.append("all_media.json")

			folders_album.num_media_in_sub_tree = num
			self.origin_album.add_album(folders_album)
			self.all_cache_entries.append(Options.config['folders_string'] + ".json")

			message("generating date albums...", "", 4)
			by_date_album = self.generate_date_albums(self.origin_album)
			next_level()
			message("generated date albums", "", 5)
			back_level()
			if by_date_album is not None and not by_date_album.empty:
				self.all_cache_entries.append(Options.config['by_date_string'] + ".json")
				self.origin_album.add_album(by_date_album)

			# gps albums cannot be generated like date albums, because we must determine media clustering and upper levels clusterings
			# so the work flow is:
			# - sort media so that clustering is more predictable
			# - group media into clusters according to smaller distances
			# - group first level clusters into cluster for following level distance, and so on

			if self.media_with_gps_data_list:
				message("sorting gps list...", "", 4)
				self.sort_media_with_gps_data_list()
				next_level()
				message("gps list sorted", "", 5)
				back_level()

				message("generating gps clusters...", "", 4)
				for media in self.media_with_gps_data_list:
					self.add_media_to_gps_cluster_list(media)
				next_level()
				message("gps clusters generated", "", 5)
				back_level()

				message("generating gps tree...", "", 4)
				gps_tree = self.generate_gps_tree()
				next_level()
				message("generated gps tree", "", 5)
				back_level()

				message("generating gps albums...", "", 4)
				by_gps_album = self.generate_gps_albums(self.origin_album, gps_tree, Options.config['by_gps_string'])
				next_level()
				message("gps albums generated", "", 5)
				back_level()

				self.all_albums.append(self.origin_album)
				self.all_cache_entries.append(Options.config['by_gps_string'] + ".json")
				self.origin_album.add_album(by_gps_album)

			self.all_albums_to_json_file(self.origin_album)
		self.remove_stale()
		message("complete", "", 4)

	def all_albums_to_json_file(self, album):
		for sub_album in album.albums_list:
			self.all_albums_to_json_file(sub_album)
		album.to_json_file()

	def add_media_to_gps_data_list(self, media):
		if media.has_gps_data and not any(media.media_file_name == _media.media_file_name for _media in self.media_with_gps_data_list):
			self.media_with_gps_data_list.append(media)
			self.media_with_gps_data_list_is_sorted = False


	def sort_media_with_gps_data_list(self):
		if not self.media_with_gps_data_list_is_sorted:
			self.media_with_gps_data_list.sort(key=lambda _m: _m.latitude + _m.longitude)
			self.media_with_gps_data_list_is_sorted = True

	def generate_gps_albums(self, up_album, cluster_list, current_path):
		next_level()
		# reads the list of media with gps data and generates the corresponding set of albums
		# works recursively on clustering_distances

		path = os.path.join(Options.config['album_path'], current_path)
		album = Album(path)
		album.parent = up_album
		album.cache_base = cache_base(path)

		smallest_cluster = False
		max_file_date = None
		if not isinstance(cluster_list, list):
			cluster_list = [cluster_list]
			smallest_cluster = True

		album_index = 0
		for cluster in cluster_list:
			sub_path = os.path.join(current_path, str(album_index))
			if not smallest_cluster:
				if 'cluster_list' in cluster:
					sub_album = self.generate_gps_albums(album, cluster['cluster_list'], sub_path)
				else:
					# we are at the smallest distance cluster level:
					# cluster_list is a list of one object with only "center" and "media_list" attributes
					# we call the generation function with that object instead of a list
					sub_album = self.generate_gps_albums(album, cluster, sub_path)
					# sub_album.num_media_in_album += len(cluster['media_list'])
				album.add_album(sub_album)
				album.num_media_in_sub_tree += len(cluster['media_list'])
				sub_album.num_media_in_album = len(cluster['media_list'])
			album.center = {}
			album.center['latitude'] = cluster['center']['latitude']
			album.center['longitude'] = cluster['center']['longitude']
			geoname = Geonames()
			album.geonames = geoname.lookup_nearby_place(album.center['latitude'], album.center['longitude'])
			# album.geonames is a dictionary with this data:
			#  'country_name': the country name in given language
			#  'country_code': the ISO country code
			#  'admin_name_1': the administrative name (the region in normal states, the state in federative states) in given language
			#  'admin_code_1': the corresponding geonames code
			#  'name': the nearby place name
			#  'geoname_id': the nearby place geonames id
			#  'distance': the distance between given coordinates and nearby place geonames coordinates

			for i, current_media in enumerate(cluster['media_list']):
				if not 'cluster_list' in cluster:
					# print "--- ", current_media, sub_path
					cluster['media_list'][i].gps_path = current_path
					# pprint.pprint(current_media)
				album.add_media(current_media)
				current_media_date = max(current_media._attributes["dateTimeFile"], current_media._attributes["dateTimeDir"])
				if max_file_date:
					max_file_date = max(max_file_date, current_media_date)
				else:
					max_file_date = current_media_date
			album_index += 1

		self.all_albums.append(album)
		if album.num_media_in_sub_tree > 0:
			self.generate_composite_image(album, max_file_date)
		back_level()
		return album


	def generate_date_albums(self, origin_album):
		next_level()
		# convert the temporary structure where media are organized by year, month, date to a set of albums

		by_date_path = os.path.join(Options.config['album_path'], Options.config['by_date_string'])
		by_date_album = Album(by_date_path)
		by_date_album.parent = origin_album
		by_date_album.cache_base = cache_base(by_date_path)
		by_date_max_file_date = None
		for year, months in self.tree_by_date.iteritems():
			year_path = os.path.join(by_date_path, str(year))
			year_album = Album(year_path)
			year_album.parent = by_date_album
			year_album.cache_base = cache_base(year_path)
			year_max_file_date = None
			by_date_album.add_album(year_album)
			for month, days in self.tree_by_date[year].iteritems():
				month_path = os.path.join(year_path, str(month))
				month_album = Album(month_path)
				month_album.parent = year_album
				month_album.cache_base = cache_base(month_path)
				month_max_file_date = None
				year_album.add_album(month_album)
				for day, media in self.tree_by_date[year][month].iteritems():
					message("elaborating day album...", "", 5)
					day_path = os.path.join(month_path, str(day))
					day_album = Album(day_path)
					day_album.parent = month_album
					day_album.cache_base = cache_base(day_path)
					day_max_file_date = None
					month_album.add_album(day_album)
					for single_media in media:
						day_album.add_media(single_media)
						day_album.num_media_in_sub_tree += 1
						day_album.num_media_in_album += 1
						month_album.add_media(single_media)
						month_album.num_media_in_sub_tree += 1
						year_album.add_media(single_media)
						year_album.num_media_in_sub_tree += 1
						by_date_album.add_media(single_media)
						by_date_album.num_media_in_sub_tree += 1
						single_media_date = max(single_media._attributes["dateTimeFile"], single_media._attributes["dateTimeDir"])
						if day_max_file_date:
							day_max_file_date = max(day_max_file_date, single_media_date)
						else:
							day_max_file_date = single_media_date
						if month_max_file_date:
							month_max_file_date = max(month_max_file_date, single_media_date)
						else:
							month_max_file_date = single_media_date
						if year_max_file_date:
							year_max_file_date = max(year_max_file_date, single_media_date)
						else:
							year_max_file_date = single_media_date
						if by_date_max_file_date:
							by_date_max_file_date = max(by_date_max_file_date, single_media_date)
						else:
							by_date_max_file_date = single_media_date
					self.all_albums.append(day_album)
					next_level()
					message("day album elaborated", media[0].year + "-" + media[0].month + "-" + media[0].day, 4)
					back_level()
					self.generate_composite_image(day_album, day_max_file_date)
				self.all_albums.append(month_album)
				self.generate_composite_image(month_album, month_max_file_date)
			self.all_albums.append(year_album)
			self.generate_composite_image(year_album, year_max_file_date)
		self.all_albums.append(by_date_album)
		if by_date_album.num_media_in_sub_tree > 0:
			self.generate_composite_image(by_date_album, by_date_max_file_date)
		back_level()
		return by_date_album

	def add_media_to_tree_by_date(self, media):
		# add the given media to a temporary structure where media are organized by year, month, date

		if not media.year in self.tree_by_date.keys():
			self.tree_by_date[media.year] = {}
		if not media.month in self.tree_by_date[media.year].keys():
			self.tree_by_date[media.year][media.month] = {}
		if not media.day in self.tree_by_date[media.year][media.month].keys():
			self.tree_by_date[media.year][media.month][media.day] = list()
		if not any(media.media_file_name == _media.media_file_name for _media in self.tree_by_date[media.year][media.month][media.day]):
		#~ if not media in self.tree_by_date[media.year][media.month][media.day]:
			self.tree_by_date[media.year][media.month][media.day].append(media)

	def add_media_to_gps_cluster_list(self, media):
		# adds the given media to a temporary structure where media are organized by gps according to various clustering distances

		found_cluster = False
		smallest_distance = Options.config['clustering_distances'][0]
		# check if media falls short with any of media in already generated clusters
		for cluster in self.gps_cluster_list:
			if any(self.distance_between_media(media, _media) < smallest_distance for _media in cluster['media_list']):
				# add media to this cluster
				cluster['center']['latitude'] = self.recalculate_mean(cluster['center']['latitude'], len(cluster['media_list']), media.latitude)
				cluster['center']['longitude'] = self.recalculate_mean(cluster['center']['longitude'], len(cluster['media_list']), media.longitude)
				cluster['media_list'].append(media)
				found_cluster = True
				break
		if not found_cluster:
			# make a new cluster
			new_cluster = {}
			new_cluster['center'] = {}
			new_cluster['center']['latitude'] = media.latitude
			new_cluster['center']['longitude'] = media.longitude
			new_cluster['media_list'] = list()
			new_cluster['media_list'].append(media)
			self.gps_cluster_list.append(new_cluster)

	def generate_gps_tree(self):
		# converts the gps_cluster_list to a tree of lists (like the date one, but date one is a tree of objects)

		# first, starting from the smallest distance clusters, the clusters for the second smallest distance are to be generated, and so on
		cluster_list = self.gps_cluster_list[:]
		for _distance in Options.config['clustering_distances']:
			if _distance == Options.config['clustering_distances'][0]:
				continue
			fathers = list()
			for cluster in cluster_list:
				if any(self.distance_between_coordinates(cluster['center']['latitude'], cluster['center']['longitude'], father['center']['latitude'], father['center']['longitude']) < _distance
							for father in fathers):
					# add cluster to this father
					father['center']['latitude'] = self.recalculate_mean(father['center']['latitude'], len(father['media_list']), cluster['center']['latitude'], len(cluster['media_list']))
					father['center']['longitude'] = self.recalculate_mean(father['center']['longitude'], len(father['media_list']), cluster['center']['longitude'], len(cluster['media_list']))
					father['media_list'].extend(cluster['media_list'])
					father['cluster_list'].append(cluster)
				else:
					# make a new cluster
					father = {}
					father['cluster_list'] = list()
					father['center'] = {}
					father['center']['latitude'] = cluster['center']['latitude']
					father['center']['longitude'] = cluster['center']['longitude']
					father['media_list'] = cluster['media_list'][:]
					father['cluster_list'].append(cluster)
					fathers.append(father)

			# prepare for next distance
			cluster_list = fathers[:]

		return fathers

	def recalculate_mean(self, old_mean, old_len, new_value, new_len = 1):
		return (old_mean * old_len + new_value * new_len) / (old_len + new_len)


	def distance_between_media(self, media1, media2):
		# calculate the distance between the media gps coordinates
		lat1 = media1.latitude
		lon1 = media1.longitude
		lat2 = media2.latitude
		lon2 = media2.longitude

		return self.distance_between_coordinates(lat1, lon1, lat2, lon2)

	def distance_between_coordinates(self, lat1, lon1, lat2, lon2):
		# https://gis.stackexchange.com/questions/61924/python-gdal-degrees-to-meters-without-reprojecting
		# Calculate the great circle distance between two points on the earth (specified in decimal degrees)

		# convert decimal degrees to radians
		r_lon1, r_lat1, r_lon2, r_lat2 = map(math.radians, [lon1, lat1, lon2, lat2])
		# haversine formula
		d_r_lon = r_lon2 - r_lon1
		d_r_lat = r_lat2 - r_lat1
		a = math.sin(d_r_lat / 2.0) ** 2 + math.cos(r_lat1) * math.cos(r_lat2) * math.sin(d_r_lon / 2.0) ** 2
		c = 2.0 * math.asin(math.sqrt(a))
		m = 6371.0 * c * 1000.0
		return m

	def listdir_sorted_by_time(self, path):
		# this function returns the directory listing sorted by mtime
		# it takes into account the fact that the file is a symlink to an unexistent file
		mtime = lambda f: os.path.exists(os.path.join(path, f)) and os.stat(os.path.join(path, f)).st_mtime or time.mktime(datetime.now().timetuple())
		return list(sorted(os.listdir(path), key=mtime))

	def walk(self, absolute_path, album_cache_base, parent_album = None):
		#~ trimmed_path = trim_base_custom(absolute_path, Options.config['album_path'])
		#~ absolute_path_with_marker = os.path.join(Options.config['album_path'], Options.config['folders_string'])
		#~ if trimmed_path:
			#~ absolute_path_with_marker = os.path.join(absolute_path_with_marker, trimmed_path)
		max_file_date = file_mtime(absolute_path)
		message("Walking                                 ", os.path.basename(absolute_path), 3)
		next_level()
		message("cache base", album_cache_base, 4)
		if not os.access(absolute_path, os.R_OK | os.X_OK):
			message("access denied to directory", os.path.basename(absolute_path), 1)
			back_level()
			return [None, 0, None]
		listdir = os.listdir(absolute_path)
		if Options.config['exclude_tree_marker'] in listdir:
			next_level()
			message("excluded with subfolders by marker file", Options.config['exclude_tree_marker'], 4)
			back_level()
			back_level()
			return [None, 0, None]
		skip_files = False
		if Options.config['exclude_files_marker'] in listdir:
			next_level()
			message("files excluded by marker file", Options.config['exclude_files_marker'], 4)
			skip_files = True
			back_level()
		json_file = os.path.join(Options.config['cache_path'], album_cache_base) + ".json"
		json_file_OK = False
		cached_album = None
		json_message = json_file + " (path: " + os.path.basename(absolute_path) + ")"
		try:
			if os.path.exists(json_file):
				if not os.access(json_file, os.R_OK):
					message("json file unreadable", json_file, 1)
				elif not os.access(json_file, os.W_OK):
					message("json file unwritable", json_file, 1)
				else:
					message("reading json file to import album...", json_file, 5)
					# the following is the instruction which could raise the error
					cached_album = Album.from_cache(json_file, album_cache_base)
					next_level()
					message("json file read", "", 5)
					back_level()
					if (
						file_mtime(absolute_path) <= file_mtime(json_file) and
						cached_album is not None and
						hasattr(cached_album, "absolute_path") and
						cached_album.absolute_path == absolute_path and
						hasattr(cached_album, "json_version") and cached_album.json_version == Options.json_version
					):
						next_level()
						message("json file is OK", "  " + json_message, 4)
						back_level()
						json_file_OK = True
						album = cached_album
						message("adding media in album to big lists...", "", 5)
						for media in album.media:
							if not any(media.media_file_name == _media.media_file_name for _media in album.media):
								self.all_media.append(media)
								self.add_media_to_tree_by_date(media)
								self.add_media_to_gps_data_list(media)
						next_level()
						message("added media to big lists", "", 5)
						back_level()
					else:
						next_level()
						message("json file invalid (old or invalid path)", json_message, 4)
						back_level()
						cached_album = None
		except KeyboardInterrupt:
			raise
		except IOError:
			next_level()
			message("json file unexistent", json_message, 4)
			back_level()
		except (ValueError, AttributeError, KeyError) as e:
			message(" json file invalid", json_message, 4)
			cached_album = None

		if not json_file_OK:
			message("generating album...", absolute_path, 5)
			album = Album(absolute_path)
			next_level()
			message("album generated", "", 5)
			back_level()
		if parent_album is not None:
			album.parent = parent_album
		album.cache_base = album_cache_base

		message("subdir for cache files", " " + album.subdir, 3)

		#~ for entry in sorted(os.listdir(absolute_path)):
		message("reading directory...", absolute_path, 5)
		for entry in self.listdir_sorted_by_time(absolute_path):
			try:
				entry = entry.decode(sys.getfilesystemencoding())
			except KeyboardInterrupt:
				raise
			except:
				next_level()
				message("unicode error", entry.decode(sys.getfilesystemencoding(), "replace"), 1)
				back_level()
				continue

			if entry[0] == '.':
				# skip hidden files and directories
				continue

			entry_with_path = os.path.join(absolute_path, entry)
			if not os.path.exists(entry_with_path):
				next_level()
				message("unexistent file, perhaps a symlink, skipping", entry_with_path, 2)
				back_level()
			elif not os.access(entry_with_path, os.R_OK):
				next_level()
				message("unreadable file", entry_with_path, 2)
				back_level()
			elif os.path.islink(entry_with_path) and not Options.config['follow_symlinks']:
				# this way file symlink are skippe too: may be symlinks can be checked only for directories?
				next_level()
				message("symlink, skipping as set in options", entry_with_path, 3)
				back_level()
			elif os.path.isdir(entry_with_path):
				trimmed_path = trim_base_custom(absolute_path, Options.config['album_path'])
				entry_for_cache_base = os.path.join(Options.config['folders_string'], trimmed_path, entry)
				message("determining cache base...", "", 5)
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
					else:
						next_album_cache_base = _next_album_cache_base
						break
				next_level()
				message("determined cache base", "", 5)
				back_level()
				[next_walked_album, num, sub_max_file_date] = self.walk(entry_with_path, next_album_cache_base, album)
				if next_walked_album is not None:
					max_file_date = max(max_file_date, sub_max_file_date)
					album.num_media_in_sub_tree += num
					album.add_album(next_walked_album)
			elif os.path.isfile(entry_with_path):
				if skip_files:
					continue
				next_level()
				cache_hit = False
				mtime = file_mtime(entry_with_path)
				max_file_date = max(max_file_date, mtime)
				if cached_album:
					message("reading cache media from cached album...", "", 5)
					cached_media = cached_album.media_from_path(entry_with_path)
					next_level()
					message("cache media read", "", 5)
					back_level()
					if (
						cached_media and
						mtime != cached_media.attributes["dateTimeFile"]
					):
						cache_files = cached_media.image_caches
						# check if the cache files actually exist and are not old
						cache_hit = True
						for cache_file in cache_files:
							absolute_cache_file = os.path.join(Options.config['cache_path'], cache_file)
							if (
								Options.config['recreate_fixed_height_thumbnails'] and
								os.path.exists(absolute_cache_file) and file_mtime(absolute_cache_file) < file_mtime(json_file)
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

							if (
								not os.path.exists(absolute_cache_file) or
								json_file_OK and (
									file_mtime(absolute_cache_file) < cached_media._attributes["dateTimeFile"] or
									file_mtime(absolute_cache_file) > file_mtime(json_file)
								) or
								(Options.config['recreate_reduced_photos'] or Options.config['recreate_thumbnails'])
							):
								cache_hit = False
								break
						if cache_hit:
							if media._attributes["mediaType"] == "video":
								message("reduced size transcoded video and thumbnails OK", os.path.basename(entry_with_path), 4)
							else:
								message("reduced size images and thumbnails OK", os.path.basename(entry_with_path), 4)
							media = cached_media
						#~ else:
							#~ absolute_cache_file = ""
				if not cache_hit:
					message("processing file", entry_with_path, 4)
					next_level()
					if not json_file_OK:
						message("json file not OK", "  " + json_message, 4)
					else:
						if cached_media is None:
							message("media not cached", "", 4)
						elif cache_hit:
							if not os.path.exists(absolute_cache_file):
								message("unexistent reduction/thumbnail", absolute_cache_file, 4)
							else:
								if file_mtime(absolute_cache_file) < cached_media._attributes["dateTimeFile"]:
									message("reduction/thumbnail older than cached media", absolute_cache_file, 4)
								elif file_mtime(absolute_cache_file) > file_mtime(json_file):
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
					if media._attributes["mediaType"] == "video":
						Options.num_video += 1
						if not cache_hit:
							Options.num_video_processed += 1
					else:
						Options.num_photo += 1
						if not cache_hit:
							Options.num_photo_processed += 1
					message("adding media to album...", "", 5)
					album.add_media(media)
					next_level()
					message("added media to album", "", 5)
					back_level()
					message("adding media to gps list...", "", 5)
					self.add_media_to_gps_data_list(media)
					next_level()
					message("added media to gps list", "", 5)
					back_level()
					message("adding media to big list...", "", 5)
					if not any(media.media_file_name == _media.media_file_name for _media in self.all_media):
						self.all_media.append(media)
					next_level()
					message("added media to big list", "", 5)
					back_level()

					# the following function has a check on media already present
					message("adding media to by date tree...", "", 5)
					self.add_media_to_tree_by_date(media)
					next_level()
					message("added media to by date tree", "", 5)
					back_level()

					# the following function has a check on media already present
				elif not media.is_valid:
					next_level()
					message("not image nor video", entry_with_path, 1)
					back_level()
				back_level()
		if not album.empty:
			next_level()
			message("adding album to big list...", "", 5)
			self.all_albums.append(album)
			next_level()
			message("added album to big list", "", 4)
			back_level()
			back_level()
		else:
			message("VOID: no media in this directory", os.path.basename(absolute_path), 4)

		if album.num_media_in_sub_tree:
			# generate the album composite image for sharing
			self.generate_composite_image(album, max_file_date)
		back_level()

		return [album, album.num_media_in_sub_tree, max_file_date]

	def index_to_coords(self, index, tile_width, px_between_tiles, side_off_set, linear_number_of_tiles):
		x = side_off_set + (index % linear_number_of_tiles) * (tile_width + px_between_tiles)
		y = side_off_set + int(index / linear_number_of_tiles) * (tile_width + px_between_tiles)
		return [x, y]

	def pick_random_image(self, album, random_number):
		if random_number < len(album.media_list):
			return [album.media_list[random_number], random_number]
		else:
			random_number -= len(album.media_list)
			for subalbum in album.albums_list:
				if random_number < subalbum.num_media_in_sub_tree:
					[picked_image, random_number] = self.pick_random_image(subalbum, random_number)
					if picked_image:
						return [picked_image, random_number]
				random_number -= subalbum.num_media_in_sub_tree
		return [None, random_number]

	def generate_composite_image(self, album, max_file_date):
		composite_image_name = album.cache_base + ".jpg"
		self.all_album_composite_images.append(composite_image_name)
		composite_image_path = os.path.join(self.album_cache_path, composite_image_name)
		json_file_with_path = os.path.join(Options.config['cache_path'], album.json_file)
		if (os.path.exists(composite_image_path) and
			file_mtime(composite_image_path) > max_file_date and
			os.path.exists(json_file_with_path) and
			file_mtime(json_file_with_path) < file_mtime(composite_image_path)
		):
			message("composite image OK", "", 5)
			with open(composite_image_path, 'a'):
				os.utime(composite_image_path, None)
			next_level()
			message("composite image OK, touched", composite_image_path, 4)
			back_level()
			return

		message("generating composite image...", composite_image_path, 5)

		# pick a maximum of Options.max_album_share_thumbnails_number random images in album and subalbums
		# and generate a square composite image

		# determine the number of images to use
		if album.num_media_in_sub_tree == 1 or Options.config['max_album_share_thumbnails_number'] == 1:
			max_thumbnail_number = 1
		elif album.num_media_in_sub_tree < 9 or Options.config['max_album_share_thumbnails_number'] == 4:
			max_thumbnail_number = 4
		elif album.num_media_in_sub_tree < 16 or Options.config['max_album_share_thumbnails_number'] == 9:
			max_thumbnail_number = 9
		elif album.num_media_in_sub_tree < 25 or Options.config['max_album_share_thumbnails_number'] == 16:
			max_thumbnail_number = 16
		elif album.num_media_in_sub_tree < 36 or Options.config['max_album_share_thumbnails_number'] == 25:
			max_thumbnail_number = 25
		else:
			max_thumbnail_number = Options.config['max_album_share_thumbnails_number']

		# pick max_thumbnail_number random square album thumbnails
		random_thumbnails = list()
		random_list = list()
		bad_list = list()
		num_random_thumbnails = min(max_thumbnail_number, album.num_media_in_sub_tree)
		i = 0
		good_media_number = album.num_media_in_sub_tree
		while True:
			if i >= good_media_number:
				break
			if num_random_thumbnails == 1:
				random_media = album.media[0]
			else:
				while True:
					random_number = random.randint(0, album.num_media_in_sub_tree - 1)
					if random_number not in random_list and random_number not in bad_list:
						break
				random_list.append(random_number)
				[random_media, random_number] = self.pick_random_image(album, random_number)
			folder_prefix = remove_folders_marker(random_media.album.cache_base)
			if folder_prefix:
				folder_prefix += Options.config['cache_folder_separator']
			thumbnail = os.path.join(
					Options.config['cache_path'],
					random_media.album.subdir,
					folder_prefix + random_media.cache_base
				) + "_" + str(Options.config['album_thumb_size']) + "as.jpg"
			if os.path.exists(thumbnail):
				random_thumbnails.append(thumbnail)
				i += 1
				if i == num_random_thumbnails:
					break
			else:
				message("unexistent thumbnail " + thumbnail + ", i=" + i, "good=", good_media_number, 5)
				bad_list.append(thumbnail)
				good_media_number -= 1

		if len(random_thumbnails) < max_thumbnail_number:
			# add the missing images: repeat the present ones
			for i in range(max_thumbnail_number - len(random_thumbnails)):
				random_thumbnails.append(random_thumbnails[i])

		# generate the composite image
		# following code inspired from
		# https://stackoverflow.com/questions/30429383/combine-16-images-into-1-big-image-with-php#30429557
		# thanks to Adarsh Vardhan who wrote it!

		tile_width = Options.config['album_thumb_size']
		tile_height = Options.config['album_thumb_size']

		# INIT BASE IMAGE FILLED WITH BACKGROUND COLOR
		linear_number_of_tiles = int(math.sqrt(max_thumbnail_number))
		px_between_tiles = 1
		side_off_set = 1

		map_width = side_off_set + (tile_width + px_between_tiles) * linear_number_of_tiles - px_between_tiles + side_off_set;
		map_height = side_off_set + (tile_width + px_between_tiles) * linear_number_of_tiles - px_between_tiles + side_off_set;
		img = Image.new( 'RGB', (map_width, map_height), "white")

		# PUT SRC IMAGES ON BASE IMAGE
		index = -1
		for thumbnail in random_thumbnails:
			index += 1
			tile = Image.open(thumbnail)
			tile_img_width = tile.size[0]
			tile_img_height = tile.size[1]
			[x, y] = self.index_to_coords(index, tile_width, px_between_tiles, side_off_set, linear_number_of_tiles)
			if tile_img_width < tile_width:
				x += int(float(tile_width - tile_img_width) / 2)
			if tile_img_height < tile_width:
				y += int(float(tile_width - tile_img_height) / 2)
			img.paste(tile, (x, y))

		# save the composite image
		img.save(composite_image_path, "JPEG", quality=Options.config['jpeg_quality'])
		next_level()
		message("generated composite image", "", 5)
		back_level()

	def save_all_media_json(self):
		media_list = []
		message("sorting media list...", "", 5)
		self.all_media.sort()
		next_level()
		message("sorted media list", "", 5)
		back_level()
		message("building media path list...", "", 5)
		for media in self.all_media:
			media_list.append(media.path)
		next_level()
		message("built media path list", "", 5)
		back_level()
		message("caching all media path list...", "", 4)
		with open(os.path.join(Options.config['cache_path'], "all_media.json"), 'w') as fp:
			json.dump(media_list, fp, cls=PhotoAlbumEncoder)
		message("cached all media path list", "", 5)
		fp.close()
	def save_json_options(self):
		json_options_file = os.path.join(Options.config['cache_path'], 'options.json')
		message("saving json options file...", json_options_file, 4)
		with open(json_options_file, 'w') as fp:
			json.dump(Options.config, fp)
		next_level()
		message("saved json options file", "", 5)
		back_level()

	def remove_stale(self, subdir = ""):
		if not subdir:
			next_level()
			message("cleaning up, be patient...", "", 3)
			next_level()
			message("building stale list...", "", 4)
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
			next_level()
			message("built stale list", "", 5)
			back_level()
			info = "in cache path"
			deletable_files_suffixes_re ="\.json$"
		else:
			info = "in subdir " + subdir
			# reduced sizes, thumbnails, old style thumbnails
			if subdir == Options.config['cache_album_subdir']:
				self.all_cache_entries_by_subdir[subdir] = list()
				for path in self.all_album_composite_images:
					self.all_cache_entries_by_subdir[subdir].append(path)
				deletable_files_suffixes_re = "\.jpg$"
			else:
				deletable_files_suffixes_re = "_transcoded(_([1-9][0-9]{0,3}[kKmM]|[1-9][0-9]{3,10})(_[1-5]?[0-9])?)?\.mp4$"
				deletable_files_suffixes_re += "|_[1-9][0-9]{1,4}(a|t|s|[at][sf])?\.jpg$"
		message("searching for stale cache files", info, 4)

		for cache_file in sorted(os.listdir(os.path.join(Options.config['cache_path'], subdir))):
			if os.path.isdir(os.path.join(Options.config['cache_path'], cache_file)):
				self.remove_stale(cache_file)
				if not os.listdir(os.path.join(Options.config['cache_path'], cache_file)):
					next_level()
					message("empty subdir, deleting...", "", 4)
					file_to_delete = os.path.join(Options.config['cache_path'], cache_file)
					next_level()
					os.rmdir(os.path.join(Options.config['cache_path'], file_to_delete))
					message("empty subdir, deleted", "", 5)
					back_level()
					back_level()
			else:
				# only delete json's, transcoded videos, reduced images and thumbnails
				next_level()
				message("deciding whether to keep a cache file...", "", 7)
				match = re.search(deletable_files_suffixes_re, cache_file)
				next_level()
				message("decided whether to keep a cache file", cache_file, 6)
				back_level()
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
						message("removing stale cache file...", cache_file, 3)
						file_to_delete = os.path.join(Options.config['cache_path'], subdir, cache_file)
						os.unlink(file_to_delete)
						next_level()
						message("removed stale cache file", "", 5)
						back_level()
				else:
					next_level()
					message("not a stale cache file, keeping it", cache_file, 2)
					back_level()
					continue
				back_level()
		if not subdir:
			message("cleaned", "", 5)
			back_level()
			back_level()
