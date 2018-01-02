# -*- coding: utf-8 -*-

# gps code got from https://gist.github.com/erans/983821

import locale
locale.setlocale(locale.LC_ALL, '')
from CachePath import *
from datetime import datetime
from Geonames import *
import json
import os
import os.path
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
from multiprocessing import Pool
import gc
import tempfile
from VideoToolWrapper import *
import math
import Options
import hashlib
import sys
from pprint import pprint
import pprint

def make_photo_thumbs(self, image, original_path, thumbs_path, thumb_size, thumb_type = ""):
	# The pool methods use a queue.Queue to pass tasks to the worker processes.
	# Everything that goes through the queue.Queue must be pickable, and since
	# self.reduce_size_or_make_thumbnail is not defined at the top level, it's not pickable.
	# This is why we have this "dummy" function, so that it's pickable.
	try:
		self.reduce_size_or_make_thumbnail(image, original_path, thumbs_path, thumb_size, thumb_type)
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
				self.baseless_path.find(Options.config['by_date_string']) != 0 or
				self.baseless_path.find(Options.config['by_gps_string']) != 0
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
		if hasattr(self, name):
			return self.name
		else:
			return self.path

	@property
	def json_file(self):
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

	def to_json_file(self):
		json_file_with_path = os.path.join(Options.config['cache_path'], self.json_file)
		if os.path.exists(json_file_with_path) and not os.access(json_file_with_path, os.W_OK):
			message("FATAL ERROR", json_file_with_path + " not writable, quitting")
			sys.exit(-97)
		message("sorting album...", "", 5)
		self.sort_subalbums_and_media()
		next_level()
		message("album sorted", self.absolute_path, 4)
		back_level()
		message("saving album...", "", 5)
		with open(json_file_with_path, 'w') as fp:
			json.dump(self, fp, cls=PhotoAlbumEncoder)
		next_level()
		message("album saved", json_file_with_path, 3)
		back_level()

	@staticmethod
	def from_cache(path, album_cache_base):
		message("reading album...", "", 5)
		with open(path, "r") as fp:
			dictionary = json.load(fp)
		next_level()
		message("album read", path, 5)
		back_level()
		# generate the album from the json file loaded
		# subalbums are not generated yet
		message("converting album to dictionary...", "", 5)
		dictionary = Album.from_dict(dictionary, album_cache_base)
		next_level()
		if dictionary is not None:
			message("album converted to dictionary", "", 4)
		else:
			message("json version unexistent or old", "", 4)
		back_level()
		return dictionary

	@staticmethod
	def from_dict(dictionary, album_cache_base, cripple=True):
		if "physicalPath" in dictionary:
			path = dictionary["physicalPath"]
		else:
			path = dictionary["path"]
		if not "jsonVersion" in dictionary or float(dictionary["jsonVersion"]) != Options.json_version:
			return None
		album = Album(os.path.join(Options.config['album_path'], path))
		album.cache_base = album_cache_base
		album.json_version= dictionary["jsonVersion"]
		for media in dictionary["media"]:
			new_media = Media.from_dict(album, media, os.path.join(Options.config['album_path'], remove_folders_marker(album.baseless_path)))
			if new_media.is_valid:
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

					sub_dict = {
						"path": path_to_dict,
						"cacheBase": sub.cache_base,
						"date": sub.date,
						"numMediaInSubTree": sub.num_media_in_sub_tree
					}
					if hasattr(sub, "center"):
						sub_dict["center"] = sub.center
					if hasattr(sub, "name"):
						sub_dict["name"] = sub.name
					if hasattr(sub, "alt_name"):
						sub_dict["alt_name"] = sub.alt_name
					subalbums.append(sub_dict)

		else:
			# it looks like the following code is never executed
			for sub in self.albums_list:
				if not sub.empty:
					subalbums.append(sub)

		path_without_folders_marker = remove_folders_marker(self.path)

		path_to_dict = self.path
		folder_position = path_to_dict.find(Options.config['folders_string'])
		by_date_position = path_to_dict.find(Options.config['by_date_string'])
		by_gps_position = path_to_dict.find(Options.config['by_gps_string'])
		if path_to_dict and by_date_position == -1 and by_gps_position == -1 and self.cache_base != "root" and folder_position != 0:
			path_to_dict = Options.config['folders_string'] + '/' + path_to_dict

		ancestors_cache_base = list()
		ancestors_center = list()
		_parent = self
		while True:
			ancestors_cache_base.append(_parent.cache_base)
			if hasattr(_parent, "center"):
				ancestors_center.append(_parent.center)
			else:
				ancestors_center.append("")
			if _parent.parent is None:
				break
			_parent = _parent.parent
		ancestors_cache_base.reverse()
		ancestors_center.reverse()

		dictionary = {
			"path": path_to_dict,
			"absolutePath": self.absolute_path,
			"cacheSubdir": self._subdir,
			"date": self.date,
			"albums": subalbums,
			"media": self.media_list,
			"cacheBase": self.cache_base,
			"ancestorsCacheBase": ancestors_cache_base,
			"ancestorsCenter": ancestors_center,
			"physicalPath": path_without_folders_marker,
			"numMediaInSubTree": self.num_media_in_sub_tree,
			"numMediaInAlbum": self.num_media_in_album,
			"jsonVersion": Options.json_version
		}
		if hasattr(self, "center"):
			dictionary["center"] = self.center
		if hasattr(self, "name"):
			dictionary["name"] = self.name
		if hasattr(self, "alt_name"):
			dictionary["alt_name"] = self.alt_name

		if self.parent is not None:
			dictionary["parentCacheBase"] = self.parent.cache_base
		return dictionary
	def media_from_path(self, path):
		_path = remove_album_path(path)
		for media in self.media_list:
			if _path == media.media_file_name:
				return media
		return None

