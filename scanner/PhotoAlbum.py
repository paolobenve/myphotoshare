# -*- coding: utf-8 -*-

# gps code got from https://gist.github.com/erans/983821

import locale
locale.setlocale(locale.LC_ALL, '')

import json
import os
import os.path
import tempfile
import hashlib
import unicodedata
import sys
from datetime import datetime
from pprint import pprint
import pprint

# @python2
try:
	import configparser
except ImportError:
	import ConfigParser as configparser
try:
	from configparser import NoOptionError
except ImportError:
	from ConfigParser import NoOptionError

import math
import numpy as np

from CachePath import remove_album_path, remove_folders_marker, trim_base_custom, checksum, thumbnail_types_and_sizes, file_mtime, photo_cache_name, video_cache_name, find, find_in_usr_share
from Utilities import message, next_level, back_level
from Geonames import Geonames
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
from VideoToolWrapper import VideoProbeWrapper, VideoTranscodeWrapper
import Options


cv2_installed = True
thumbnail_types_and_sizes_list = None
try:
	import cv2

	message("importer", "opencv library available, using it!", 3)
	next_level()
	FACE_CONFIG_FILE = "haarcascade_frontalface_default.xml"
	message("looking for file...", FACE_CONFIG_FILE, 5)
	face_config_file_with_path = find_in_usr_share(FACE_CONFIG_FILE)
	if not face_config_file_with_path:
		face_config_file_with_path = find(FACE_CONFIG_FILE)
	if not face_config_file_with_path:
		next_level()
		message("face xml file not found", FACE_CONFIG_FILE, 5)
		back_level()
		cv2_installed = False
	else:
		face_cascade = cv2.CascadeClassifier(face_config_file_with_path)
		next_level()
		message("found and initialized:", face_config_file_with_path, 5)
		back_level()
		EYE_CONFIG_FILE = "haarcascade_eye.xml"
		message("looking for file...", EYE_CONFIG_FILE, 5)
		eye_config_file_with_path = find_in_usr_share(EYE_CONFIG_FILE)
		if not eye_config_file_with_path:
			eye_config_file_with_path = find(EYE_CONFIG_FILE)
		if not eye_config_file_with_path:
			next_level()
			message("eyes xml file not found", EYE_CONFIG_FILE, 5)
			back_level()
			cv2_installed = False
		else:
			eye_cascade = cv2.CascadeClassifier(eye_config_file_with_path)
			next_level()
			message("found and initialized:", eye_config_file_with_path, 5)
			back_level()
	back_level()
except ImportError:
	cv2_installed = False
	message("importer", "No opencv library available, not using it", 2)


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
		self.cache_base = ""
		self.media_list = list()
		self.albums_list = list()
		self.media_list_is_sorted = True
		self.albums_list_is_sorted = True
		self._subdir = ""
		self.num_media_in_sub_tree = 0
		self.num_media_in_album = 0
		self.parent = None
		self.album_ini = None
		self._attributes = {}
		self._attributes["metadata"] = {}
		self.json_version = {}

		if (
			Options.config['subdir_method'] in ("md5", "folder") and
			(
				self.baseless_path.find(Options.config['by_date_string']) != 0 or
				self.baseless_path.find(Options.config['by_gps_string']) != 0 or
				self.baseless_path.find(Options.config['by_search_string']) != 0
			)
		):
			if Options.config['subdir_method'] == "md5":
				# @python2
				if sys.version_info < (3, ):
					self._subdir = hashlib.md5(path).hexdigest()[:2]
				else:
					self._subdir = hashlib.md5(os.fsencode(path)).hexdigest()[:2]
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
		if hasattr(self, "name"):
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


	def __lt__(self, other):
		try:
			return self.date < other.date
		except TypeError:
			return True


	def read_album_ini(self):
		"""Read the 'album.ini' file in the directory 'self.absolute_path' to
		get user defined metadata for the album and pictures.
		"""
		self.album_ini = configparser.ConfigParser(allow_no_value=True)
		message("reading album.ini...", "", 5)
		self.album_ini.read(os.path.join(self.absolute_path, "album.ini"))
		next_level()
		message("album.ini read", os.path.join(self.absolute_path, "album.ini"), 5)
		back_level()

		Metadata.set_metadata_from_album_ini("album", self._attributes, self.album_ini)


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
			message("FATAL ERROR", json_file_with_path + " not writable, quitting", 0)
			sys.exit(-97)
		message("sorting album...", "", 5)
		self.sort_subalbums_and_media()
		next_level()
		message("album sorted", self.absolute_path, 4)
		back_level()
		message("saving album...", "", 5)
		with open(json_file_with_path, 'w') as filepath:
			json.dump(self, filepath, cls=PhotoAlbumEncoder)
		next_level()
		message("album saved", json_file_with_path, 3)
		back_level()

	@staticmethod
	def from_cache(path, album_cache_base):
		message("reading album...", "", 5)
		with open(path, "r") as filepath:
			dictionary = json.load(filepath)
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
		# Don't use cache if version has changed
		if "jsonVersion" not in dictionary or float(dictionary["jsonVersion"]) != Options.json_version:
			return None
		album = Album(os.path.join(Options.config['album_path'], path))
		album.cache_base = album_cache_base
		album.json_version = dictionary["jsonVersion"]
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
		by_search_position = path_to_dict.find(Options.config['by_search_string'])
		if path_to_dict and by_date_position == -1 and by_gps_position == -1 and by_search_position == -1 and self.cache_base != "root" and folder_position != 0:
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

	def generate_cache_base(self, subalbum_or_media_path, media_file_name=None):
		# this method calculate the cache base for a subalbum or a media in self album
		# for a media, the parameter media_file_name has to be given; in this case subalbum_or_media_path is the media file name without any path info
		# result only has ascii characters

		# respect alphanumeric characters, substitute non-alphanumeric (but not slashes) with underscore
		subalbum_or_media_path = "".join([c if c.isalnum() or c == '/' else "_" for c in subalbum_or_media_path])

		# convert slashes
		subalbum_or_media_path = subalbum_or_media_path.replace('/', Options.config['cache_folder_separator']).lower()

		# convert accented characters to ascii, from https://stackoverflow.com/questions/517923/what-is-the-best-way-to-remove-accents-in-a-python-unicode-string
		subalbum_or_media_path = ''.join(c for c in unicodedata.normalize('NFD', subalbum_or_media_path) if unicodedata.category(c) != 'Mn')

		while subalbum_or_media_path.find("__") != -1:
			subalbum_or_media_path = subalbum_or_media_path.replace("__", "_")
		while subalbum_or_media_path.find("-_") != -1:
			subalbum_or_media_path = subalbum_or_media_path.replace('-_', '-')
		while subalbum_or_media_path.find("_-") != -1:
			subalbum_or_media_path = subalbum_or_media_path.replace('_-', '-')
		while subalbum_or_media_path.find("--") != -1:
			subalbum_or_media_path = subalbum_or_media_path.replace("--", "-")

		if media_file_name is None and hasattr(self, "albums_list") or media_file_name is not None and hasattr(self, "media_list"):
			# let's avoid that different album/media with equivalent names have the same cache base
			distinguish_suffix = 0
			while True:
				_path = subalbum_or_media_path
				if distinguish_suffix:
					_path += "_" + str(distinguish_suffix)
				if (
					media_file_name is None     and any(_path == _album.cache_base and self.absolute_path != _album.absolute_path   for _album in self.albums_list) or
					media_file_name is not None and any(_path == _media.cache_base and media_file_name    != _media.media_file_name for _media in self.media_list)
				):
					distinguish_suffix += 1
				else:
					subalbum_or_media_path = _path
					break

		return subalbum_or_media_path

