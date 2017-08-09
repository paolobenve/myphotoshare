import locale
locale.setlocale(locale.LC_ALL, '')
from CachePath import *
from datetime import datetime
import json
import os
import os.path
from PIL import Image
from PIL.ExifTags import TAGS
from multiprocessing import Pool
import gc
import tempfile
from VideoToolWrapper import *
import math
import Options
import hashlib
#~ from pprint import pprint

def make_photo_thumbs(self, image, original_path, thumbs_path, thumb_size, thumb_type = ""):
	# The pool methods use a queue.Queue to pass tasks to the worker processes.
	# Everything that goes through the queue.Queue must be pickable, and since
	# self.reduce_image_size_or_make_thumbnail is not defined at the top level, it's not pickable.
	# This is why we have this "dummy" function, so that it's pickable.
	try:
		self.reduce_image_size_or_make_thumbnail(image, original_path, thumbs_path, thumb_size, thumb_type)
	except KeyboardInterrupt:
		raise

class Album(object):
	#~ def __init__(self, path, path_has_folder_marker):
	def __init__(self, path):
		#~ if path_has_folder_marker:
			#~ path = remove_album_path(path)
			#~ path = trim_base_custom(path, Options.config['album_path'])
			#~ path = os.join(Options.config['album_path'], path)
		if path[-1:] == '/':
			path = path[0:-1]
		self.absolute_path = path
		self.baseless_path = remove_album_path(path)
		self.media_list = list()
		self.albums_list = list()
		self.media_list_is_sorted = True
		self.albums_list_is_sorted = True
		self._subdir = ""
		self.num_media_in_sub_tree = 0
		self.num_media_in_album = 0
		self.parent = None
		
		if (
			Options.config['subdir_method'] in ("md5", "folder") and
			(
				self.baseless_path.find(Options.config['by_date_string']) != 0
				#~ and self.baseless_path != ""
			)
		):
			if Options.config['subdir_method'] == "md5":
				self._subdir = hashlib.md5(path).hexdigest()[:2]
			elif Options.config['subdir_method'] == "folder":
				if path.find("/") == -1:
					self._subdir = "__"
				else:
					self._subdir = path[path.rfind("/") + 1:][:2].replace(" ", "_")
					if len(self._subdir) == 1:
						self._subdir += "_"
			self.cache_path_with_subdir = os.path.join(Options.config['cache_path'], self._subdir)
			if not os.path.exists(self.cache_path_with_subdir):
				os.makedirs(self.cache_path_with_subdir)
	
	@property
	def media(self):
		return self.media_list
	@property
	def albums(self):
		return self.albums_list
	@property
	def path(self):
		return self.baseless_path
	def __str__(self):
		return self.path
	@property
	def json_file(self):
		#~ return json_name(self.path)
		return self.cache_base + ".json"
	@property
	def subdir(self):
		return self._subdir
	@property
	def date(self):
		self.sort_subalbums_and_media()
		if len(self.media_list) == 0 and len(self.albums_list) == 0:
			return datetime(1900, 1, 1)
		elif len(self.media_list) == 0:
			return self.albums_list[-1].date
		elif len(self.albums_list) == 0:
			return self.media_list[-1].date
		return max(self.media_list[-1].date, self.albums_list[-1].date)
	def __cmp__(self, other):
		try:
			return cmp(self.date, other.date)
		except TypeError:
			return 1
	def add_media(self, media):
		if not any(media.media_file_name == _media.media_file_name for _media in self.media_list):
		#~ if not media in self.media_list:
			self.media_list.append(media)
			self.media_list_is_sorted = False
	def add_album(self, album):
		self.albums_list.append(album)
		self.albums_list_is_sorted = False
	def sort_subalbums_and_media(self):
		if not self.media_list_is_sorted:
			self.media_list.sort()
			self.media_list_is_sorted = True
		if not self.albums_list_is_sorted:
			self.albums_list.sort()
			self.albums_list_is_sorted = True
	@property
	def empty(self):
		if len(self.media_list) != 0:
			return False
		if len(self.albums_list) == 0:
			return True
		for album in self.albums_list:
			if not album.empty:
				return False
		return True
		
	def cache(self, base_dir):
		self.sort_subalbums_and_media()
		fp = open(os.path.join(base_dir, self.json_file), 'w')
		json.dump(self, fp, cls=PhotoAlbumEncoder)
		fp.close()
	@staticmethod
	def from_cache(path):
		fp = open(path, "r")
		dictionary = json.load(fp)
		fp.close()
		# generate the album from the json file loaded
		# subalbums are not generated yet
		return Album.from_dict(dictionary)
	@staticmethod
	def from_dict(dictionary, cripple=True):
		if "physicalPath" in dictionary:
			path = dictionary["physicalPath"]
		else:
			path = dictionary["path"]
		album = Album(os.path.join(Options.config['album_path'], path))
		for media in dictionary["media"]:
			new_media = Media.from_dict(album, media, os.path.join(Options.config['album_path'], remove_folders_marker(album.baseless_path)))
			album.add_media(new_media)
		if not cripple:
			# it looks like the following code is never executed
			for subalbum in dictionary["albums"]:
				album.add_album(Album.from_dict(subalbum, cripple))
		album.sort_subalbums_and_media()
		
		return album
	def to_dict(self, cripple=True):
		self.sort_subalbums_and_media()
		subalbums = []
		if cripple:
			for sub in self.albums_list:
				if not sub.empty:
					path_to_dict = trim_base_custom(sub.path, self.baseless_path)
					if path_to_dict == "":
						path_to_dict = Options.config['folders_string']
					
					subalbums.append({
						"path": path_to_dict,
						"cacheBase": sub.cache_base,
						"date": sub.date,
						"numMediaInSubTree": sub.num_media_in_sub_tree
					})
		else:
			# it looks like the following code is never executed
			for sub in self.albums_list:
				if not sub.empty:
					subalbums.append(sub)
		
		path_without_folders_marker = remove_folders_marker(self.path)
		
		path_to_dict = self.path
		folder_position = path_to_dict.find(Options.config['folders_string'])
		by_date_position = path_to_dict.find(Options.config['by_date_string'])
		if by_date_position == -1 and self.cache_base != "root" and (folder_position == -1 or folder_position > 0):
			path_to_dict = Options.config['folders_string'] + '/' + path_to_dict
		
		
		ancestors_cache_base = list()
		_parent = self
		while True:
			ancestors_cache_base.append(_parent.cache_base)
			if _parent.parent is None:
				break
			_parent = _parent.parent
		ancestors_cache_base.reverse()
		
		dictionary = {
			"path": path_to_dict,
			"absolutePath": self.absolute_path,
			"cacheSubdir": self._subdir,
			"date": self.date,
			"albums": subalbums,
			"media": self.media_list,
			"cacheBase": self.cache_base,
			"ancestorsCacheBase": ancestors_cache_base,
			"physicalPath": path_without_folders_marker,
			"numMediaInSubTree": self.num_media_in_sub_tree,
			"numMediaInAlbum": self.num_media_in_album
		}
		if self.parent is not None:
			dictionary["parentCacheBase"] = self.parent.cache_base
		return dictionary
	def media_from_path(self, path):
		for media in self.media_list:
			if remove_album_path(path) == media.media_file_name:
				return media
		return None