class Media(object):
	def __init__(self, album, media_path, thumbs_path=None, attributes=None):
		self.album = album
		self.media_file_name = remove_album_path(media_path)
		dirname = os.path.dirname(media_path)
		self.folders = remove_album_path(dirname)
		self.album_path = os.path.join(Options.config['server_album_path'], self.media_file_name)

		self.is_valid = True
		self.has_exif_date = False

		image = None
		try:
			mtime = file_mtime(media_path)
			dir_mtime = file_mtime(dirname)
		except KeyboardInterrupt:
			raise
		except:
			next_level()
			message("could not read file or dir mtime", media_path, 5)
			back_level()
			self.is_valid = False
			return

		if Options.config['checksum']:
			next_level()
			message("generating checksum...", media_path, 5)
			this_checksum = checksum(media_path)
			next_level()
			message("checksum generated", "", 5)
			back_level()
			back_level()

		if (
			attributes is not None and
			attributes["dateTimeFile"] >= mtime and
			(not Options.config['checksum'] or 'checksum' in attributes and attributes['checksum'] == this_checksum)
		):
			self._attributes = attributes
			self._attributes["dateTimeDir"] = dir_mtime
			self.cache_base = attributes["cacheBase"]
			return

		self._attributes = {}
		self._attributes["metadata"] = {}
		self._attributes["dateTimeFile"] = mtime
		self._attributes["dateTimeDir"] = dir_mtime
		self._attributes["mediaType"] = "photo"
		self.cache_base = cache_base(trim_base_custom(media_path, album.absolute_path))

		# let's avoid that different media names have the same cache base
		distinguish_suffix = 0
		while True:
			_cache_base = self.cache_base
			if distinguish_suffix:
				_cache_base += "_" + str(distinguish_suffix)
			cache_name_absent = True
			if any(_cache_base == _media.cache_base and self.media_file_name != _media.media_file_name for _media in album.media_list):
				distinguish_suffix += 1
			else:
				self.cache_base = _cache_base
				break

		try:
			image = Image.open(media_path)
		except KeyboardInterrupt:
			raise
		except IOError:
			next_level()
			message("Image.open() raised IOError, could be a video", media_path, 5)
			back_level()
		except ValueError:
			# PIL cannot read this file (seen for .xpm file)
			# next lines will detect that the image is invalid
			next_level()
			message("ValueError when Image.open(), could be a video", media_path, 5)
			back_level()

		if self.is_valid:
			if isinstance(image, Image.Image):
				self._photo_metadata(image)
				self._photo_thumbnails(image, media_path, Options.config['cache_path'])
				if self.has_gps_data:
					next_level()
					message("looking for geonames...", media_path, 5)
					geoname = Geonames()
					self._attributes["geoname"] = geoname.lookup_nearby_place(self.latitude, self.longitude)
					# self._attributes["geoname"] is a dictionary with this data:
					#  'country_name': the country name in given language
					#  'country_code': the ISO country code
					#  'region_name': the administrative name (the region in normal states, the state in federative states) in given language
					#  'region_code': the corresponding geonames code
					#  'place_name': the nearby place name
					#  'place_code': the nearby place geonames id
					#  'distance': the distance between given coordinates and nearby place geonames coordinates
					back_level()
			else:
				# try with video detection
				self._video_metadata(media_path)
				if self._attributes["mediaType"] == "video":
					self._video_transcode(thumbs_path, media_path)
					if self.is_valid:
						self._video_thumbnails(thumbs_path, media_path)
				else:
					next_level()
					message("error transcodind, not a video?", media_path, 5)
					back_level()
					self.is_valid = False
		return

	def _photo_metadata(self, image):
		next_level()
		message("extracting metadata...", "", 5)
		back_level()
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

			if decoded == "GPSInfo":
				gps_data = {}
				for t in value:
					sub_decoded = GPSTAGS.get(t, t)
					gps_data[sub_decoded] = value[t]
					exif[decoded] = gps_data
			else:
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
				self._attributes["metadata"]["dateTime"] = datetime.strptime(exif["DateTimeOriginal"], Options.exif_date_time_format)
			except KeyboardInterrupt:
				raise
			except ValueError:
				# value isn't usable, forget it
				pass
		elif "DateTime" in exif:
			try:
				self._attributes["metadata"]["dateTime"] = datetime.strptime(exif["DateTime"], Options.exif_date_time_format)
			except KeyboardInterrupt:
				raise
			except ValueError:
				# value isn't usable, forget it
				pass

		if "GPSInfo" in exif:
			gps_latitude = exif["GPSInfo"].get("GPSLatitude", None)
			gps_latitude_ref = exif["GPSInfo"].get('GPSLatitudeRef', None)
			gps_longitude = exif["GPSInfo"].get('GPSLongitude', None)
			gps_longitude_ref = exif["GPSInfo"].get('GPSLongitudeRef', None)
			if gps_latitude and gps_latitude_ref and gps_longitude and gps_longitude_ref:
				self._attributes["metadata"]["latitude"] = self._convert_to_degrees_decimal(gps_latitude, gps_latitude_ref)
				self._attributes["metadata"]["latitudeMS"] = self._convert_to_degrees_minutes_seconds(gps_latitude, gps_latitude_ref)
				self._attributes["metadata"]["longitude"] = self._convert_to_degrees_decimal(gps_longitude, gps_longitude_ref)
				self._attributes["metadata"]["longitudeMS"] = self._convert_to_degrees_minutes_seconds(gps_longitude, gps_longitude_ref)
		next_level()
		message("extracted", "", 5)
		back_level()

	def _convert_to_degrees_minutes_seconds(self, value, ref):
		# Helper function to convert the GPS coordinates stored in the EXIF to degrees, minutes and seconds

		# Degrees
		d0 = value[0][0]
		d1 = value[0][1]
		d = int(float(d0) / float(d1))
		# Minutes
		m0 = value[1][0]
		m1 = value[1][1]
		m = int(float(m0) / float(m1))
		# Seconds
		s0 = value[2][0]
		s1 = value[2][1]
		s = int((float(s0) / float(s1)) * 1000) / 1000.0

		# result = ''
		# if ref == "S" or ref == "W":
		# 	result = '-'

		result = str(d) + "º " + str(m) + "' " + str(s) + '" ' + ref

		return result

	def _convert_to_degrees_decimal(self, value, ref):
		#Helper function to convert the GPS coordinates stored in the EXIF to degress in float format

		# Degrees
		d0 = value[0][0]
		d1 = value[0][1]
		d = float(d0) / float(d1)
		# Minutes
		m0 = value[1][0]
		m1 = value[1][1]
		m = float(m0) / float(m1)
		# Seconds
		s0 = value[2][0]
		s1 = value[2][1]
		s = float(s0) / float(s1)

		result = d + (m / 60.0) + (s / 3600.0)
		# limit decimal digits to what is needed by openstreetmap
		six_zeros = 1000000.0
		result = int(result * six_zeros) / six_zeros
		if ref == "S" or ref == "W":
			result = - result
		return result


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
			next_level()
			message("error probing video, not a video?", path, 5)
			back_level()
			self.is_valid = False
			return
		info = json.loads(p)
		for s in info["streams"]:
			if 'codec_type' in s:
				next_level()
				message("debug: s[codec_type]", s['codec_type'], 5)
				back_level()
			if 'codec_type' in s and s['codec_type'] == 'video':
				self._attributes["mediaType"] = "video"
				self._attributes["metadata"]["size"] = (int(s["width"]), int(s["height"]))
				if "duration" in s:
					self._attributes["metadata"]["duration"] = round(float(s["duration"]) * 10) / 10
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
			message("WARNING: Photo couldn't be trasposed", photo_path, 2)
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
			thumb_type == "fixed_height" and
			(thumb_size == Options.config['media_thumb_size'] or thumb_size == int(round(Options.config['media_thumb_size'] * Options.config['mobile_thumbnail_factor']))) and
			image_width > image_height
		):
			veredict = (thumb_size < image_height)
		elif thumb_type == "square":
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
		thumb = self.reduce_size_or_make_thumbnail(image, photo_path, thumbs_path, thumb_size)
		self._photo_thumbnails_parallel(thumb, photo_path, thumbs_path)

	def _photo_thumbnails_cascade(self, image, photo_path, thumbs_path):
		# this function calls self.reduce_size_or_make_thumbnail() with the proper image self.reduce_size_or_make_thumbnail() needs
		# so that the thumbnail doesn't get blurred
		thumb = image
		image_width = image.size[0]
		image_height = image.size[1]
		for thumb_size in Options.config['reduced_sizes']:
			thumb = self.reduce_size_or_make_thumbnail(thumb, photo_path, thumbs_path, thumb_size)
		smallest_reduced_size_image = thumb

		# album size: square thumbnail are generated anyway, because they are needed by the code that generates composite images for sharing albums
		(thumb_size, thumb_type) = (Options.config['album_thumb_size'], Options.config['album_thumb_type'])

		# if requested, generate the bigger thumbnail for mobile
		if Options.config['mobile_thumbnail_factor'] > 1:
			mobile_thumb_size = int(round(thumb_size * Options.config['mobile_thumbnail_factor']))
			if self.thumbnail_size_is_smaller_then_size_of_(smallest_reduced_size_image, mobile_thumb_size, thumb_type):
				thumb = self.reduce_size_or_make_thumbnail(smallest_reduced_size_image, photo_path, thumbs_path, thumb_size, thumb_type, True)
			else:
				thumb = self.reduce_size_or_make_thumbnail(image, photo_path, thumbs_path, thumb_size, thumb_type, True)

		for i in range(2):
			if thumb_type == "fit" or self.thumbnail_size_is_smaller_then_size_of_(smallest_reduced_size_image, thumb_size, thumb_type):
				thumb = self.reduce_size_or_make_thumbnail(smallest_reduced_size_image, photo_path, thumbs_path, thumb_size, thumb_type)
			else:
				thumb = self.reduce_size_or_make_thumbnail(image, photo_path, thumbs_path, thumb_size, thumb_type)
			if i == 0:
				if thumb_type == "square":
					# no need for a second iteration
					break
				elif thumb_type == "fit":
					thumb_type = "square"

		# media size
		# at this point thumb is always square
		(thumb_size, thumb_type) = (Options.config['media_thumb_size'], Options.config['media_thumb_type'])

		# if requested, generate the bigger thumbnail for mobile
		if Options.config['mobile_thumbnail_factor'] > 1:
			if self.thumbnail_size_is_smaller_then_size_of_(smallest_reduced_size_image, mobile_thumb_size, thumb_type):
				thumb = self.reduce_size_or_make_thumbnail(smallest_reduced_size_image, photo_path, thumbs_path, thumb_size, thumb_type, True)
			else:
				thumb = self.reduce_size_or_make_thumbnail(image, photo_path, thumbs_path, thumb_size, thumb_type, True)

		if self.thumbnail_size_is_smaller_then_size_of_(smallest_reduced_size_image, thumb_size, thumb_type):
			thumb = self.reduce_size_or_make_thumbnail(smallest_reduced_size_image, photo_path, thumbs_path, thumb_size, thumb_type)
		else:
			thumb = self.reduce_size_or_make_thumbnail(image, photo_path, thumbs_path, thumb_size, thumb_type)

	def is_thumbnail(self, thumb_size, thumb_type):
		_is_thumbnail = (thumb_type != "")
		return _is_thumbnail

	def reduce_size_or_make_thumbnail(self, start_image, original_path, thumbs_path, thumb_size, thumb_type = "", mobile_bigger = False):
		album_prefix = remove_folders_marker(self.album.cache_base) + Options.config["cache_folder_separator"]
		if album_prefix == Options.config["cache_folder_separator"]:
			album_prefix = ""
		thumbs_path_with_subdir = os.path.join(thumbs_path, self.album.subdir)
		actual_thumb_size = thumb_size
		media_thumb_size = Options.config['media_thumb_size']
		album_thumb_size = Options.config['album_thumb_size']
		if mobile_bigger:
			actual_thumb_size = int(round(actual_thumb_size * Options.config['mobile_thumbnail_factor']))
			media_thumb_size = int(round(media_thumb_size * Options.config['mobile_thumbnail_factor']))
			album_thumb_size = int(round(album_thumb_size * Options.config['mobile_thumbnail_factor']))
		thumb_path = os.path.join(thumbs_path_with_subdir, album_prefix + photo_cache_name(self, thumb_size, thumb_type, mobile_bigger))
		# if the reduced image/thumbnail is there and is valid, exit immediately
		json_file = os.path.join(thumbs_path, self.album.json_file)
		_is_thumbnail = self.is_thumbnail(thumb_size, thumb_type)
		is_video = self._attributes["mediaType"] == "video"
		next_level()
		message("checking reduction/thumbnail", thumb_path, 5)
		if (
			os.path.exists(thumbs_path_with_subdir) and
			os.path.exists(thumb_path) and
			file_mtime(thumb_path) >= self._attributes["dateTimeFile"] and
			(
				not os.path.exists(json_file) or file_mtime(thumb_path) < file_mtime(json_file)
			) and
			(
				not _is_thumbnail and not Options.config['recreate_reduced_photos'] or
				_is_thumbnail and not Options.config['recreate_thumbnails']
			)
		):
			next_level()
			message("reduction/thumbnail OK, skipping", "", 5)
			back_level()
			back_level()
			return start_image

		next_level()
		message("reduction/thumbnail not OK, creating", thumbs_path_with_subdir, 5)
		next_level()
		if not os.path.exists(thumbs_path_with_subdir):
			message("unexistent subdir", thumbs_path_with_subdir, 5)
		elif not os.path.exists(thumb_path):
			message("unexistent reduction/thumbnail", thumb_path, 5)
		elif not file_mtime(thumb_path) >= self._attributes["dateTimeFile"]:
			message("reduction/thumbnail older than media date time", thumb_path, 5)
		elif not os.path.exists(json_file):
			message("unexistent json file", json_file, 5)
		elif not file_mtime(thumb_path) < file_mtime(json_file):
			message("reduction/thumbnail newer than json file", thumb_path + ", " + json_file, 5)
		back_level()
		message("calculations...", "", 5)
		original_thumb_size = actual_thumb_size
		info_string = str(original_thumb_size)
		if thumb_type == "square":
			info_string += ", square"
		if thumb_size == Options.config['album_thumb_size'] and thumb_type == "fit":
			info_string += ", fit size"
		elif thumb_size == Options.config['media_thumb_size'] and thumb_type == "fixed_height":
			info_string += ", fixed height"
		if mobile_bigger:
			info_string += " (mobile)"

		start_image_width = start_image.size[0]
		start_image_height = start_image.size[1]
		if thumb_type == "square":
			# image is to be cropped: calculate the cropping values
			if min(start_image_width, start_image_height) >= actual_thumb_size:
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
				thumbnail_width = actual_thumb_size
				thumbnail_height = actual_thumb_size
				must_crop = True
			elif max(start_image_width, start_image_height) >= actual_thumb_size:
				# image smallest size is smaller than the square which would result from cropping
				# cropped image will not be square
				if start_image_width > start_image_height:
					left = (start_image_width - actual_thumb_size) / 2
					top = 0
					right = start_image_width - left
					bottom = start_image_height
					thumbnail_width = actual_thumb_size
					thumbnail_height = start_image_height
				else:
					left = 0
					top = (start_image_height - actual_thumb_size) / 2
					right = start_image_width
					bottom = start_image_height - top
					thumbnail_width = start_image_width
					thumbnail_height = actual_thumb_size
				must_crop = True
			else:
				# image is smaller than the square thumbnail, don't crop it
				thumbnail_width = start_image_width
				thumbnail_height = start_image_height
				must_crop = False
		else:
			must_crop = False
			if (
				original_thumb_size == media_thumb_size and
				thumb_type == "fixed_height" and
				start_image_width > start_image_height
			):
				# the thumbnail size will not be thumb_size, the image will be greater
				thumbnail_height = original_thumb_size
				thumbnail_width = int(round(original_thumb_size * start_image_width / float(start_image_height)))
				actual_thumb_size = thumbnail_width
			elif start_image_width > start_image_height:
				thumbnail_width = actual_thumb_size
				thumbnail_height = int(round(actual_thumb_size * start_image_height / float(start_image_width)))
			else:
				thumbnail_width = int(round(actual_thumb_size * start_image_width / float(start_image_height)))
				thumbnail_height = actual_thumb_size

		# now thumbnail_width and thumbnail_height are the values the thumbnail will get,
		# and if the thumbnail isn't a square one, their ratio is the same of the original image

		must_resize = True
		if max(start_image_width, start_image_height) <= actual_thumb_size:
			# resizing to thumbnail size an image smaller than the thumbnail to produce would return a blurred image
			# simply copy the start image to the thumbnail
			must_resize = False
			if not mobile_bigger and original_thumb_size > Options.config['album_thumb_size'] or mobile_bigger and original_thumb_size > int(Options.config['album_thumb_size'] * Options.config['mobile_thumbnail_factor']):
				message("small image, no reduction", info_string, 4)
			elif not mobile_bigger and original_thumb_size == Options.config['album_thumb_size'] or mobile_bigger and original_thumb_size == int(Options.config['album_thumb_size'] * Options.config['mobile_thumbnail_factor']):
				message("small image, no thumbing for album", info_string, 4)
			else:
				message("small image, no thumbing for media", info_string, 4)

		try:
			message("making copy...", "", 5)
			start_image_copy = start_image.copy()
			next_level()
			message("copy made", info_string, 4)
			back_level()
		except KeyboardInterrupt:
			raise
		except:
			# we try again to work around PIL bug
			message("making copy (2nd try)...", info_string, 5)
			start_image_copy = start_image.copy()
			next_level()
			message("copy made (2nd try)", info_string, 5)
			back_level()

		# both width and height of thumbnail are less then width and height of start_image, no blurring will happen
		# we can resize, but first crop to square if needed
		if must_crop:
			message("cropping...", info_string, 4)
			start_image_copy = start_image_copy.crop((left, top, right, bottom))
			next_level()
			message("cropped (" + str(original_thumb_size) + ")", "", 5)
			back_level()

		if must_resize:
			# resizing
			if original_thumb_size > Options.config['album_thumb_size']:
				message("reducing size...", info_string, 5)
			elif original_thumb_size == Options.config['album_thumb_size']:
				message("thumbing for albums...", info_string, 5)
			else:
				message("thumbing for media...", info_string, 5)
			start_image_copy.thumbnail((actual_thumb_size, actual_thumb_size), Image.ANTIALIAS)
			next_level()
			if not mobile_bigger and original_thumb_size > Options.config['album_thumb_size'] or mobile_bigger and original_thumb_size > int(Options.config['album_thumb_size'] * Options.config['mobile_thumbnail_factor']):
				message("reduced size (" + str(original_thumb_size) + ")", "", 4)
			elif not mobile_bigger and original_thumb_size == Options.config['album_thumb_size'] or mobile_bigger and original_thumb_size == int(Options.config['album_thumb_size'] * Options.config['mobile_thumbnail_factor']):
				message("thumbed for albums (" + str(original_thumb_size) + ")", "", 4)
			else:
				message("thumbed for media (" + str(original_thumb_size) + ")", "", 4)
			back_level()

		# the subdir hadn't been created when creating the album in order to avoid creation of empty directories
		if not os.path.exists(thumbs_path_with_subdir):
			message("creating unexistent subdir", "", 5)
			os.makedirs(thumbs_path_with_subdir)
			next_level()
			message("unexistent subdir created", thumbs_path_with_subdir, 4)
			back_level()

		if os.path.exists(thumb_path) and not os.access(thumb_path, os.W_OK):
			message("FATAL ERROR", thumb_path + " not writable, quitting")
			sys.exit(-97)

		if self._attributes["mediaType"] == "video":
			message("adding video transparency...", "", 5)
			start_image_copy_for_saving = start_image_copy.copy()
			transparency_file = os.path.join(os.path.dirname(__file__), "../web/img/play_button_100_62.png")
			video_transparency = Image.open(transparency_file)
			x = (start_image_copy.size[0] - video_transparency.size[0]) / 2
			y = (start_image_copy.size[1] - video_transparency.size[1]) / 2
			start_image_copy_for_saving.paste(video_transparency, (x, y), video_transparency)
			next_level()
			message("video transparency added", "", 4)
			back_level()
		else:
			start_image_copy_for_saving = start_image_copy

		message("saving...", info_string, 5)
		try:
			start_image_copy_for_saving.save(thumb_path, "JPEG", quality=Options.config['jpeg_quality'])
			next_level()
			if original_thumb_size > Options.config['album_thumb_size']:
				message("saved reduced", thumb_path, 4)
			elif original_thumb_size == Options.config['album_thumb_size']:
				message("saved for albums", thumb_path, 4)
			else:
				message("saved for media", thumb_path, 4)
			back_level()
			back_level()
			back_level()
			return start_image_copy
		except KeyboardInterrupt:
			try:
				os.unlink(thumb_path)
			except OSError:
				pass
			raise
		except IOError:
			message("saving (2nd try)...", info_string, 5)
			try:
				start_image_copy_for_saving.convert('RGB').save(thumb_path, "JPEG", quality=Options.config['jpeg_quality'])
				next_level()
				if original_thumb_size > Options.config['album_thumb_size']:
					message("saved reduced (2nd try, " + str(original_thumb_size) + ")", "", 2)
				elif original_thumb_size == Options.config['album_thumb_size']:
					message("saved for albums (2nd try, " + str(original_thumb_size) + ")", "", 2)
				else:
					message("saved for media (2nd try, " + str(original_thumb_size) + ")", "", 2)
				back_level()
			except KeyboardInterrupt:
				try:
					os.unlink(thumb_path)
				except OSError:
					pass
			back_level()
			back_level()
			return start_image_copy
		except:
			next_level()
			message(str(original_thumb_size) + " thumbnail", "save failure to " + os.path.basename(thumb_path), 1)
			back_level()
			try:
				os.unlink(thumb_path)
			except OSError:
				pass
			back_level()
			back_level()
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
			next_level()
			message("error extracting video frame", path, 5)
			back_level()
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
			message("error opening video thumbnail", tfn + " from " + path, 5)
			back_level()
			self.is_valid = False
			try:
				os.unlink(tfn)
			except OSError:
				pass
			return
		mirror = image
		if "rotate" in self._attributes:
			if self._attributes["metadata"]["rotate"] == "90":
				mirror = image.transpose(Image.ROTATE_270)
			elif self._attributes["metadata"]["rotate"] == "180":
				mirror = image.transpose(Image.ROTATE_180)
			elif self._attributes["metadata"]["rotate"] == "270":
				mirror = image.transpose(Image.ROTATE_90)

		mobile_bigger = False
		for n in range(2):
			(thumb_size, thumb_type) = (Options.config['album_thumb_size'], Options.config['album_thumb_type'])
			self.reduce_size_or_make_thumbnail(mirror, original_path, thumbs_path, thumb_size, thumb_type, mobile_bigger)
			if thumb_type == "fit" and not mobile_bigger:
				# square thumbnail is needed too for sharing albums
				thumb_type = "square"
				self.reduce_size_or_make_thumbnail(mirror, original_path, thumbs_path, thumb_size, thumb_type, mobile_bigger)

			(thumb_size, thumb_type) = (Options.config['media_thumb_size'], Options.config['media_thumb_type'])
			self.reduce_size_or_make_thumbnail(mirror, original_path, thumbs_path, thumb_size, thumb_type, mobile_bigger)

			if Options.config['mobile_thumbnail_factor'] == 1:
				break
			mobile_bigger = True

		try:
			os.unlink(tfn)
		except OSError:
			pass

	def _video_transcode(self, transcode_path, original_path):
		album_prefix = remove_folders_marker(self.album.cache_base) + Options.config["cache_folder_separator"]
		if album_prefix == Options.config["cache_folder_separator"]:
			album_prefix = ""

		album_cache_path = os.path.join(transcode_path, self.album.subdir)
		if os.path.exists(album_cache_path):
			if not os.access(album_cache_path, os.W_OK):
				message("FATAL ERROR", album_cache_path + " not writable, quitting")
				sys.exit(-97)
		else:
			message("creating still unexistent album cache subdir", "", 5)
			os.makedirs(album_cache_path)
			next_level()
			message("created still unexistent subdir", album_cache_path, 4)
			back_level()

		transcode_path = os.path.join(album_cache_path, album_prefix + video_cache_name(self))
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

		next_level()
		message("transcoding...", info_string, 5)
		tmp_transcode_cmd = transcode_cmd[:]
		transcode_cmd.append(transcode_path)
		try:
			p = VideoTranscodeWrapper().call(*transcode_cmd)
			if p != False:
				next_level()
				message("transcoded", "", 4)
				back_level()
		except KeyboardInterrupt:
			raise

		if p == False:
			# add another option, try transcoding again
			# done to avoid this error;
			# x264 [error]: baseline profile doesn't support 4:2:2
			next_level()
			message("transcoding failure, trying yuv420p...", "", 3)
			tmp_transcode_cmd.append('-pix_fmt')
			tmp_transcode_cmd.append('yuv420p')
			tmp_transcode_cmd.append(transcode_path)
			try:
				p = VideoTranscodeWrapper().call(*tmp_transcode_cmd)
				if p != False:
					next_level()
					message("transcoded with yuv420p", "", 2)
					back_level()
			except KeyboardInterrupt:
				raise

			if p == False:
				next_level()
				message("transcoding failure", os.path.basename(original_path), 1)
				back_level()
				self.is_valid = False
				try:
					os.unlink(transcode_path)
				except OSError:
					pass
			back_level()

		if self.is_valid:
			self._video_metadata(transcode_path, False)
		back_level()

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
		if album_prefix == Options.config["cache_folder_separator"]:
			album_prefix = ""
		if "mediaType" in self._attributes and self._attributes["mediaType"] == "video":
			# transcoded video path
			caches.append(os.path.join(self.album.subdir, album_prefix + video_cache_name(self)))
		else:
			# reduced sizes paths
			for thumb_size in Options.config['reduced_sizes']:
				caches.append(
					os.path.join(
						self.album.subdir,
						album_prefix + photo_cache_name(self,thumb_size)
					)
				)
		# album thumbnail path
		mobile_bigger = False
		for n in range(2):
			caches.append(
				os.path.join(
					self.album.subdir,
					album_prefix + photo_cache_name(
						self,
						Options.config['album_thumb_size'],
						Options.config['album_thumb_type'],
						mobile_bigger
					)
				)
			)
			if Options.config['album_thumb_type'] == "fit" and not mobile_bigger:
				# album square thumbnail path (it's generated always)
				caches.append(
					os.path.join(
						self.album.subdir,
						album_prefix + photo_cache_name(
							self,
							Options.config['album_thumb_size'],
							"square",
							mobile_bigger
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
						Options.config['media_thumb_type'],
						mobile_bigger
					)
				)
			)
			if Options.config['mobile_thumbnail_factor'] == 1:
				break
			mobile_bigger = True
		return caches

	@property
	def date(self):
		correct_date = None;
		if not self.is_valid:
			correct_date = datetime(1900, 1, 1)
		if "dateTimeOriginal" in self._attributes["metadata"]:
			correct_date = self._attributes["metadata"]["dateTimeOriginal"]
			self.has_exif_date = True
		elif "dateTime" in self._attributes["metadata"]:
			correct_date = self._attributes["metadata"]["dateTime"]
			self.has_exif_date = True
		else:
			correct_date = self._attributes["dateTimeFile"]
		return correct_date

	@property
	def has_gps_data(self):
		return "latitude" in self._attributes["metadata"]

	@property
	def latitude(self):
		return self._attributes["metadata"]["latitude"]

	@property
	def longitude(self):
		return self._attributes["metadata"]["longitude"]

	@property
	def year(self):
		return str(self.date.year)

	@property
	def month(self):
		#~ return self.date.strftime("%B").capitalize() + " " + self.year
		return self.date.strftime("%m")

	@property
	def day(self):
		return str(self.date.day).zfill(2)

	@property
	def country_name(self):
		return self._attributes["geoname"]["country_name"]

	@property
	def country_code(self):
		return self._attributes["geoname"]["country_code"]

	@property
	def region_name(self):
		return self._attributes["geoname"]["region_name"]

	@property
	def region_code(self):
		return self._attributes["geoname"]["region_code"]

	@property
	def place_name(self):
		return self._attributes["geoname"]["place_name"]

	@property
	def place_code(self):
		return self._attributes["geoname"]["place_code"]

	@property
	def year_album_path(self):
		return Options.config['by_date_string'] + "/" + self.year

	@property
	def month_album_path(self):
		return self.year_album_path + "/" + self.month

	@property
	def day_album_path(self):
		return self.month_album_path + "/" + self.day

	@property
	def country_album_path(self):
		return Options.config['by_gps_string'] + "/" + self.country_code

	@property
	def region_album_path(self):
		return self.country_album_path + "/" + self.region_code

	@property
	def place_album_path(self):
		return self.region_album_path + "/" + self.place_code

	@property
	def gps_album_path(self):
		if hasattr(self, "gps_path"):
			return self.gps_path
		else:
			return ""

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
		media["name"]              = self.name
		media["cacheBase"]         = self.cache_base
		media["date"]              = self.date
		# media["yearAlbum"]		= self.year_album_path
		# media["monthAlbum"]		= self.month_album_path
		media["dayAlbum"]          = self.day_album_path
		media["dayAlbumCacheBase"] = cache_base(self.day_album_path, True)
		if self.gps_album_path:
			media["gpsAlbum"]          = self.gps_album_path
			media["gpsAlbumCacheBase"] = cache_base(self.gps_album_path, True)
		if Options.config['checksum']:
			media["checksum"]          = checksum(os.path.join(Options.config['album_path'], self.media_file_name))

		# the following data don't belong properly to media, but to album, but they must be put here in order to work with dates structure
		media["albumName"]         = self.album_path
		media["foldersAlbum"]      = foldersAlbum
		media["foldersCacheBase"]  = self.album.cache_base
		media["cacheSubdir"]       = self.album.subdir
		return media

class PhotoAlbumEncoder(json.JSONEncoder):
	def default(self, obj):
		if isinstance(obj, datetime):
			return obj.strftime("%Y-%m-%d %H:%M:%S")
		if isinstance(obj, Album) or isinstance(obj, Media):
			return obj.to_dict()
		return json.JSONEncoder.default(self, obj)