class Media(object):
	def __init__(self, album, media_path, thumbs_path=None, attributes=None):
		self.album = album
		self.media_file_name = remove_album_path(media_path)
		dirname = os.path.dirname(media_path)
		self.folders = remove_album_path(dirname)
		self.album_path = os.path.join(Options.config['server_album_path'], self.media_file_name)
		self.cache_base = album.generate_cache_base(trim_base_custom(media_path, album.absolute_path), self.media_file_name)

		self.is_valid = True

		image = None
		try:
			mtime = file_mtime(media_path)
			dir_mtime = file_mtime(dirname)
		except KeyboardInterrupt:
			raise
		except OSError:
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

					# Overwrite with album.ini values when album has been read from file
					if self.album.album_ini:
						Metadata.set_geoname_from_album_ini(self.name, self._attributes, self.album.album_ini)
					back_level()
			else:
				# try with video detection
				self._video_metadata(media_path)
				if self.is_video:
					self._video_transcode(thumbs_path, media_path)
					if self.is_valid:
						self._video_thumbnails(thumbs_path, media_path)

						if self.has_gps_data:
							next_level()
							message("looking for geonames...", media_path, 5)
							geoname = Geonames()
							self._attributes["geoname"] = geoname.lookup_nearby_place(self.latitude, self.longitude)
							# Overwrite with album.ini values when read from file
							if self.album.album_ini:
								Metadata.set_geoname_from_album_ini(self.name, self._attributes, self.album.album_ini)
							back_level()
				else:
					next_level()
					message("error transcodind, not a video?", media_path, 5)
					back_level()
					self.is_valid = False
		return


	@property
	def datetime_file(self):
		return self._attributes["dateTimeFile"]


	@property
	def datetime_dir(self):
		return self._attributes["dateTimeDir"]


	def _photo_metadata(self, image):
		next_level()
		message("extracting metadata...", "", 5)
		self._attributes["metadata"]["size"] = image.size
		self._orientation = 1
		try:
			info = image._getexif()
		except KeyboardInterrupt:
			raise
		except:
			next_level()
			message("unknown error extracting metadata", "", 5)
			back_level()
			back_level()
			return

		if not info:
			next_level()
			message("empty metadata", "", 5)
			back_level()
			back_level()
			return

		exif = {}
		for tag, value in list(info.items()):
			decoded = TAGS.get(tag, tag)
			if (isinstance(value, tuple) or isinstance(value, list)) and (isinstance(decoded, str) or isinstance(decoded, str)) and decoded.startswith("DateTime") and len(value) >= 1:
				value = value[0]
			if isinstance(value, str) or isinstance(value, str):
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
				for gps_tag in value:
					sub_decoded = GPSTAGS.get(gps_tag, gps_tag)
					gps_data[sub_decoded] = value[gps_tag]
					exif[decoded] = gps_data
			else:
				exif[decoded] = value

		if "Orientation" in exif:
			self._orientation = exif["Orientation"]
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

		gps_latitude = None
		gps_latitude_ref = None
		gps_longitude = None
		gps_longitude_ref = None
		if "GPSInfo" in exif:
			gps_latitude = exif["GPSInfo"].get("GPSLatitude", None)
			gps_latitude_ref = exif["GPSInfo"].get("GPSLatitudeRef", None)
			gps_longitude = exif["GPSInfo"].get("GPSLongitude", None)
			gps_longitude_ref = exif["GPSInfo"].get("GPSLongitudeRef", None)

		if gps_latitude and gps_latitude_ref and gps_longitude and gps_longitude_ref:
			self._attributes["metadata"]["latitude"] = Metadata.convert_to_degrees_decimal(gps_latitude, gps_latitude_ref)
			self._attributes["metadata"]["latitudeMS"] = Metadata.convert_to_degrees_minutes_seconds(gps_latitude, gps_latitude_ref)
			self._attributes["metadata"]["longitude"] = Metadata.convert_to_degrees_decimal(gps_longitude, gps_longitude_ref)
			self._attributes["metadata"]["longitudeMS"] = Metadata.convert_to_degrees_minutes_seconds(gps_longitude, gps_longitude_ref)

		# Overwrite with album.ini values when it has been read from file
		if self.album.album_ini:
			Metadata.set_metadata_from_album_ini(self.name, self._attributes, self.album.album_ini)

		next_level()
		message("extracted", "", 5)
		back_level()
		back_level()



	_photo_metadata.flash_dictionary = {0x0: "No Flash", 0x1: "Fired", 0x5: "Fired, Return not detected", 0x7: "Fired, Return detected",
		0x8: "On, Did not fire", 0x9: "On, Fired", 0xd: "On, Return not detected", 0xf: "On, Return detected", 0x10: "Off, Did not fire",
		0x14: "Off, Did not fire, Return not detected", 0x18: "Auto, Did not fire", 0x19: "Auto, Fired", 0x1d: "Auto, Fired, Return not detected",
		0x1f: "Auto, Fired, Return detected", 0x20: "No flash function", 0x30: "Off, No flash function", 0x41: "Fired, Red-eye reduction",
		0x45: "Fired, Red-eye reduction, Return not detected", 0x47: "Fired, Red-eye reduction, Return detected", 0x49: "On, Red-eye reduction",
		0x4d: "On, Red-eye reduction, Return not detected", 0x4f: "On, Red-eye reduction, Return detected", 0x50: "Off, Red-eye reduction",
		0x58: "Auto, Did not fire, Red-eye reduction", 0x59: "Auto, Fired, Red-eye reduction", 0x5d: "Auto, Fired, Red-eye reduction, Return not detected",
		0x5f: "Auto, Fired, Red-eye reduction, Return detected"}
	_photo_metadata.light_source_dictionary = {0: "Unknown", 1: "Daylight", 2: "Fluorescent", 3: "Tungsten (incandescent light)", 4: "Flash", 9: "Fine weather", 10: "Cloudy weather", 11: "Shade", 12: "Daylight fluorescent (D 5700 - 7100K)", 13: "Day white fluorescent (N 4600 - 5400K)", 14: "Cool white fluorescent (W 3900 - 4500K)", 15: "White fluorescent (WW 3200 - 3700K)", 17: "Standard light A", 18: "Standard light B", 19: "Standard light C", 20: "D55", 21: "D65", 22: "D75", 23: "D50", 24: "ISO studio tungsten"}
	_photo_metadata.metering_list = ["Unknown", "Average", "Center-weighted average", "Spot", "Multi-spot", "Multi-segment", "Partial"]
	_photo_metadata.exposure_list = ["Not Defined", "Manual", "Program AE", "Aperture-priority AE", "Shutter speed priority AE", "Creative (Slow speed)", "Action (High speed)", "Portrait", "Landscape", "Bulb"]
	_photo_metadata.orientation_list = ["Horizontal (normal)", "Mirror horizontal", "Rotate 180", "Mirror vertical", "Mirror horizontal and rotate 270 CW", "Rotate 90 CW", "Mirror horizontal and rotate 90 CW", "Rotate 270 CW"]
	_photo_metadata.sensing_method_list = ["Not defined", "One-chip color area sensor", "Two-chip color area sensor", "Three-chip color area sensor", "Color sequential area sensor", "Trilinear sensor", "Color sequential linear sensor"]
	_photo_metadata.scene_capture_type_list = ["Standard", "Landscape", "Portrait", "Night scene"]
	_photo_metadata.subject_distance_range_list = ["Unknown", "Macro", "Close view", "Distant view"]


	def _video_metadata(self, path, original=True):
		return_code = VideoProbeWrapper().call('-show_format', '-show_streams', '-of', 'json', '-loglevel', '0', path)
		if not return_code:
			next_level()
			message("error probing video, not a video?", path, 5)
			back_level()
			self.is_valid = False
			return
		info = json.loads(return_code.decode(sys.getdefaultencoding()))
		for s in info["streams"]:
			if 'codec_type' in s:
				next_level()
				message("debug: s[codec_type]", s['codec_type'], 5)
				back_level()
			if 'codec_type' in s and s['codec_type'] == 'video':
				self._attributes["mediaType"] = "video"
				self._attributes["metadata"]["size"] = (int(s["width"]), int(s["height"]))
				if "duration" in s:
					self._attributes["metadata"]["duration"] = int(round(float(s["duration"]) * 10) / 10)
				if "tags" in s and "rotate" in s["tags"]:
					self._attributes["metadata"]["rotate"] = s["tags"]["rotate"]
				if original:
					self._attributes["metadata"]["originalSize"] = (int(s["width"]), int(s["height"]))
				break

		# Video should also contain metadata like GPS information, at least in QuickTime and MP4 files...
		if self.album.album_ini:
			Metadata.set_metadata_from_album_ini(self.name, self._attributes, self.album.album_ini)


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
			# https://github.com/paolobenve/myphotoshare/issues/46: some image may raise this exception
			message("WARNING: Photo couldn't be trasposed", photo_path, 2)

		self._photo_thumbnails_cascade(image, photo_path, thumbs_path)


	@staticmethod
	def _thumbnail_is_smaller_than(image, thumb_size, thumb_type="", mobile_bigger=False):
		image_width = image.size[0]
		image_height = image.size[1]
		max_image_size = max(image_width, image_height)
		corrected_thumb_size = int(round(thumb_size * Options.config['mobile_thumbnail_factor'])) if mobile_bigger else thumb_size
		if (
			thumb_type == "fixed_height" and
			image_width > image_height
		):
			verdict = (corrected_thumb_size < image_height)
		elif thumb_type == "square":
			min_image_size = min(image_width, image_height)
			verdict = (corrected_thumb_size < min_image_size)
		else:
			verdict = (corrected_thumb_size < max_image_size)
		return verdict


	def generate_all_thumbnails(self, reduced_size_images, photo_path, thumbs_path):
		global thumbnail_types_and_sizes_list
		if thumbnail_types_and_sizes_list is None:
			thumbnail_types_and_sizes_list = list(thumbnail_types_and_sizes().items())

		for thumb_type, thumb_sizes in thumbnail_types_and_sizes_list:
			thumbs_and_reduced_size_images = reduced_size_images[:]
			for (thumb_size, mobile_bigger) in thumb_sizes:
				index = -1
				last_index = len(thumbs_and_reduced_size_images) - 1
				for thumb_or_reduced_size_image in thumbs_and_reduced_size_images:
					index += 1
					if index == last_index or Media._thumbnail_is_smaller_than(thumb_or_reduced_size_image, thumb_size, thumb_type, mobile_bigger):
						thumb = self.reduce_size_or_make_thumbnail(thumb_or_reduced_size_image, photo_path, thumbs_path, thumb_size, thumb_type, mobile_bigger)
						thumbs_and_reduced_size_images = [thumb] + thumbs_and_reduced_size_images
						break



	def _photo_thumbnails_cascade(self, image, photo_path, thumbs_path):
		# this function calls self.reduce_size_or_make_thumbnail() with the proper image self.reduce_size_or_make_thumbnail() needs
		# so that the thumbnail doesn't get blurred
		reduced_size_image = image
		reduced_size_images = []
		for thumb_size in Options.config['reduced_sizes']:
			reduced_size_image = self.reduce_size_or_make_thumbnail(reduced_size_image, photo_path, thumbs_path, thumb_size)
			reduced_size_images = [reduced_size_image] + reduced_size_images

		self.generate_all_thumbnails(reduced_size_images, photo_path, thumbs_path)


	@staticmethod
	def is_thumbnail(thumb_type):
		_is_thumbnail = (thumb_type != "")
		return _is_thumbnail

	def face_center(self, faces, image_size):
		length = len(faces)
		(x0, y0, w0, h0) = faces[0]
		if length == 1:
			# return the only face
			return (int(x0 + w0 / 2), int(y0 + h0 / 2))
		elif length == 2:
			(x1, y1, w1, h1) = faces[1]
			center0_x = int(x0 + w0 / 2)
			center0_y = int(y0 + h0 / 2)
			center1_x = int(x1 + w1 / 2)
			center1_y = int(y1 + h1 / 2)
			dist_x = max(x0, x1) + (w0 + w1) / 2 - min(x0, x1)
			dist_y = max(y0, y1) + (h0 + h1) / 2 - min(y0, y1)
			if dist_x > image_size or dist_y > image_size:
				# the faces are too far each other, choose one: return the bigger one
				if w1 > w0:
					return (center1_x, center1_y)
				else:
					return (center0_x, center0_y)
			else:
				return (int((center1_x + center0_x) / 2), int((center1_y + center0_y) / 2))
		else:
			dist_x = max([x for (x, y, w, h) in faces]) - min([x for (x, y, w, h) in faces])
			dist_y = max([y for (x, y, w, h) in faces]) - min([y for (x, y, w, h) in faces])
			if dist_x < image_size and dist_y < image_size:
				# all the faces are within the square, get the mean point
				return (int(np.mean([x + w / 2 for (x, y, w, h) in faces])), int(np.mean([y + h / 2 for (x, y, w, h) in faces])))
			else:
				# remove the farther faces and then return the agerage point of the remaining group
				distances = np.empty((length, length))
				positions = np.empty(length, dtype=object)
				max_sum_of_distances = 0
				for k1, f1 in enumerate(faces):
					(x, y, w, h) = f1
					x_pos = x + int(w / 2)
					y_pos = y + int(h / 2)
					positions[k1] = np.array([x_pos, y_pos])
					sum_of_distances = 0
					for k2, f2 in enumerate(faces):
						distances[k1, k2] = math.sqrt((f1[0] - f2[0]) ** 2 + (f1[1] - f2[1]) ** 2)
						sum_of_distances += distances[k1, k2]
					if sum_of_distances > max_sum_of_distances:
						max_sum_of_distances = sum_of_distances
						max_key = k1

				mean_distance = np.mean(distances)
				if max_sum_of_distances / length > 2 * mean_distance:
					# remove the face
					faces.pop(max_key)
					return self.face_center(faces, image_size)
				else:
					return np.mean(np.asarray(positions)).tolist()


	def reduce_size_or_make_thumbnail(self, start_image, original_path, thumbs_path, thumb_size, thumb_type="", mobile_bigger=False):
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
		json_file_exists = os.path.exists(json_file)
		_is_thumbnail = Media.is_thumbnail(thumb_type)
		next_level()
		message("checking reduction/thumbnail", thumb_path, 5)
		if (
			os.path.exists(thumbs_path_with_subdir) and
			os.path.exists(thumb_path) and
			file_mtime(thumb_path) >= self.datetime_file and
			(not json_file_exists or file_mtime(thumb_path) < file_mtime(json_file)) and
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
		message("reduction/thumbnail not OK, creating", "", 5)
		next_level()
		if not os.path.exists(thumbs_path_with_subdir):
			message("unexistent subdir", thumbs_path_with_subdir, 5)
		elif not os.path.exists(thumb_path):
			message("unexistent reduction/thumbnail", thumb_path, 5)
		elif file_mtime(thumb_path) < self.datetime_file:
			message("reduction/thumbnail older than media date time", thumb_path, 5)
		elif not json_file_exists:
			message("unexistent json file", json_file, 5)
		elif file_mtime(thumb_path) > file_mtime(json_file):
			message("reduction/thumbnail newer than json file", thumb_path + ", " + json_file, 5)
		back_level()

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
		must_crop = False
		try_shifting = False
		if thumb_type == "square":
			# image is to be cropped: calculate the cropping values
			# if opencv is installed, crop it, taking into account the faces
			if (
				start_image_width != start_image_height and
				(max(start_image_width, start_image_height) >= actual_thumb_size)
			):
				must_crop = True
				if cv2_installed:
					# if the reduced size images were generated in a previous scanner run, start_image is the original image,
					# and detecting the faces is very very very time consuming, so resize it to an appropriate value before detecting the faces
					smaller_size = int(Options.config['album_thumb_size'] * Options.config['mobile_thumbnail_factor'] * 1.5)
					start_image_copy_for_detecting = start_image.copy()
					width_for_detecting = start_image_width
					height_for_detecting = start_image_height
					if min(start_image_width, start_image_height) > smaller_size:
						longer_size = int(smaller_size / min(start_image_width, start_image_height) * max(start_image_width, start_image_height))
						width_for_detecting = smaller_size if start_image_width < start_image_height else longer_size
						height_for_detecting = longer_size if start_image_width < start_image_height else smaller_size
						sizes_change = "from " + str(start_image_width) + "x" + str(start_image_height) + " to " + str(width_for_detecting) + "x" + str(height_for_detecting)
						message("reducing size for face detection...", sizes_change, 5)
						start_image_copy_for_detecting.thumbnail((longer_size, longer_size), Image.ANTIALIAS)
						next_level()
						message("size reduced", "", 5)
						back_level()

					# opencv!
					# see http://opencv-python-tutroals.readthedocs.io/en/latest/py_tutorials/py_objdetect/py_face_detection/py_face_detection.html#haar-cascade-detection-in-opencv
					try:
						opencv_image = np.array(start_image_copy_for_detecting.convert('RGB'))[:, :, ::-1].copy()
						gray_opencv_image = cv2.cvtColor(opencv_image, cv2.COLOR_BGR2GRAY)
					except cv2.error:
						# this happens with gif's... weird...
						pass
					else:
						try_shifting = True

						# detect faces
						message("opencv: detecting faces...", "from " + str(width_for_detecting) + "x" + str(height_for_detecting), 4)
						# from https://docs.opencv.org/2.4/modules/objdetect/doc/cascade_classification.html:
						# detectMultiScale(image[, scaleFactor[, minNeighbors[, flags[, minSize[, maxSize]]]]])
						# - scaleFactor – Parameter specifying how much the image size is reduced at each image scale.
						# - minNeighbors – Parameter specifying how many neighbors each candidate rectangle should have to retain it.
						# - flags – Parameter with the same meaning for an old cascade as in the function cvHaarDetectObjects. It is not used for a new cascade.
						# - minSize – Minimum possible object size. Objects smaller than that are ignored.
						# - maxSize – Maximum possible object size. Objects larger than that are ignored.
						# You should read the beginning of the page in order to understand the parameters
						faces = face_cascade.detectMultiScale(gray_opencv_image, Options.config['face_cascade_scale_factor'], 5)
						if len(faces) and Options.config['show_faces']:
							img = opencv_image
							for (x, y, w, h) in faces:
								cv2.rectangle(img, (x, y), (x + w, y + h), (255, 0, 0), 2)
								roi_gray = gray_opencv_image[y: y + h, x: x + w]
								roi_color = img[y: y + h, x: x + w]
								eyes = eye_cascade.detectMultiScale(roi_gray)
								for (ex, ey, ew, eh) in eyes:
									cv2.rectangle(roi_color, (ex, ey), (ex + ew, ey + eh), (0, 255, 0), 2)
							cv2.imshow('img', img)
							cv2.waitKey(0)
							cv2.destroyAllWindows()

						# get the position of the center of the faces
						if len(faces):
							next_level()
							message("faces detected", str(len(faces)) + " faces", 4)
							(x_center, y_center) = self.face_center(faces.tolist(), actual_thumb_size)
							next_level()
							message("opencv", "center: " + str(x_center) + ", " + str(y_center), 4)
							back_level()
							back_level()
						else:
							try_shifting = False
							next_level()
							message("no faces detected", "", 4)
							back_level()

				if min(start_image_width, start_image_height) >= actual_thumb_size:
					# image is bigger than the square which will result from cropping
					if start_image_width > start_image_height:
						# wide image
						top = 0
						bottom = start_image_height
						left = int((start_image_width - start_image_height) / 2)
						right = start_image_width - left
						if cv2_installed and try_shifting:
							# maybe the position of the square could be modified so that it includes more faces
							# center on the faces
							shift = int(x_center - start_image_width / 2)
							message("cropping for square", "shifting horizontally by " + str(shift) + " px", 4)
							left += shift
							if left < 0:
								left = 0
								right = start_image_height
							else:
								right += shift
								if right > start_image_width:
									right = start_image_width
									left = start_image_width - start_image_height
					else:
						# tall image
						left = 0
						right = start_image_width
						top = int((start_image_height - start_image_width) / 2)
						bottom = start_image_height - top
						if cv2_installed and try_shifting:
							# maybe the position of the square could be modified so that it includes more faces
							# center on the faces
							shift = int(y_center - start_image_height / 2)
							message("cropping for square", "shifting vertically by " + str(shift) + " px", 4)
							top += shift
							if top < 0:
								top = 0
								bottom = start_image_width
							else:
								bottom += shift
								if bottom > start_image_height:
									bottom = start_image_height
									top = start_image_height - start_image_width
					thumbnail_width = actual_thumb_size
				elif max(start_image_width, start_image_height) >= actual_thumb_size:
					# image smallest size is smaller than the square which would result from cropping
					# cropped image will not be square
					if start_image_width > start_image_height:
						# wide image
						top = 0
						bottom = start_image_height
						left = int((start_image_width - actual_thumb_size) / 2)
						right = left + actual_thumb_size
						if cv2_installed and try_shifting:
							# maybe the position of the crop could be modified so that it includes more faces
							# center on the faces
							shift = int(x_center - start_image_width / 2)
							message("cropping wide image", "shifting horizontally by " + str(shift) + " px", 4)
							left += shift
							if left < 0:
								left = 0
								right = actual_thumb_size
							else:
								right += shift
								if right > start_image_width:
									right = start_image_width
									left = right - actual_thumb_size
						thumbnail_width = actual_thumb_size
					else:
						# tall image
						left = 0
						right = start_image_width
						top = int((start_image_height - actual_thumb_size) / 2)
						bottom = top + actual_thumb_size
						if cv2_installed and try_shifting:
							# maybe the position of the crop could be modified so that it includes more faces
							# center on the faces
							shift = int(y_center - start_image_height / 2)
							message("cropping tall image", "shifting vertically by " + str(shift) + " px", 4)
							top += shift
							if top < 0:
								top = 0
								bottom = actual_thumb_size
							else:
								bottom += shift
								if bottom > start_image_height:
									bottom = start_image_height
									top = bottom - actual_thumb_size
						thumbnail_width = start_image_width
			else:
				# image is square, or is smaller than the square thumbnail, don't crop it
				thumbnail_width = start_image_width
		else:
			if (
				original_thumb_size == media_thumb_size and
				thumb_type == "fixed_height" and
				start_image_width > start_image_height
			):
				# the thumbnail size will not be thumb_size, the image will be greater
				thumbnail_width = int(round(original_thumb_size * start_image_width / float(start_image_height)))
				actual_thumb_size = thumbnail_width
			elif start_image_width > start_image_height:
				thumbnail_width = actual_thumb_size
			else:
				thumbnail_width = int(round(actual_thumb_size * start_image_width / float(start_image_height)))

		# now thumbnail_width and thumbnail_height are the values the thumbnail will get,
		# and if the thumbnail isn't a square one, their ratio is the same of the original image

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

		if max(start_image_copy.size[0], start_image_copy.size[1]) <= actual_thumb_size:
			# no resize
			# resizing to thumbnail size an image smaller than the thumbnail we must produce would return a blurred image
			if not mobile_bigger and original_thumb_size > Options.config['album_thumb_size'] or mobile_bigger and original_thumb_size > int(Options.config['album_thumb_size'] * Options.config['mobile_thumbnail_factor']):
				message("small image, no reduction", info_string, 4)
			elif not mobile_bigger and original_thumb_size == Options.config['album_thumb_size'] or mobile_bigger and original_thumb_size == int(Options.config['album_thumb_size'] * Options.config['mobile_thumbnail_factor']):
				message("small image, no thumbing for album", info_string, 4)
			else:
				message("small image, no thumbing for media", info_string, 4)
		else:
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
				message("size reduced (" + str(original_thumb_size) + ")", "", 4)
			elif not mobile_bigger and original_thumb_size == Options.config['album_thumb_size'] or mobile_bigger and original_thumb_size == int(Options.config['album_thumb_size'] * Options.config['mobile_thumbnail_factor']):
				message("thumbed for albums (" + str(original_thumb_size) + ")", "", 4)
			else:
				message("thumbed for media (" + str(original_thumb_size) + ")", "", 4)
			back_level()

		# if the crop results smaller than the required size, extend it with a background
		start_image_copy_filled = start_image_copy
		if thumb_type == "square" and min(start_image_copy.size[0], start_image_copy.size[1]) < actual_thumb_size:
			# it's smaller than the square we need: fill it
			message("small crop: filling...", "background color: " + Options.config['small_square_crops_background_color'], 5)
			new_image = Image.new('RGBA', (actual_thumb_size, actual_thumb_size), Options.config['small_square_crops_background_color'])
			new_image.paste(start_image_copy, (int((actual_thumb_size - start_image_copy.size[0]) / 2), int((actual_thumb_size - start_image_copy.size[1]) / 2)))
			start_image_copy_filled = new_image
			next_level()
			message("filled", "", 5)
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

		if self.is_video:
			message("adding video transparency...", "", 5)
			start_image_copy_for_saving = start_image_copy_filled.copy()
			transparency_file = os.path.join(os.path.dirname(__file__), "../web/img/play_button_100_62.png")
			video_transparency = Image.open(transparency_file)
			x = int((start_image_copy_filled.size[0] - video_transparency.size[0]) / 2)
			y = int((start_image_copy_filled.size[1] - video_transparency.size[1]) / 2)
			start_image_copy_for_saving.paste(video_transparency, (x, y), video_transparency)
			next_level()
			message("video transparency added", "", 4)
			back_level()
		else:
			start_image_copy_for_saving = start_image_copy_filled

		message("saving...", info_string, 5)
		try:
			jpeg_quality = Options.config['jpeg_quality']
			if thumb_type:
				# use maximum quality for album and media thumbnails
				jpeg_quality = 100
			start_image_copy_for_saving.save(thumb_path, "JPEG", quality=jpeg_quality)
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
		(_, tfn) = tempfile.mkstemp()
		return_code = VideoTranscodeWrapper().call(
			'-i', original_path,    # original file to extract thumbs from
			'-f', 'image2',         # extract image
			'-vsync', '1',          # CRF
			'-vframes', '1',        # extrat 1 single frame
			'-an',                  # disable audio
			'-loglevel', 'quiet',   # don't display anything
			'-y',                   # don't prompt for overwrite
			tfn                     # temporary file to store extracted image
		)
		if not return_code:
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
			message("error opening video thumbnail", tfn + " from " + original_path, 5)
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

		# generate the thumbnails
		self.generate_all_thumbnails([mirror], original_path, thumbs_path)

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
		num_of_cores = os.sysconf('SC_NPROCESSORS_ONLN') - Options.config['respected_processors']
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
			'-threads', str(num_of_cores),				# number of cores (all minus respected_processors)
			'-loglevel', 'quiet',					# don't display anything
			'-y' 							# don't prompt for overwrite
		]
		filters = []
		info_string = "mp4, h264, " + Options.config['video_transcode_bitrate'] + " bit/sec, crf=" + str(Options.config['video_crf'])

		if os.path.exists(transcode_path) and file_mtime(transcode_path) >= self.datetime_file:
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
			return_code = VideoTranscodeWrapper().call(*transcode_cmd)
			if return_code != False:
				next_level()
				message("transcoded", "", 4)
				back_level()
		except KeyboardInterrupt:
			raise

		if not return_code:
			# add another option, try transcoding again
			# done to avoid this error;
			# x264 [error]: baseline profile doesn't support 4:2:2
			next_level()
			message("transcoding failure, trying yuv420p...", "", 3)
			tmp_transcode_cmd.append('-pix_fmt')
			tmp_transcode_cmd.append('yuv420p')
			tmp_transcode_cmd.append(transcode_path)
			try:
				return_code = VideoTranscodeWrapper().call(*tmp_transcode_cmd)
				if return_code != False:
					next_level()
					message("transcoded with yuv420p", "", 2)
					back_level()
			except KeyboardInterrupt:
				raise

			if not return_code:
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

	@property
	def title(self):
		if 'metadata' in self._attributes and 'title' in self._attributes["metadata"]:
			return self._attributes["metadata"]["title"]
		else:
			return ''

	@property
	def description(self):
		if 'metadata' in self._attributes and 'description' in self._attributes["metadata"]:
			return self._attributes["metadata"]["description"]
		else:
			return ''

	@property
	def tags(self):
		if 'metadata' in self._attributes and 'tags' in self._attributes["metadata"]:
			return self._attributes["metadata"]["tags"]
		else:
			return ''

	@property
	def size(self):
		return self._attributes["metadata"]["size"]

	@property
	def is_video(self):
		return "mediaType" in self._attributes["metadata"] and self._attributes["metadata"]["mediaType"] == "video"

	def __str__(self):
		return self.name

	@property
	def path(self):
		return self.media_file_name

	@property
	def image_caches(self):
		global thumbnail_types_and_sizes_list
		if thumbnail_types_and_sizes_list is None:
			thumbnail_types_and_sizes_list = list(thumbnail_types_and_sizes().items())

		caches = []
		album_prefix = remove_folders_marker(self.album.cache_base) + Options.config["cache_folder_separator"]
		if album_prefix == Options.config["cache_folder_separator"]:
			album_prefix = ""
		if self.is_video:
			# transcoded video path
			caches.append(os.path.join(self.album.subdir, album_prefix + video_cache_name(self)))
		else:
			# reduced sizes paths
			for thumb_size in Options.config['reduced_sizes']:
				caches.append(
					os.path.join(
						self.album.subdir,
						album_prefix + photo_cache_name(self, thumb_size)
					)
				)

		# album and media thumbnail path
		for thumb_type, thumb_sizes in thumbnail_types_and_sizes_list:
			for (thumb_size, mobile_bigger) in thumb_sizes:
				caches.append(
					os.path.join(
						self.album.subdir,
						album_prefix +
							photo_cache_name(
											self,
											thumb_size,
											thumb_type,
											mobile_bigger
						)
					)
				)
		return caches

	@property
	def date(self):
		correct_date = None
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
	def has_gps_data(self):
		return "latitude" in self._attributes["metadata"] and "longitude" in self._attributes["metadata"]

	@property
	def has_exif_date(self):
		return "dateTimeOriginal" in self._attributes["metadata"] or "dateTime" in self._attributes["metadata"]

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

	@place_name.setter
	def place_name(self, value):
		self._attributes["geoname"]["place_name"] = value

	@property
	def place_code(self):
		return self._attributes["geoname"]["place_code"]

	@property
	def alt_place_name(self):
		return self._attributes["geoname"]["alt_place_name"]

	@alt_place_name.setter
	def alt_place_name(self, value):
		self._attributes["geoname"]["alt_place_name"] = value

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

	def __lt__(self, other):
		try:
			if self.date < other.date:
				return True
			elif self.date > other.date:
				return False
			else:
				return self.name < other.name
		except TypeError:
			return True

	@property
	def attributes(self):
		return self._attributes


	@staticmethod
	def from_dict(album, dictionary, basepath):
		del dictionary["date"]
		media_path = os.path.join(basepath, dictionary["name"])

		del dictionary["name"]
		for key, value in list(dictionary.items()):
			if key.startswith("dateTime"):
				try:
					dictionary[key] = datetime.strptime(value, Options.date_time_format)
				except KeyboardInterrupt:
					raise
				except ValueError:
					pass
			if key == "metadata":
				for key1, value1 in list(value.items()):
					if key1.startswith("dateTime"):
						try:
							dictionary[key][key1] = datetime.strptime(value1, Options.date_time_format)
						except KeyboardInterrupt:
							raise
						except ValueError:
							pass
		return Media(album, media_path, None, dictionary)


	def to_dict(self):
		folders_album = Options.config['folders_string']
		if self.folders:
			folders_album = os.path.join(folders_album, self.folders)

		media = self.attributes
		media["name"] = self.name
		media["cacheBase"] = self.cache_base
		media["date"] = self.date
		# media["yearAlbum"] = self.year_album_path
		# media["monthAlbum"] = self.month_album_path
		media["dayAlbum"] = self.day_album_path
		media["dayAlbumCacheBase"] = self.day_album_cache_base
		if self.gps_album_path:
			media["gpsAlbum"] = self.gps_album_path
			media["gpsAlbumCacheBase"] = self.gps_album_cache_base
		media["words"] = self.words
		if Options.config['checksum']:
			media["checksum"] = checksum(os.path.join(Options.config['album_path'], self.media_file_name))

		# the following data don't belong properly to media, but to album, but they must be put here in order to work with dates structure
		media["albumName"] = self.album_path
		media["folders_album"] = folders_album
		media["foldersCacheBase"] = self.album.cache_base
		media["cacheSubdir"] = self.album.subdir
		return media