class Media(object):
	def __init__(self, album, media_path, thumbs_path=None, attributes=None):
		self.album = album
		self.media_file_name = remove_album_path(media_path)
		self.folders = remove_album_path(os.path.dirname(self.media_file_name))
		self.album_path = os.path.join(Options.config['server_album_path'], self.media_file_name)
		self.is_valid = True
		
		image = None
		try:
			mtime = file_mtime(media_path)
		except KeyboardInterrupt:
			raise
		except:
			self.is_valid = False
			return
		if attributes is not None and attributes["dateTimeFile"] >= mtime:
		#~ if attributes is not None and attributes["date"] >= mtime:
			self._attributes = attributes
			self.cache_base = attributes["cacheBase"]
			return
		self._attributes = {}
		self._attributes["metadata"] = {}
		self._attributes["dateTimeFile"] = mtime
		self._attributes["mediaType"] = "photo"
		self.cache_base = cache_base(trim_base_custom(media_path, album.absolute_path))
		
		# let's avoid that different media names have the same cache base
		distinguish_suffix = 0
		while True:
			_cache_base = self.cache_base
			if distinguish_suffix:
				_cache_base += "_" + str(distinguish_suffix)
			cache_name_absent = True
			for _media in album.media_list:
				if _cache_base == _media.cache_base and self.media_file_name != _media.media_file_name:
					cache_name_absent = False
					distinguish_suffix += 1
					break
			if cache_name_absent:
				self.cache_base = _cache_base
				break
		try:
			image = Image.open(media_path)
		except KeyboardInterrupt:
			raise
		except IOError:
			# file is not an image
			self._video_metadata(media_path)
		
		if isinstance(image, Image.Image):
			self._photo_metadata(image)
			self._photo_thumbnails(image, media_path, Options.config['cache_path'])
		elif self._attributes["mediaType"] == "video":
			self._video_transcode(thumbs_path, media_path)
			self._video_thumbnails(thumbs_path, media_path)
		else:
			self.is_valid = False
			return
		
	def _photo_metadata(self, image):
		self._attributes["metadata"]["size"] = image.size
		self._orientation = 1
		try:
			info = image._getexif()
		except KeyboardInterrupt:
			raise
		except:
			return
		
		if not info:
			return
		
		exif = {}
		for tag, value in info.items():
			decoded = TAGS.get(tag, tag)
			if (isinstance(value, tuple) or isinstance(value, list)) and (isinstance(decoded, str) or isinstance(decoded, unicode)) and decoded.startswith("DateTime") and len(value) >= 1:
				value = value[0]
			if isinstance(value, str) or isinstance(value, unicode):
				value = value.strip().partition("\x00")[0]
				#~ # the following lines (commented out) seem unuseful
				#~ if (isinstance(decoded, str) or isinstance(decoded, unicode)) and decoded.startswith("DateTime"):
					#~ try:
						#~ value = datetime.strptime(value, Options.exif_date_time_format)
					#~ except KeyboardInterrupt:
						#~ raise
					#~ except ValueError:
						#~ pass
			exif[decoded] = value
		
		if "Orientation" in exif:
			self._orientation = exif["Orientation"];
			if self._orientation in range(5, 9):
				self._attributes["metadata"]["size"] = (self._attributes["metadata"]["size"][1], self._attributes["metadata"]["size"][0])
			if self._orientation - 1 < len(self._photo_metadata.orientation_list):
				self._attributes["metadata"]["orientation"] = self._photo_metadata.orientation_list[self._orientation - 1]
		if "Make" in exif:
			self._attributes["metadata"]["make"] = exif["Make"]
		if "Model" in exif:
			self._attributes["metadata"]["model"] = exif["Model"]
		if "ApertureValue" in exif:
			self._attributes["metadata"]["aperture"] = exif["ApertureValue"]
		elif "FNumber" in exif:
			self._attributes["metadata"]["aperture"] = exif["FNumber"]
		if "FocalLength" in exif:
			self._attributes["metadata"]["focalLength"] = exif["FocalLength"]
		if "ISOSpeedRatings" in exif:
			self._attributes["metadata"]["iso"] = exif["ISOSpeedRatings"]
		if "ISO" in exif:
			self._attributes["metadata"]["iso"] = exif["ISO"]
		if "PhotographicSensitivity" in exif:
			self._attributes["metadata"]["iso"] = exif["PhotographicSensitivity"]
		if "ExposureTime" in exif:
			self._attributes["metadata"]["exposureTime"] = exif["ExposureTime"]
		if "Flash" in exif and exif["Flash"] in self._photo_metadata.flash_dictionary:
			try:
				self._attributes["metadata"]["flash"] = self._photo_metadata.flash_dictionary[exif["Flash"]]
			except KeyboardInterrupt:
				raise
			#~ except:
				#~ pass
		if "LightSource" in exif and exif["LightSource"] in self._photo_metadata.light_source_dictionary:
			try:
				self._attributes["metadata"]["lightSource"] = self._photo_metadata.light_source_dictionary[exif["LightSource"]]
			except KeyboardInterrupt:
				raise
			#~ except:
				#~ pass
		if "ExposureProgram" in exif and exif["ExposureProgram"] < len(self._photo_metadata.exposure_list):
			self._attributes["metadata"]["exposureProgram"] = self._photo_metadata.exposure_list[exif["ExposureProgram"]]
		if "SpectralSensitivity" in exif:
			self._attributes["metadata"]["spectralSensitivity"] = exif["SpectralSensitivity"]
		if "MeteringMode" in exif and exif["MeteringMode"] < len(self._photo_metadata.metering_list):
			self._attributes["metadata"]["meteringMode"] = self._photo_metadata.metering_list[exif["MeteringMode"]]
		if "SensingMethod" in exif and exif["SensingMethod"] < len(self._photo_metadata.sensing_method_list):
			self._attributes["metadata"]["sensingMethod"] = self._photo_metadata.sensing_method_list[exif["SensingMethod"]]
		if "SceneCaptureType" in exif and exif["SceneCaptureType"] < len(self._photo_metadata.scene_capture_type_list):
			self._attributes["metadata"]["sceneCaptureType"] = self._photo_metadata.scene_capture_type_list[exif["SceneCaptureType"]]
		if "SubjectDistanceRange" in exif and exif["SubjectDistanceRange"] < len(self._photo_metadata.subject_distance_range_list):
			self._attributes["metadata"]["subjectDistanceRange"] = self._photo_metadata.subject_distance_range_list[exif["SubjectDistanceRange"]]
		if "ExposureCompensation" in exif:
			self._attributes["metadata"]["exposureCompensation"] = exif["ExposureCompensation"]
		if "ExposureBiasValue" in exif:
			self._attributes["metadata"]["exposureCompensation"] = exif["ExposureBiasValue"]
		if "DateTimeOriginal" in exif:
			try:
				self._attributes["metadata"]["dateTimeOriginal"] = datetime.strptime(exif["DateTimeOriginal"], Options.exif_date_time_format)
			except KeyboardInterrupt:
				raise
			except ValueError:
				# value isn't usable, forget it
				pass
		if "DateTime" in exif:
			try:
				self._attributes["metadata"]["dateTime"] = datetime.strptime(exif["DateTime"], Options.exif_date_time_format)
			except KeyboardInterrupt:
				raise
			except ValueError:
				# value isn't usable, forget it
				pass

	_photo_metadata.flash_dictionary = {0x0: "No Flash", 0x1: "Fired",0x5: "Fired, Return not detected",0x7: "Fired, Return detected",0x8: "On, Did not fire",0x9: "On, Fired",0xd: "On, Return not detected",0xf: "On, Return detected",0x10: "Off, Did not fire",0x14: "Off, Did not fire, Return not detected",0x18: "Auto, Did not fire",0x19: "Auto, Fired",0x1d: "Auto, Fired, Return not detected",0x1f: "Auto, Fired, Return detected",0x20: "No flash function",0x30: "Off, No flash function",0x41: "Fired, Red-eye reduction",0x45: "Fired, Red-eye reduction, Return not detected",0x47: "Fired, Red-eye reduction, Return detected",0x49: "On, Red-eye reduction",0x4d: "On, Red-eye reduction, Return not detected",0x4f: "On, Red-eye reduction, Return detected",0x50: "Off, Red-eye reduction",0x58: "Auto, Did not fire, Red-eye reduction",0x59: "Auto, Fired, Red-eye reduction",0x5d: "Auto, Fired, Red-eye reduction, Return not detected",0x5f: "Auto, Fired, Red-eye reduction, Return detected"}
	_photo_metadata.light_source_dictionary = {0: "Unknown", 1: "Daylight", 2: "Fluorescent", 3: "Tungsten (incandescent light)", 4: "Flash", 9: "Fine weather", 10: "Cloudy weather", 11: "Shade", 12: "Daylight fluorescent (D 5700 - 7100K)", 13: "Day white fluorescent (N 4600 - 5400K)", 14: "Cool white fluorescent (W 3900 - 4500K)", 15: "White fluorescent (WW 3200 - 3700K)", 17: "Standard light A", 18: "Standard light B", 19: "Standard light C", 20: "D55", 21: "D65", 22: "D75", 23: "D50", 24: "ISO studio tungsten"}
	_photo_metadata.metering_list = ["Unknown", "Average", "Center-weighted average", "Spot", "Multi-spot", "Multi-segment", "Partial"]
	_photo_metadata.exposure_list = ["Not Defined", "Manual", "Program AE", "Aperture-priority AE", "Shutter speed priority AE", "Creative (Slow speed)", "Action (High speed)", "Portrait", "Landscape", "Bulb"]
	_photo_metadata.orientation_list = ["Horizontal (normal)", "Mirror horizontal", "Rotate 180", "Mirror vertical", "Mirror horizontal and rotate 270 CW", "Rotate 90 CW", "Mirror horizontal and rotate 90 CW", "Rotate 270 CW"]
	_photo_metadata.sensing_method_list = ["Not defined", "One-chip color area sensor", "Two-chip color area sensor", "Three-chip color area sensor", "Color sequential area sensor", "Trilinear sensor", "Color sequential linear sensor"]
	_photo_metadata.scene_capture_type_list = ["Standard", "Landscape", "Portrait", "Night scene"]
	_photo_metadata.subject_distance_range_list = ["Unknown", "Macro", "Close view", "Distant view"]


	def _video_metadata(self, path, original=True):
		p = VideoProbeWrapper().call('-show_format', '-show_streams', '-of', 'json', '-loglevel', '0', path)
		if p == False:
			self.is_valid = False
			return
		info = json.loads(p)
		for s in info["streams"]:
			next_level()
			message("debug: codec_type", 'codec_type', 5)
			if 'codec_type' in s:
				message("debug: s[codec_type]", s['codec_type'], 5)
			back_level()
			if 'codec_type' in s and s['codec_type'] == 'video':
				self._attributes["mediaType"] = "video"
				self._attributes["metadata"]["size"] = (int(s["width"]), int(s["height"]))
				if "duration" in s:
					self._attributes["metadata"]["duration"] = float(int(float(s["duration"]) * 10)) / 10
				if "tags" in s and "rotate" in s["tags"]:
					self._attributes["metadata"]["rotate"] = s["tags"]["rotate"]
				if original:
					self._attributes["metadata"]["originalSize"] = (int(s["width"]), int(s["height"]))
				break
	def _photo_thumbnails(self, image, photo_path, thumbs_path):
		# give image the correct orientation
		try:
			mirror = image
			if self._orientation == 2:
				# Vertical Mirror
				mirror = image.transpose(Image.FLIP_LEFT_RIGHT)
			elif self._orientation == 3:
				# Rotation 180
				mirror = image.transpose(Image.ROTATE_180)
			elif self._orientation == 4:
				# Horizontal Mirror
				mirror = image.transpose(Image.FLIP_TOP_BOTTOM)
			elif self._orientation == 5:
				# Horizontal Mirror + Rotation 270
				mirror = image.transpose(Image.FLIP_TOP_BOTTOM).transpose(Image.ROTATE_270)
			elif self._orientation == 6:
				# Rotation 270
				mirror = image.transpose(Image.ROTATE_270)
			elif self._orientation == 7:
				# Vertical Mirror + Rotation 270
				mirror = image.transpose(Image.FLIP_LEFT_RIGHT).transpose(Image.ROTATE_270)
			elif self._orientation == 8:
				# Rotation 90
				mirror = image.transpose(Image.ROTATE_90)
			image = mirror
		except IOError:
			# https://github.com/paolobenve/myphotoshare/issues/46 : some image make raise this exception
			pass
		
		if (Options.config['thumbnail_generation_mode'] == "parallel"):
			self._photo_thumbnails_parallel(image, photo_path, thumbs_path)
		elif (Options.config['thumbnail_generation_mode'] == "mixed"):
			self._photo_thumbnails_mixed(image, photo_path, thumbs_path)
		elif (Options.config['thumbnail_generation_mode'] == "cascade"):
			self._photo_thumbnails_cascade(image, photo_path, thumbs_path)
	def thumbnail_size_is_smaller_then_size_of_(self, image, thumb_size, thumb_type = ""):
		image_width = image.size[0]
		image_height = image.size[1]
		max_image_size = max(image_width, image_height)
		if (
			thumb_size == Options.config['media_thumb_size'] and
			Options.config['media_thumb_type'] == "fixed_height" and
			image_width > image_height
		):
			veredict = (thumb_size * image_width / image_height < image_width)
		elif Options.config['media_thumb_type'] == "square":
			min_image_size = min(image_width, image_height)
			veredict = (thumb_size < min_image_size)
		else:
			veredict = (thumb_size < max_image_size)
		return veredict
			
	def _photo_thumbnails_parallel(self, start_image, photo_path, thumbs_path):
		# get number of cores on the system, and use all minus one
		num_of_cores = os.sysconf('SC_NPROCESSORS_ONLN') - Options.config['respected_processors']
		pool = Pool(processes=num_of_cores)
		try:
			# reduced sizes media
			for thumb_size in Options.config['reduced_sizes']:
				if (
					Options.config['thumbnail_generation_mode'] == "mixed" and
					thumb_size == Options.config['reduced_sizes'][0]
				):
					continue
				pool.apply_async(
					make_photo_thumbs,
					args = (self, start_image, photo_path, thumbs_path, thumb_size)
				)
			# album thumbnails
			(thumb_size, thumb_type) = (Options.config['album_thumb_size'], Options.config['album_thumb_type'])
			pool.apply_async(
				make_photo_thumbs,
				args = (self, start_image, photo_path, thumbs_path, thumb_size, thumb_type)
			)
			if thumb_type == "fit":
				# square album thumbnail is needed too
				thumb_type = "square"
				pool.apply_async(
					make_photo_thumbs,
					args = (self, start_image, photo_path, thumbs_path, thumb_size, thumb_type)
				)
			# media thumbnails
			(thumb_size, thumb_type) = (Options.config['media_thumb_size'], Options.config['media_thumb_type'])
			pool.apply_async(
				make_photo_thumbs,
				args = (self, start_image, photo_path, thumbs_path, thumb_size, thumb_type)
			)
		except KeyboardInterrupt:
			raise
		except:
			pool.terminate()
		pool.close()
		pool.join()
	
	def _photo_thumbnails_mixed(self, image, photo_path, thumbs_path):
		thumb_size = Options.config['reduced_sizes'][0]
		thumb = self.reduce_image_size_or_make_thumbnail(image, photo_path, thumbs_path, thumb_size)
		self._photo_thumbnails_parallel(thumb, photo_path, thumbs_path)
	def _photo_thumbnails_cascade(self, image, photo_path, thumbs_path):
		# this function calls self.reduce_image_size_or_make_thumbnail() with the proper image self.reduce_image_size_or_make_thumbnail() needs
		# so that the thumbnail doesn't get blurred
		thumb = image
		image_width = image.size[0]
		image_height = image.size[1]
		for thumb_size in Options.config['reduced_sizes']:
			thumb = self.reduce_image_size_or_make_thumbnail(thumb, photo_path, thumbs_path, thumb_size)
		smallest_reduced_size_image = thumb
		
		# album size: square thumbnail are generated anyway, because they are needed by the php code that permits sharing albums
		(thumb_size, thumb_type) = (Options.config['album_thumb_size'], Options.config['album_thumb_type'])
		for i in range(2):
			if thumb_type == "fit" or self.thumbnail_size_is_smaller_then_size_of_(smallest_reduced_size_image, thumb_size, thumb_type):
				thumb = self.reduce_image_size_or_make_thumbnail(smallest_reduced_size_image, photo_path, thumbs_path, thumb_size, thumb_type)
			else:
				thumb = self.reduce_image_size_or_make_thumbnail(image, photo_path, thumbs_path, thumb_size, thumb_type)
			if i == 0:
				if thumb_type == "square":
					# no need for a second iteration
					break
				elif thumb_type == "fit":
					thumb_type = "square"
		# media size
		# at this point thumb is always square
		(thumb_size, thumb_type) = (Options.config['media_thumb_size'], Options.config['media_thumb_type'])
		if self.thumbnail_size_is_smaller_then_size_of_(smallest_reduced_size_image, thumb_size, thumb_type):
			thumb = self.reduce_image_size_or_make_thumbnail(smallest_reduced_size_image, photo_path, thumbs_path, thumb_size, thumb_type)
		else:
			thumb = self.reduce_image_size_or_make_thumbnail(image, photo_path, thumbs_path, thumb_size, thumb_type)
	
	def reduce_image_size_or_make_thumbnail(self, start_image, original_path, thumbs_path, thumb_size, thumb_type = ""):
		thumb_path = os.path.join(thumbs_path, self.album.subdir, remove_folders_marker(self.album.cache_base) + Options.config["cache_folder_separator"] + photo_cache_name(self, thumb_size, thumb_type))
		# if the reduced image/thumbnail is there and is valid, exit immediately
		json_file = os.path.join(thumbs_path, self.album.json_file)
		is_thumbnail = (thumb_size == Options.config['album_thumb_size'] or thumb_size == Options.config['media_thumb_size'])
		is_video = self._attributes["mediaType"] == "video"
		next_level()
		if (
			os.path.exists(thumb_path) and
			file_mtime(thumb_path) >= self._attributes["dateTimeFile"] and
			(not os.path.exists(json_file) or file_mtime(thumb_path) < file_mtime(json_file)) and (
				not is_thumbnail and not Options.config['recreate_reduced_photos'] or
				is_thumbnail and not Options.config['recreate_thumbnails']
			)
		):
			message("reduction/thumbnail OK, skipping", thumb_path, 5)
			back_level()
			return start_image
		
		message("reduction/thumbnail not OK, creating", thumb_path, 5)
		info_string = str(thumb_size)
		original_thumb_size = thumb_size
		if thumb_type == "square": 
			info_string += ", square"
		if thumb_size == Options.config['album_thumb_size'] and thumb_type == "fit":
			info_string += ", fit size"
		elif thumb_size == Options.config['media_thumb_size'] and thumb_type == "fixed_height":
			info_string += ", fixed height"
		
		start_image_width = start_image.size[0]
		start_image_height = start_image.size[1]
		if thumb_type == "square":
			# image is to be cropped: calculate the cropping values
			if min(start_image_width, start_image_height) >= thumb_size:
				# image is bigger than the square which will result from cropping
				if start_image_width > start_image_height:
					left = (start_image_width - start_image_height) / 2
					top = 0
					right = start_image_width - left
					bottom = start_image_height
				else:
					left = 0
					top = (start_image_height - start_image_width) / 2
					right = start_image_width
					bottom = start_image_height - top
				thumbnail_width = thumb_size
				thumbnail_height = thumb_size
				must_crop = True
			elif max(start_image_width, start_image_height) >= thumb_size:
				# image smallest size is smaller than the square which would result from cropping
				# cropped image will not be square
				if start_image_width > start_image_height:
					left = (start_image_width - thumb_size) / 2
					top = 0
					right = start_image_width - left
					bottom = start_image_height
					thumbnail_width = thumb_size
					thumbnail_height = start_image_height
				else:
					left = 0
					top = (start_image_height - thumb_size) / 2
					right = start_image_width
					bottom = start_image_height - top
					thumbnail_width = start_image_width
					thumbnail_height = thumb_size
				must_crop = True
			else:
				# image is smaller than the square thumbnail, don't crop it
				thumbnail_width = start_image_width
				thumbnail_height = start_image_height
				must_crop = False
		else:
			must_crop = False
			if (
				original_thumb_size == Options.config['media_thumb_size'] and thumb_type == "fixed_height" and
				start_image_width > start_image_height
			):
				# the thumbnail size will not be thumb_size, the image will be greater
				thumbnail_height = original_thumb_size
				thumbnail_width = int(round(original_thumb_size * start_image_width / float(start_image_height)))
				thumb_size = thumbnail_width
			elif start_image_width > start_image_height:
				thumbnail_width = thumb_size
				thumbnail_height = int(round(thumb_size * start_image_height / float(start_image_width)))
			else:
				thumbnail_width = int(round(thumb_size * start_image_width / float(start_image_height)))
				thumbnail_height = thumb_size
		
		# now thumbnail_width and thumbnail_height are the values the thumbnail will get,
		# and if the thumbnail isn't a square one, their ratio is the same of the original image
		next_level()
		
		#~ if (
			#~ os.path.exists(thumb_path) and
			#~ file_mtime(thumb_path) >= self._attributes["dateTimeFile"] and (
				#~ not is_thumbnail and not Options.config['recreate_reduced_photos'] or
				#~ is_thumbnail and not Options.config['recreate_thumbnails']
			#~ )
		#~ ):
			#~ if original_thumb_size == Options.config['album_thumb_size']:
				#~ message("existing album thumbnail", thumb_path, 4)
			#~ elif original_thumb_size == Options.config['media_thumb_size']:
				#~ message("existing thumbnail", thumb_path, 4)
			#~ else:
				#~ message("existing reduced size", thumb_path, 4)
			#~ back_level()
			#~ back_level()
			#~ return start_image
		
		must_resize = True
		if max(start_image_width, start_image_height) <= thumb_size:
			# resizing to thumbnail size an image smaller than the thumbnail to produce would return a blurred image
			# simply copy the start image to the thumbnail
			must_resize = False
			if original_thumb_size > Options.config['album_thumb_size']:
				message("image smaller, no reduction", info_string, 4)
			elif original_thumb_size == Options.config['album_thumb_size']:
				message("image smaller, no thumbing for album", info_string, 4)
			else:
				message("image smaller, no thumbing for media", info_string, 4)
			#~ try:
				#~ os.unlink(thumb_path)
			#~ except OSError:
				#~ pass
			#~ return start_image
		
		try:
			start_image_copy = start_image.copy()
		except KeyboardInterrupt:
			raise
		except:
			start_image_copy = start_image.copy() # we try again to work around PIL bug
			
		# both width and height of thumbnail are less then width and height of start_image, no blurring will happen
		# we can resize, but first crop to square if needed
		if must_crop:
			message("cropping", info_string, 4)
			start_image_copy = start_image_copy.crop((left, top, right, bottom))
		
		if must_resize:
			# resizing
			if original_thumb_size > Options.config['album_thumb_size']:
				message("reducing size", info_string, 4)
			elif original_thumb_size == Options.config['album_thumb_size']:
				message("thumbing for albums", info_string, 4)
			else:
				message("thumbing for media", info_string, 4)
			start_image_copy.thumbnail((thumb_size, thumb_size), Image.ANTIALIAS)
		
		gc.collect()
		
		try:
			start_image_copy.save(thumb_path, "JPEG", quality=Options.config['jpeg_quality'])
			message("saved anyway", info_string, 5)
			back_level()
			back_level()
			gc.collect()
			return start_image_copy
		except KeyboardInterrupt:
			try:
				os.unlink(thumb_path)
			except OSError:
				pass
			raise
		except IOError:
			try:
				start_image_copy.convert('RGB').save(thumb_path, "JPEG", quality=Options.config['jpeg_quality'])
				message("saved (2nd try)!", os.path.basename(thumb_path) + ", " + info_string, 2)
			except KeyboardInterrupt:
				try:
					os.unlink(thumb_path)
				except OSError:
					pass
				raise
			gc.collect()
			back_level()
			back_level()
			return start_image_copy
		except:
			message(str(thumb_size) + " thumbnail", "save failure to " + os.path.basename(thumb_path), 1)
			try:
				os.unlink(thumb_path)
			except OSError:
				pass
			back_level()
			back_level()
			gc.collect()
			return start_image
	
	def _video_thumbnails(self, thumbs_path, original_path):
		(tfd, tfn) = tempfile.mkstemp();
		p = VideoTranscodeWrapper().call(
			'-i', original_path,    # original file to extract thumbs from
			'-f', 'image2',         # extract image
			'-vsync', '1',          # CRF
			'-vframes', '1',        # extrat 1 single frame
			'-an',                  # disable audio
			'-loglevel', 'quiet',   # don't display anything
			'-y',                   # don't prompt for overwrite
			tfn                     # temporary file to store extracted image
		)
		if p == False:
			next_level()
			message("couldn't extract video frame", os.path.basename(original_path), 1)
			back_level()
			try:
				os.unlink(tfn)
			except OSError:
				pass
			self.is_valid = False
			return
		try:
			image = Image.open(tfn)
		except KeyboardInterrupt:
			try:
				os.unlink(tfn)
			except OSError:
				pass
			raise
		except:
			next_level()
			message("couldn't open video thumbnail", tfn, 1)
			back_level()
			try:
				os.unlink(tfn)
			except OSError:
				pass
			self.is_valid = False
			return
		mirror = image
		if "rotate" in self._attributes:
			if self._attributes["metadata"]["rotate"] == "90":
				mirror = image.transpose(Image.ROTATE_270)
			elif self._attributes["metadata"]["rotate"] == "180":
				mirror = image.transpose(Image.ROTATE_180)
			elif self._attributes["metadata"]["rotate"] == "270":
				mirror = image.transpose(Image.ROTATE_90)
		(thumb_size, thumb_type) = (Options.config['album_thumb_size'], Options.config['album_thumb_type'])
		self.reduce_image_size_or_make_thumbnail(mirror, original_path, thumbs_path, thumb_size, thumb_type)
		if thumb_type == "fit":
			# square thumbnail is needed too
			thumb_type = "square"
			self.reduce_image_size_or_make_thumbnail(mirror, original_path, thumbs_path, thumb_size, thumb_type)
		(thumb_size, thumb_type) = (Options.config['media_thumb_size'], Options.config['media_thumb_type'])
		self.reduce_image_size_or_make_thumbnail(mirror, original_path, thumbs_path, thumb_size, thumb_type)
		
		try:
			os.unlink(tfn)
		except OSError:
			pass

	def _video_transcode(self, transcode_path, original_path):
		transcode_path = os.path.join(transcode_path, self.album.subdir, remove_folders_marker(self.album.cache_base) + Options.config["cache_folder_separator"] + video_cache_name(self))
		# get number of cores on the system, and use all minus one
		num_of_cores = os.sysconf('SC_NPROCESSORS_ONLN') - 1
		transcode_cmd = [
			'-i', original_path,					# original file to be encoded
			'-c:v', 'libx264',					# set h264 as videocodec
			'-preset', 'slow',					# set specific preset that provides a certain encoding speed to compression ratio
			'-profile:v', 'baseline',				# set output to specific h264 profile
			'-level', '3.0',					# sets highest compatibility with target devices
			'-crf', str(Options.config['video_crf']),		# set quality
			'-b:v', Options.config['video_transcode_bitrate'],	# set videobitrate
			'-strict', 'experimental',				# allow native aac codec below
			'-c:a', 'aac',						# set aac as audiocodec
			'-ac', '2',						# force two audiochannels
			'-ab', '160k',						# set audiobitrate to 160Kbps
			'-maxrate', '10000000',					# limits max rate, will degrade CRF if needed
			'-bufsize', '10000000',					# define how much the client should buffer
			'-f', 'mp4',						# fileformat mp4
			'-threads', str(num_of_cores),				# number of cores (all minus one)
			'-loglevel', 'quiet',					# don't display anything
			'-y' 							# don't prompt for overwrite
		]
		filters = []
		info_string = "mp4, h264, " + Options.config['video_transcode_bitrate'] + " bit/sec, crf=" + str(Options.config['video_crf'])
		if (
			os.path.exists(transcode_path) and
			file_mtime(transcode_path) >= self._attributes["dateTimeFile"]
		):
			next_level()
			message("existent transcoded video", info_string, 4)
			back_level()
			self._video_metadata(transcode_path, False)
			return
		next_level()
		message("transcoding", info_string, 4)
		back_level()
		if "originalSize" in self._attributes["metadata"] and self._attributes["metadata"]["originalSize"][1] > 720:
			transcode_cmd.append('-s')
			transcode_cmd.append('hd720')
		if "rotate" in self._attributes["metadata"]:
			if self._attributes["metadata"]["rotate"] == "90":
				filters.append('transpose=1')
			elif self._attributes["metadata"]["rotate"] == "180":
				filters.append('vflip,hflip')
			elif self._attributes["metadata"]["rotate"] == "270":
				filters.append('transpose=2')
		if len(filters):
			transcode_cmd.append('-vf')
			transcode_cmd.append(','.join(filters))
		
		tmp_transcode_cmd = transcode_cmd[:]
		transcode_cmd.append(transcode_path)
		p = VideoTranscodeWrapper().call(*transcode_cmd)
		if p == False:
			# add another option, try transcoding again
			# done to avoid this error;
			# x264 [error]: baseline profile doesn't support 4:2:2
			next_level()
			message("transcoding failure, trying yuv420p", os.path.basename(original_path), 2)
			back_level()
			tmp_transcode_cmd.append('-pix_fmt')
			tmp_transcode_cmd.append('yuv420p')
			tmp_transcode_cmd.append(transcode_path)
			p = VideoTranscodeWrapper().call(*tmp_transcode_cmd)
		
		if p == False:
			next_level()
			message("transcoding failure", os.path.basename(original_path), 1)
			back_level()
			try:
				os.unlink(transcode_path)
			except OSError:
				self.is_valid = False
			return
		self._video_metadata(transcode_path, False)

	@property
	def name(self):
		return os.path.basename(self.media_file_name)
	def __str__(self):
		return self.name
	@property
	def path(self):
		return self.media_file_name
	@property
	def image_caches(self):
		caches = []
		album_prefix = remove_folders_marker(self.album.cache_base) + Options.config["cache_folder_separator"]
		if "mediaType" in self._attributes and self._attributes["mediaType"] == "video":
			# transcoded video path
			caches.append(os.path.join(self.album.subdir, album_prefix + video_cache_name(self)))
		else:
			# reduced sizes paths
			for thumb_size in Options.config['reduced_sizes']:
				caches.append(
					os.path.join(
						self.album.subdir,
						album_prefix + photo_cache_name(
							self,
							thumb_size
						)
					)
				)
		# album thumbnail path
		caches.append(
			os.path.join(
				self.album.subdir,
				album_prefix + photo_cache_name(
					self,
					Options.config['album_thumb_size'],
					Options.config['album_thumb_type']
				)
			)
		)
		if Options.config['album_thumb_type'] == "fit":
			# album square thumbnail path (it's generated always)
			caches.append(
				os.path.join(
					self.album.subdir,
					album_prefix + photo_cache_name(
						self,
						Options.config['album_thumb_size'],
						"square"
					)
				)
			)
		# media thumbnail path
		caches.append(
			os.path.join(
				self.album.subdir,
				album_prefix + photo_cache_name(
					self,
					Options.config['media_thumb_size'],
					Options.config['media_thumb_type']
				)
			)
		)
		return caches
	@property
	def date(self):
		correct_date = None;
		if not self.is_valid:
			correct_date = datetime(1900, 1, 1)
		if "dateTimeOriginal" in self._attributes["metadata"]:
			correct_date = self._attributes["metadata"]["dateTimeOriginal"]
		elif "dateTime" in self._attributes["metadata"]:
			correct_date = self._attributes["metadata"]["dateTime"]
		else:
			correct_date = self._attributes["dateTimeFile"]
		return correct_date
	@property
	def year(self):
		return str(self.date.year)
	@property
	def month(self):
		return self.date.strftime("%B").capitalize() + " " + self.year
	@property
	def day(self):
		return str(self.date.day) + " " + self.month
	@property
	def year_month(self):
		return self.year + " " + self.month
	@property
	def year_month_day(self):
		return self.year_month + " " + self.day
	@property
	def year_album_path(self):
		return Options.config['by_date_string'] + "/" + self.year
	@property
	def month_album_path(self):
		return self.year_album_path + "/" + self.month
	@property
	def day_album_path(self):
		return self.month_album_path + "/" + self.day
	def __cmp__(self, other):
		try:
			date_compare = cmp(self.date, other.date)
		except TypeError:
			date_compare = 1
		if date_compare == 0:
			return cmp(self.name, other.name)
		return date_compare
	@property
	def attributes(self):
		return self._attributes
	@staticmethod
	def from_dict(album, dictionary, basepath):
		del dictionary["date"]
		media_path = os.path.join(basepath, dictionary["name"])
		
		del dictionary["name"]
		for key, value in dictionary.items():
			if key.startswith("dateTime"):
				try:
					dictionary[key] = datetime.strptime(value, Options.date_time_format)
				except KeyboardInterrupt:
					raise
				except ValueError:
					pass
			if key == "metadata":
				for key1, value1 in value.items():
					if key1.startswith("dateTime"):
						try:
							dictionary[key][key1] = datetime.strptime(value1, Options.date_time_format)
						except KeyboardInterrupt:
							raise
						except ValueError:
							pass
					
		return Media(album, media_path, None, dictionary)
	def to_dict(self):
		foldersAlbum = Options.config['folders_string']
		if (self.folders):
			foldersAlbum = os.path.join(foldersAlbum, self.folders)
		
		media = self.attributes
		media["name"]			= self.name
		media["cacheBase"]		= self.cache_base
		media["date"]			= self.date
		media["yearAlbum"]		= self.year_album_path
		media["monthAlbum"]		= self.month_album_path
		media["dayAlbum"]		= self.day_album_path
		media["dayAlbumCacheBase"]	= cache_base(self.day_album_path, True)
		
		# the following data don't belong properly to media, but to album, but they must be put here in order to work with dates structure
		media["albumName"]		= self.album_path
		media["foldersAlbum"]		= foldersAlbum
		media["foldersCacheBase"]	= self.album.cache_base
		media["cacheSubdir"]		= self.album.subdir
		
		return media

class PhotoAlbumEncoder(json.JSONEncoder):
	def default(self, obj):
		if isinstance(obj, datetime):
			return obj.strftime("%Y-%m-%d %H:%M:%S")
		if isinstance(obj, Album) or isinstance(obj, Media):
			return obj.to_dict()
		return json.JSONEncoder.default(self, obj)

