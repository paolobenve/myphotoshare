import os
import os.path
import sys
from datetime import datetime
from PhotoAlbum import Media, Album, PhotoAlbumEncoder
from CachePath import *
import json
import Options
import re
import time
import random
import math
from PIL import Image
#~ from pprint import pprint

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

		origin_album = Album(Options.config['album_path'])
		origin_album.cache_base = cache_base(Options.config['album_path'])
		album_cache_base = Options.config['folders_string']
		[folders_album, num, max_file_date] = self.walk(Options.config['album_path'], album_cache_base, origin_album)
		folders_album.num_media_in_sub_tree = num
		if folders_album is None:
			message("WARNING", "ALBUMS ROOT EXCLUDED BY MARKER FILE", 2)
		else:
			self.all_cache_entries.append("all_media.json")
			self.all_cache_entries.append(Options.config['folders_string'] + ".json")
			message("saving all media json file...", "", 4)
			self.save_all_media_json()
			next_level()
			message("saved all media json file", "", 5)
			back_level()
			message("generating date albums...", "", 4)
			by_date_album = self.generate_date_album(origin_album)
			next_level()
			message("generated date albums", "", 5)
			back_level()
			origin_album.add_album(folders_album)
			self.all_albums.append(origin_album)
			if by_date_album is not None and not by_date_album.empty:
				self.all_cache_entries.append(Options.config['by_date_string'] + ".json")
				origin_album.add_album(by_date_album)
			if not origin_album.empty:
				origin_album.cache()
		self.remove_stale()
		message("complete", "", 4)
	def generate_date_album(self, origin_album):
		next_level()
		# convert the temporary structure where media are organized by year, month, date to a set of albums
		by_date_path = os.path.join(Options.config['album_path'], Options.config['by_date_string'])
		by_date_album = Album(by_date_path)
		by_date_album.parent = origin_album
		by_date_album.cache_base = cache_base(by_date_path)
		#~ by_date_json_file_with_path = os.path.join(Options.config['cache_path'], by_date_album.json_file)
		by_date_max_file_date = None
		for year, months in self.tree_by_date.iteritems():
			year_path = os.path.join(by_date_path, str(year))
			year_album = Album(year_path)
			year_album.parent = by_date_album
			year_album.cache_base = cache_base(year_path)
			#~ year_json_file_with_path = os.path.join(Options.config['cache_path'], year_album.json_file)
			year_max_file_date = None
			by_date_album.add_album(year_album)
			for month, days in self.tree_by_date[year].iteritems():
				month_path = os.path.join(year_path, str(month))
				month_album = Album(month_path)
				month_album.parent = year_album
				month_album.cache_base = cache_base(month_path)
				#~ month_json_file_with_path = os.path.join(Options.config['cache_path'], month_album.json_file)
				month_max_file_date = None
				year_album.add_album(month_album)
				for day, media in self.tree_by_date[year][month].iteritems():
					day_path = os.path.join(month_path, str(day))
					day_album = Album(day_path)
					day_album.parent = month_album
					day_album.cache_base = cache_base(day_path)
					#~ day_json_file_with_path = os.path.join(Options.config['cache_path'], day_album.json_file)
					day_max_file_date = None
					month_album.add_album(day_album)
					message("elaborating day album...", "", 5)
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
					message("elaborated day album", media[0].year + "-" + media[0].month + "-" + media[0].day, 4)
					self.all_albums.append(day_album)
					json_file = os.path.join(Options.config['cache_path'], day_album.json_file)
					if not day_album.empty and (not os.path.exists(json_file) or file_mtime(json_file) < day_max_file_date):
						day_album.cache()
					self.generate_composite_image(day_album, day_max_file_date)
				self.all_albums.append(month_album)
				json_file = os.path.join(Options.config['cache_path'], month_album.json_file)
				if not month_album.empty and (not os.path.exists(json_file) or file_mtime(json_file) < month_max_file_date):
					month_album.cache()
				self.generate_composite_image(month_album, month_max_file_date)
			self.all_albums.append(year_album)
			json_file = os.path.join(Options.config['cache_path'], year_album.json_file)
			if not year_album.empty and (not os.path.exists(json_file) or file_mtime(json_file) < year_max_file_date):
				year_album.cache()
			self.generate_composite_image(year_album, year_max_file_date)
		self.all_albums.append(by_date_album)
		json_file = os.path.join(Options.config['cache_path'], by_date_album.json_file)
		if not by_date_album.empty and (not os.path.exists(json_file) or file_mtime(json_file) < by_date_max_file_date):
			by_date_album.cache()
		self.generate_composite_image(by_date_album, by_date_max_file_date)
		back_level()
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
		json_cache_file = os.path.join(Options.config['cache_path'], album_cache_base) + ".json"
		json_cache_OK = False
		cached_album = None
		json_message = json_cache_file + " (path: " + os.path.basename(absolute_path) + ")"
		try:
			if os.path.exists(json_cache_file):
				if not os.access(json_cache_file, os.R_OK):
					message("json file unreadable", json_cache_file, 1)
				elif not os.access(json_cache_file, os.W_OK):
					message("json file unwritable", json_cache_file, 1)
				else:
					message("reading json file to import album...", json_cache_file, 5)
					cached_album = Album.from_cache(json_cache_file, album_cache_base)
					next_level()
					message("read json file", "", 5)
					back_level()
					if (
						file_mtime(absolute_path) <= file_mtime(json_cache_file) and
						hasattr(cached_album, "absolute_path") and
						cached_album.absolute_path == absolute_path
					):
						next_level()
						message("json file is OK", "  " + json_message, 4)
						back_level()
						json_cache_OK = True
						album = cached_album
						message("adding media in album to big lists...", "", 5)
						for media in album.media:
							if not any(media.media_file_name == _media.media_file_name for _media in album.media):
								self.all_media.append(media)
								self.add_media_to_tree_by_date(media)
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
		#~ except (ValueError, AttributeError, KeyError) as e:
			#~ message(" json file invalid", json_message, 4)
			#~ cached_album = None
		
		if not json_cache_OK:
			message("generating album...", absolute_path, 5)
			album = Album(absolute_path)
			next_level()
			message("generated album", "", 5)
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
				max_file_date = max(max_file_date, sub_max_file_date)
				album.num_media_in_sub_tree += num
				if next_walked_album is not None:
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
					message("read cache media", "", 5)
					back_level()
					if (
						cached_media and
						mtime <= cached_media.attributes["dateTimeFile"]
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
							
							if (
								not os.path.exists(absolute_cache_file) or 
								file_mtime(absolute_cache_file) < cached_media._attributes["dateTimeFile"] or
								json_cache_OK and file_mtime(absolute_cache_file) > file_mtime(json_cache_file) or
								(Options.config['recreate_reduced_photos'] or Options.config['recreate_thumbnails'])
							):
								cache_hit = False
								break
						if cache_hit:
							message("reduced size images and thumbnails OK", os.path.basename(entry_with_path), 4)
							media = cached_media
						else:
							absolute_cache_file = ""
				if not cache_hit:
					message("processing file", entry_with_path, 4)
					next_level()
					if json_cache_OK:
						if cached_media is None:
							message("media not cached", "", 4)
						elif not os.path.exists(absolute_cache_file):
							message("unexistent reduction/thumbnail", absolute_cache_file, 4)
						elif file_mtime(absolute_cache_file) < cached_media._attributes["dateTimeFile"]:
							message("reduction/thumbnail older than media", absolute_cache_file, 4)
						elif file_mtime(absolute_cache_file) > file_mtime(json_cache_file):
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
					message("adding media to big list...", "", 5)
					if not any(media.media_file_name == _media.media_file_name for _media in self.all_media):
						self.all_media.append(media)
					next_level()
					message("added media to big list", "", 5)
					back_level()
					# following function has a check on media already present
					message("adding media to by date tree...", "", 5)
					self.add_media_to_tree_by_date(media)
					next_level()
					message("added media to by date tree", "", 5)
					back_level()
				elif not media.is_valid:
					next_level()
					message("not image nor video", entry_with_path, 1)
					back_level()
				back_level()
		if not album.empty:
			next_level()
			json_file = os.path.join(Options.config['cache_path'], album.json_file)
			if not os.path.exists(json_file) or file_mtime(json_file) < max_file_date:
				message("saving json file for album", "", 5)
				album.cache()
				next_level()
				message("saved json file for album", os.path.basename(absolute_path), 4)
				back_level()
			else:
				message("no need to save json file for album", os.path.basename(absolute_path), 4)
			message("adding album to big list...", "", 5)
			self.all_albums.append(album)
			next_level()
			message("added album to big list", "", 5)
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
		if os.path.exists(composite_image_path) and file_mtime(composite_image_path) > max_file_date:
			message("composite image OK", composite_image_path, 5)
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
		num_random_thumbnails = min(max_thumbnail_number, album.num_media_in_sub_tree)
		for i in range(num_random_thumbnails):
			if num_random_thumbnails == 1:
				random_media = album.media[0]
			else:
				while True:
					random_number = random.randint(0, album.num_media_in_sub_tree - 1)
					if random_number not in random_list:
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
			random_thumbnails.append(thumbnail)
		
		# add the missing images, repeat the first ones
		if len(random_thumbnails) < max_thumbnail_number:
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
		try:
			json_options_file = os.path.join(Options.config['index_html_path'], 'options.json')
			message("saving json options file...", json_options_file, 4)
			with open(json_options_file, 'w') as fp:
				json.dump(Options.config, fp)
		except IOError:
			json_options_file_old = json_options_file
			json_options_file = os.path.join(Options.config['cache_path'], 'options.json')
			message("saving json options file", json_options_file + " (couldn not save " + json_options_file_old + ")", 4)
			with open(json_options_file, 'w') as fp:
				json.dump(Options.config, fp)
		next_level()
		message("saved json options file", "", 5)
		back_level()
		
	def remove_stale(self, subdir = "", cache_list = {}):
		if not subdir:
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
		if subdir:
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
		else:
			info = "in cache path"
			deletable_files_suffixes_re ="\.json$"
		message("searching for stale cache files", info, 4)
		
		next_level()
		
		for cache_file in sorted(os.listdir(os.path.join(Options.config['cache_path'], subdir))):
			if os.path.isdir(os.path.join(Options.config['cache_path'], cache_file)):
				next_level()
				self.remove_stale(cache_file)
				if not os.listdir(os.path.join(Options.config['cache_path'], cache_file)):
					message("empty subdir, deleting...", "", 4)
					file_to_delete = os.path.join(Options.config['cache_path'], cache_file)
					os.rmdir(os.path.join(Options.config['cache_path'], file_to_delete))
					next_level()
					message("empty subdir, deleted", "", 5)
					back_level()
				back_level()
			else:
				# only delete json's, transcoded videos, reduced images and thumbnails
				message
				message("deciding whether to keep a cache file...", cache_file, 6)
				match = re.search(deletable_files_suffixes_re, cache_file)
				next_level()
				message("decided whether to keep a cache file", "", 6)
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
					message("not a stale cache file, keeping it", cache_file, 2)
					continue
				
		if not subdir:
			back_level()
		back_level()