class PhotoAlbumEncoder(json.JSONEncoder):
	def default(self, obj):
		if isinstance(obj, datetime):
			return obj.strftime("%Y-%m-%d %H:%M:%S")
		if isinstance(obj, Album) or isinstance(obj, Media):
			return obj.to_dict()
		return json.JSONEncoder.default(self, obj)


class Metadata(object):
	@staticmethod
	def set_metadata_from_album_ini(name, attributes, album_ini):
		"""
		Set the 'attributes' dictionnary for album or media named 'name'
		with the metadata values from the ConfigParser 'album_ini'.

		The metadata than can be overloaded by values in 'album.ini' file are:
			* title: the caption of the album or media
			* description: a long description whose words can be searched.
			* date: a YYYY-MM-DD date replacing the one from EXIF
			* latitude: for when the media is not geotagged
			* longitude: for when the media is not geotagged
			* tags: a ',' separated list of terms
		"""

		# Initialize with album.ini defaults
		next_level()
		message("initialize album.ini metadata values", "", 5)

		# With Python2, section names are string. As we retrieve file names as unicode,
		# we can't find them in the ConfigParser dictionary
		# @python2
		if sys.version_info < (3,):
			name = str(name)

		# Title
		if album_ini.has_section(name):
			try:
				attributes["metadata"]["title"] = album_ini.get(name, "title")
			except NoOptionError:
				pass
		elif "title" in album_ini.defaults():
			attributes["metadata"]["title"] = album_ini.defaults()["title"]

		# Description
		if album_ini.has_section(name):
			try:
				attributes["metadata"]["description"] = album_ini.get(name, "description")
			except NoOptionError:
				pass
		elif "description" in album_ini.defaults():
			attributes["metadata"]["description"] = album_ini.defaults()["description"]

		# Date
		if album_ini.has_section(name):
			try:
				attributes["metadata"]["dateTime"] = datetime.strptime(album_ini.get(name, "date"), "%Y-%m-%d")
			except ValueError:
				message("ERROR", "Incorrect date in [" + name + "] in 'album.ini'", 1)
			except NoOptionError:
				pass
		elif "date" in album_ini.defaults():
			try:
				attributes["metadata"]["dateTime"] = datetime.strptime(album_ini.defaults()["date"], "%Y-%m-%d")
			except ValueError:
				message("ERROR", "Incorrect date in [DEFAULT] in 'album.ini'", 1)

		# Latitude and longitude
		gps_latitude = None
		gps_latitude_ref = None
		gps_longitude = None
		gps_longitude_ref = None
		if album_ini.has_section(name):
			try:
				gps_latitude = Metadata.create_gps_struct(abs(album_ini.getfloat(name, "latitude")))
				gps_latitude_ref = "N" if album_ini.getfloat(name, "latitude") > 0.0 else "S"
			except ValueError:
				message("ERROR", "Incorrect latitude in [" + name + "] in 'album.ini'", 1)
			except NoOptionError:
				pass
		elif "latitude" in album_ini.defaults():
			try:
				gps_latitude = Metadata.create_gps_struct(abs(float(album_ini.defaults()["latitude"])))
				gps_latitude_ref = "N" if float(album_ini.defaults()["latitude"]) > 0.0 else "S"
			except ValueError:
				message("ERROR", "Incorrect latitude in [" + name + "] in 'album.ini'", 1)
		if album_ini.has_section(name):
			try:
				gps_longitude = Metadata.create_gps_struct(abs(album_ini.getfloat(name, "longitude")))
				gps_longitude_ref = "E" if album_ini.getfloat(name, "longitude") > 0.0 else "W"
			except ValueError:
				message("ERROR", "Incorrect longitude in [" + name + "] in 'album.ini'", 1)
			except NoOptionError:
				pass
		elif "longitude" in album_ini.defaults():
			try:
				gps_longitude = Metadata.create_gps_struct(abs(float(album_ini.defaults()["longitude"])))
				gps_longitude_ref = "E" if float(album_ini.defaults()["longitude"]) > 0.0 else "W"
			except ValueError:
				message("ERROR", "Incorrect longitude in [" + name + "] in 'album.ini'", 1)

		if gps_latitude and gps_latitude_ref and gps_longitude and gps_longitude_ref:
			attributes["metadata"]["latitude"] = Metadata.convert_to_degrees_decimal(gps_latitude, gps_latitude_ref)
			attributes["metadata"]["latitudeMS"] = Metadata.convert_to_degrees_minutes_seconds(gps_latitude, gps_latitude_ref)
			attributes["metadata"]["longitude"] = Metadata.convert_to_degrees_decimal(gps_longitude, gps_longitude_ref)
			attributes["metadata"]["longitudeMS"] = Metadata.convert_to_degrees_minutes_seconds(gps_longitude, gps_longitude_ref)

		# Tags
		if album_ini.has_section(name):
			try:
				attributes["metadata"]["tags"] = [tag.strip() for tag in album_ini.get(name, "tags").split(",")]
			except NoOptionError:
				pass
		elif "tags" in album_ini.defaults():
			attributes["metadata"]["tags"] = [tag.strip() for tag in album_ini.defaults()["tags"].split(",")]

		back_level()


	@staticmethod
	def set_geoname_from_album_ini(name, attributes, album_ini):
		"""
		Set the 'attributes' dictionnary for album or media named 'name'
		with the geoname values from the ConfigParser 'album_ini'.

		The geoname values that can be set from album.ini are:
			* country_name: The name of the country
			* region_name: The name of the region
			* place_name: The name of the nearest place (town or city) calculated
			from latitude/longitude getotag.
		The geonames values that are not visible to the user, like 'country_code'
		can't be changed. We only overwrite the visible values displayed to the user.

		The geonames values must be overwrittent *after* the 'metadata' values
		because the geonames are retrieved from _attributes['metadata']['latitude'] and
		_attributes['metadata']['longitude']. You can use Media.has_gps_data to
		determine if you can call this procedure.
		"""
		# Country_name
		if album_ini.has_section(name):
			try:
				attributes["geoname"]["country_name"] = album_ini.get(name, "country_name")
			except NoOptionError:
				pass
		elif "country_name" in album_ini.defaults():
			attributes["geoname"]["country_name"] = album_ini.defaults()["country_name"]

		# Region_name
		if album_ini.has_section(name):
			try:
				attributes["geoname"]["region_name"] = album_ini.get(name, "region_name")
			except NoOptionError:
				pass
		elif "region_name" in album_ini.defaults():
			attributes["geoname"]["region_name"] = album_ini.defaults()["region_name"]

		# Place_name
		if album_ini.has_section(name):
			try:
				attributes["geoname"]["place_name"] = album_ini.get(name, "place_name")
			except NoOptionError:
				pass
		elif "place_name" in album_ini.defaults():
			attributes["geoname"]["place_name"] = album_ini.defaults()["place_name"]


	@staticmethod
	def create_gps_struct(value):
		"""
		Helper function to create the data structure returned by the EXIF GPS info
		from the decimal value entered by the user in a 'album.ini' metadata file.
		Longitude and latitude metadata are stored as rationals.
			GPS = ( (deg1, deg2),
					(min1, min2),
					(sec1, sec2) )
		"""
		frac, deg = math.modf(value)
		frac, min = math.modf(frac * 60.0)
		frac, sec = math.modf(frac * 60.0)
		return ((int(deg), 1), (int(min), 1), (int(sec), 1))


	@staticmethod
	def convert_to_degrees_minutes_seconds(value, ref):
		"""
		Helper function to convert the GPS coordinates stored in the EXIF to degrees, minutes and seconds.
		"""

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

		result = str(d) + "º " + str(m) + "' " + str(s) + '" ' + ref

		return result

	@staticmethod
	def convert_to_degrees_decimal(value, ref):
		"""
		Helper function to convert the GPS coordinates stored in the EXIF to degrees in float format.
		"""

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
