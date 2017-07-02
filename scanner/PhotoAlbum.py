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

def make_photo_thumbs(self, image, original_path, thumbs_path, thumb_size, square):
	# The pool methods use a queue.Queue to pass tasks to the worker processes.
	# Everything that goes through the queue.Queue must be pickable, and since
	# self._photo_thumbnail is not defined at the top level, it's not pickable.
	# This is why we have this "dummy" function, so that it's pickable.
	try:
		self._photo_thumbnail(image, original_path, thumbs_path, thumb_size, square)
	except KeyboardInterrupt:
		raise

class Album(object):
	def __init__(self, path):
		self._path = trim_base(path)
		self._photos = list()
		self._albums = list()
		self._photos_sorted = True
		self._albums_sorted = True
	@property
	def photos(self):
		return self._photos
	@property
	def albums(self):
		return self._albums
	@property
	def path(self):
		return self._path
	def __str__(self):
		return self.path
	@property
	def json_file(self):
		return json_name(self.path)
	@property
	def date(self):
		self._sort()
		if len(self._photos) == 0 and len(self._albums) == 0:
			return datetime(1900, 1, 1)
		elif len(self._photos) == 0:
			return self._albums[-1].date
		elif len(self._albums) == 0:
			return self._photos[-1].date
		return max(self._photos[-1].date, self._albums[-1].date)
	def __cmp__(self, other):
		try:
			return cmp(self.date, other.date)
		except TypeError:
			return 1
	def add_photo(self, photo):
		self._photos.append(photo)
		self._photos_sorted = False
	def add_album(self, album):
		self._albums.append(album)
		self._albums_sorted = False
	def _sort(self):
		if not self._photos_sorted:
			self._photos.sort()
			self._photos_sorted = True
		if not self._albums_sorted:
			self._albums.sort()
			self._albums_sorted = True
	@property
	def empty(self):
		if len(self._photos) != 0:
			return False
		if len(self._albums) == 0:
			return True
		for album in self._albums:
			if not album.empty:
				return False
		return True
		
	def cache(self, base_dir):
		self._sort()
		fp = open(os.path.join(base_dir, self.json_file), 'w')
		json.dump(self, fp, cls=PhotoAlbumEncoder)
		fp.close()
	@staticmethod
	def from_cache(path):
		fp = open(path, "r")
		dictionary = json.load(fp)
		fp.close()
		return Album.from_dict(dictionary)
	@staticmethod
	def from_dict(dictionary, cripple=True):
		album = Album(dictionary["path"])
		for photo in dictionary["photos"]:
			album.add_photo(Media.from_dict(photo, untrim_base(album.path)))
		if not cripple:
			for subalbum in dictionary["albums"]:
				album.add_album(Album.from_dict(subalbum), cripple)
		album._sort()
		return album
	def remove_marker(self, path):
		marker_position = path.find(Options.config['folders_string'])
		if marker_position == 0:
			path = path[len(Options.config['folders_string']):]
			if len(path) > 0:
				path = path[1:]
		return path
	def to_dict(self, cripple=True):
		self._sort()
		subalbums = []
		if cripple:
			for sub in self._albums:
				if not sub.empty:
					subalbums.append({ "path": trim_base_custom(sub.path, self._path), "date": sub.date })
		else:
			for sub in self._albums:
				if not sub.empty:
					subalbums.append(sub)
		path_without_marker = self.remove_marker(self.path)
		if path_without_marker == self.path:
			dictionary = {
				"path": self.path,
				"date": self.date,
				"albums": subalbums,
				"photos": self._photos,
				"cacheBase": cache_base(self.path)
				}
		else:
			dictionary = {
				"path": self.path,
				"physicalPath": path_without_marker,
				"date": self.date,
				"albums": subalbums,
				"photos": self._photos,
				"cacheBase": cache_base(self.path)
				}
		
		return dictionary
	def photo_from_path(self, path):
		for photo in self._photos:
			if trim_base(path) == photo._path:
				return photo
		return None

class Media(object):
	def __init__(self, media_path, thumbs_path=None, attributes=None):
		self.media_file_name = trim_base(media_path)
		self.folders = trim_base(os.path.dirname(self.media_file_name))
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
			self._attributes = attributes
			return
		self._attributes = {}
		self._attributes["dateTimeFile"] = mtime
		self._attributes["mediaType"] = "photo"
		
		try:
			image = Image.open(media_path)
		except KeyboardInterrupt:
			raise
		except:
			self._video_metadata(media_path)
		
		if isinstance(image, Image.Image):
			self._photo_metadata(image)
			try:
				self._photo_thumbnails(image, media_path, thumbs_path)
			except KeyboardInterrupt:
				raise
		elif self._attributes["mediaType"] == "video":
			self._video_thumbnails(thumbs_path, media_path)
			self._video_transcode(thumbs_path, media_path)
		else:
			self.is_valid = False
			return
		
	def _photo_metadata(self, image):
		self._attributes["size"] = image.size
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
				if (isinstance(decoded, str) or isinstance(decoded, unicode)) and decoded.startswith("DateTime"):
					try:
						value = datetime.strptime(value, '%Y:%m:%d %H:%M:%S')
					except KeyboardInterrupt:
						raise
					except:
						continue
			exif[decoded] = value
		
		if "Orientation" in exif:
			self._orientation = exif["Orientation"];
			if self._orientation in range(5, 9):
				self._attributes["size"] = (self._attributes["size"][1], self._attributes["size"][0])
			if self._orientation - 1 < len(self._photo_metadata.orientation_list):
				self._attributes["orientation"] = self._photo_metadata.orientation_list[self._orientation - 1]
		if "Make" in exif:
			self._attributes["make"] = exif["Make"]
		if "Model" in exif:
			self._attributes["model"] = exif["Model"]
		if "ApertureValue" in exif:
			self._attributes["aperture"] = exif["ApertureValue"]
		elif "FNumber" in exif:
			self._attributes["aperture"] = exif["FNumber"]
		if "FocalLength" in exif:
			self._attributes["focalLength"] = exif["FocalLength"]
		if "ISOSpeedRatings" in exif:
			self._attributes["iso"] = exif["ISOSpeedRatings"]
		if "ISO" in exif:
			self._attributes["iso"] = exif["ISO"]
		if "PhotographicSensitivity" in exif:
			self._attributes["iso"] = exif["PhotographicSensitivity"]
		if "ExposureTime" in exif:
			self._attributes["exposureTime"] = exif["ExposureTime"]
		if "Flash" in exif and exif["Flash"] in self._photo_metadata.flash_dictionary:
			try:
				self._attributes["flash"] = self._photo_metadata.flash_dictionary[exif["Flash"]]
			except KeyboardInterrupt:
				raise
			except:
				pass
		if "LightSource" in exif and exif["LightSource"] in self._photo_metadata.light_source_dictionary:
			try:
				self._attributes["lightSource"] = self._photo_metadata.light_source_dictionary[exif["LightSource"]]
			except KeyboardInterrupt:
				raise
			except:
				pass
		if "ExposureProgram" in exif and exif["ExposureProgram"] < len(self._photo_metadata.exposure_list):
			self._attributes["exposureProgram"] = self._photo_metadata.exposure_list[exif["ExposureProgram"]]
		if "SpectralSensitivity" in exif:
			self._attributes["spectralSensitivity"] = exif["SpectralSensitivity"]
		if "MeteringMode" in exif and exif["MeteringMode"] < len(self._photo_metadata.metering_list):
			self._attributes["meteringMode"] = self._photo_metadata.metering_list[exif["MeteringMode"]]
		if "SensingMethod" in exif and exif["SensingMethod"] < len(self._photo_metadata.sensing_method_list):
			self._attributes["sensingMethod"] = self._photo_metadata.sensing_method_list[exif["SensingMethod"]]
		if "SceneCaptureType" in exif and exif["SceneCaptureType"] < len(self._photo_metadata.scene_capture_type_list):
			self._attributes["sceneCaptureType"] = self._photo_metadata.scene_capture_type_list[exif["SceneCaptureType"]]
		if "SubjectDistanceRange" in exif and exif["SubjectDistanceRange"] < len(self._photo_metadata.subject_distance_range_list):
			self._attributes["subjectDistanceRange"] = self._photo_metadata.subject_distance_range_list[exif["SubjectDistanceRange"]]
		if "ExposureCompensation" in exif:
			self._attributes["exposureCompensation"] = exif["ExposureCompensation"]
		if "ExposureBiasValue" in exif:
			self._attributes["exposureCompensation"] = exif["ExposureBiasValue"]
		if "DateTimeOriginal" in exif:
			try:
				self._attributes["dateTimeOriginal"] = datetime.strptime(exif["DateTimeOriginal"], '%Y:%m:%d %H:%M:%S')
			except KeyboardInterrupt:
				raise
			except TypeError:
				self._attributes["dateTimeOriginal"] = exif["DateTimeOriginal"]
		if "DateTime" in exif:
			try:
				self._attributes["dateTime"] = datetime.strptime(exif["DateTime"], '%Y:%m:%d %H:%M:%S')
			except KeyboardInterrupt:
				raise
			except TypeError:
				self._attributes["dateTime"] = exif["DateTime"]

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
			#~ message("debug: codec_type", 'codec_type')
			#~ if 'codec_type' in s:
				#~ message("debug: s[codec_type]", s['codec_type'])
			if 'codec_type' in s and s['codec_type'] == 'video':
				self._attributes["mediaType"] = "video"
				self._attributes["size"] = (int(s["width"]), int(s["height"]))
				if "duration" in s:
					self._attributes["duration"] = s["duration"]
				if "tags" in s and "rotate" in s["tags"]:
					self._attributes["rotate"] = s["tags"]["rotate"]
				if original:
					self._attributes["originalSize"] = (int(s["width"]), int(s["height"]))
				break
	
	
	def _photo_thumbnail(self, image, original_path, thumbs_path, thumbnail_size, square=False):
		#~ try:
			#~ image = Image.open(original_path)
		#~ except KeyboardInterrupt:
			#~ raise
		#~ except:
			#~ self.is_valid = False
			#~ return
		
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
		self._thumbnail(image, original_path, thumbs_path, thumbnail_size, square)

	def _thumbnail(self, image, original_path, thumbs_path, thumbnail_size, square):
		#~ message("video", path_with_subdir(self.media_file_name, thumbnail_size, square))
		thumb_path = os.path.join(thumbs_path, path_with_subdir(self.media_file_name, thumbnail_size, square))
		info_string = str(thumbnail_size)
		next_level()
		if square:
			info_string += ", square"
		if (
			os.path.exists(thumb_path) and
			file_mtime(thumb_path) >= self._attributes["dateTimeFile"] and
			not Options.config['recreate_photo_thumbnails']
		):
			message("existing thumb", info_string)
			back_level()
			return image
		gc.collect()
		try:
			image_copy = image.copy()
		except KeyboardInterrupt:
			raise
		except:
			try:
				image_copy = image.copy() # we try again to work around PIL bug
			except KeyboardInterrupt:
				raise
			except:
				message("corrupt image", os.path.basename(original_path))
				self.is_valid = False
				back_level()
				return image
		if square:
			if image_copy.size[0] > image_copy.size[1]:
				left = (image_copy.size[0] - image_copy.size[1]) / 2
				top = 0
				right = image_copy.size[0] - ((image_copy.size[0] - image_copy.size[1]) / 2)
				bottom = image_copy.size[1]
			else:
				left = 0
				top = (image_copy.size[1] - image_copy.size[0]) / 2
				right = image_copy.size[0]
				bottom = image_copy.size[1] - ((image_copy.size[1] - image_copy.size[0]) / 2)
			image_copy = image_copy.crop((left, top, right, bottom))
			gc.collect()
		image_size = max(image_copy.size[0], image_copy.size[1])
		if (image_size >= thumbnail_size):
			image_copy.thumbnail((thumbnail_size, thumbnail_size), Image.ANTIALIAS)
		else:
			image_copy = self.resize_canvas(image_copy, thumbnail_size)
		try:
			image_copy.save(thumb_path, "JPEG", quality=Options.config['jpeg_quality'])
			next_level(1)
			message("thumbing", info_string)
			back_level(1)
			back_level()
			return image_copy
		except KeyboardInterrupt:
			try:
				os.unlink(thumb_path)
			except:
				pass
			raise
		except IOError:
			image_copy.convert('RGB').save(thumb_path, "JPEG", quality=Options.config['jpeg_quality'])
			next_level(1)
			message(str(thumbnail_size) + " thumbnail", "OK (bug workaround)", 1)
			back_level(1)
			back_level()
			return image_copy
		except:
			next_level()
			message(str(thumbnail_size) + " thumbnail", "save failure to " + os.path.basename(thumb_path) + ", _thumbnail() returns original image")
			back_level()
			try:
				os.unlink(thumb_path)
			except:
				pass
			back_level()
			return image
	def resize_canvas(self, image, canvas_max_size):
		old_width, old_height = image.size
		if (old_width > old_height):
			canvas_width = canvas_max_size
			canvas_height = int(float(canvas_width) / float(old_width) * float(old_height))
		else:
			canvas_height = canvas_max_size
			canvas_width = int(float(canvas_height) / float(old_height) * float(old_width))
		
		# Center the image
		x1 = int(math.floor((canvas_width - old_width) / 2))
		y1 = int(math.floor((canvas_height - old_height) / 2))
		mode = image.mode
		#~ if len(mode) == 1:  # L, 1
			#~ new_background = (34)
		#~ if len(mode) == 3:  # RGB
			#~ new_background = (34, 34, 34)
		#~ if len(mode) == 4:  # RGBA, CMYK
			#~ new_background = (34, 34, 34, 1)
		new_background = Options.config['background_color']
		newImage = Image.new(mode, (canvas_width, canvas_height), new_background)
		newImage.paste(image, (x1, y1, x1 + old_width, y1 + old_height))
		return newImage
	def _photo_thumbnails_parallel(self, image, photo_path, thumbs_path):
		try:
			# get number of cores on the system, and use all minus one
			num_of_cores = os.sysconf('SC_NPROCESSORS_ONLN') - 1
			pool = Pool(processes=num_of_cores)
			try:
				for thumb_size in Options.config['reduced_sizes']:
					if (Options.config['thumbnail_generation_mode'] == "mixed" and thumb_size == Options.config['reduced_sizes'][0]):
						continue
					try:
						pool.apply_async(make_photo_thumbs, args = (self, image, photo_path, thumbs_path, thumb_size, False))
					except KeyboardInterrupt:
						raise
				for thumb_size in Options.config['thumb_sizes']:
					try:
						pool.apply_async(make_photo_thumbs, args = (self, image, photo_path, thumbs_path, thumb_size, True))
					except KeyboardInterrupt:
						raise
			except KeyboardInterrupt:
				raise
			except:
				pool.terminate()
			pool.close()
			pool.join()
		except KeyboardInterrupt:
			raise
	def _photo_thumbnails_mixed(self, image, photo_path, thumbs_path):
		thumb = image
		try:
			thumb_size = Options.config['reduced_sizes'][0]
			try:
				if (max(image.size[0], image.size[1]) < thumb_size):
					image_to_start_from = image
				else:
					image_to_start_from = thumb
				thumb = self._thumbnail(image_to_start_from, photo_path, thumbs_path, thumb_size, False)
				self._photo_thumbnails_parallel(thumb, photo_path, thumbs_path)
			except KeyboardInterrupt:
				raise
		except KeyboardInterrupt:
			raise
	def _photo_thumbnails_cascade(self, image, photo_path, thumbs_path):
		thumb = image
		try:
			for thumb_size in Options.config['reduced_sizes']:
				try:
					if (max(image.size[0], image.size[1]) < thumb_size):
						image_to_start_from = image
					else:
						image_to_start_from = thumb
					thumb = self._thumbnail(image_to_start_from, photo_path, thumbs_path, thumb_size, False)
				except KeyboardInterrupt:
					raise
			for thumb_size in Options.config['thumb_sizes']:
				try:
					image_to_start_from = thumb
					thumb = self._thumbnail(image_to_start_from, photo_path, thumbs_path, thumb_size, True)
				except KeyboardInterrupt:
					raise
		except KeyboardInterrupt:
			raise
	def _photo_thumbnails(self, image, photo_path, thumbs_path):
		if (Options.config['thumbnail_generation_mode'] == "parallel"):
			self._photo_thumbnails_parallel(image, photo_path, thumbs_path)
		elif (Options.config['thumbnail_generation_mode'] == "mixed"):
			self._photo_thumbnails_mixed(image, photo_path, thumbs_path)
		elif (Options.config['thumbnail_generation_mode'] == "cascade"):
			self._photo_thumbnails_cascade(image, photo_path, thumbs_path)
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
			message("couldn't extract video frame", os.path.basename(original_path))
			back_level()
			try:
				os.unlink(tfn)
			except:
				pass
			self.is_valid = False
			return
		try:
			image = Image.open(tfn)
		except KeyboardInterrupt:
			try:
				os.unlink(tfn)
			except:
				pass
			raise
		except:
			next_level()
			message("couldn't open video thumbnail", tfn)
			back_level()
			try:
				os.unlink(tfn)
			except:
				pass
			self.is_valid = False
			return
		mirror = image
		if "rotate" in self._attributes:
			if self._attributes["rotate"] == "90":
				mirror = image.transpose(Image.ROTATE_270)
			elif self._attributes["rotate"] == "180":
				mirror = image.transpose(Image.ROTATE_180)
			elif self._attributes["rotate"] == "270":
				mirror = image.transpose(Image.ROTATE_90)
		for thumb_size in Options.config['thumb_sizes']:
			self._thumbnail(mirror, original_path, thumbs_path, thumb_size, True)
		try:
			os.unlink(tfn)
		except:
			pass

	def _video_transcode(self, transcode_path, original_path):
		transcode_path = os.path.join(transcode_path, video_cache_with_subdir(self.media_file_name))
		# get number of cores on the system, and use all minus one
		num_of_cores = os.sysconf('SC_NPROCESSORS_ONLN') - 1
		transcode_cmd = [
			'-i', original_path,					# original file to be encoded
			'-c:v', 'libx264',					# set h264 as videocodec
			'-preset', 'slow',					# set specific preset that provides a certain encoding speed to compression ratio
			'-profile:v', 'baseline',				# set output to specific h264 profile
			'-level', '3.0',					# sets highest compatibility with target devices
			'-crf', '20',						# set quality
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
		info_string = "%s -> mp4, h264" % (os.path.basename(original_path))
		next_level()
		message("transcoding", info_string)
		back_level()
		if (
			os.path.exists(transcode_path) and
			file_mtime(transcode_path) >= self._attributes["dateTimeFile"] and
			not Options.config['retranscode_videos']
		):
			self._video_metadata(transcode_path, False)
			return
		if "originalSize" in self._attributes and self._attributes["originalSize"][1] > 720:
			transcode_cmd.append('-s')
			transcode_cmd.append('hd720')
		if "rotate" in self._attributes:
			if self._attributes["rotate"] == "90":
				filters.append('transpose=1')
			elif self._attributes["rotate"] == "180":
				filters.append('vflip,hflip')
			elif self._attributes["rotate"] == "270":
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
			message("transcoding failure, trying yuv420p", os.path.basename(original_path))
			back_level()
			tmp_transcode_cmd.append('-pix_fmt')
			tmp_transcode_cmd.append('yuv420p')
			tmp_transcode_cmd.append(transcode_path)
			p = VideoTranscodeWrapper().call(*tmp_transcode_cmd)
		
		if p == False:
			next_level()
			message("transcoding failure", os.path.basename(original_path))
			back_level()
			try:
				os.unlink(transcode_path)
			except:
				pass
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
		if "mediaType" in self._attributes and self._attributes["mediaType"] == "video":
			for thumb_size in Options.config['thumb_sizes']:
				caches.append(path_with_subdir(self.media_file_name, thumb_size, True))
			caches.append(video_cache_with_subdir(self.media_file_name))
		else:
			caches = []
			for thumb_size in Options.config['reduced_sizes']:
				caches.append(path_with_subdir(self.media_file_name, thumb_size, False))
			for thumb_size in Options.config['thumb_sizes']:
				caches.append(path_with_subdir(self.media_file_name, thumb_size, True))
		return caches
	@property
	def date(self):
		correct_date = None;
		if not self.is_valid:
			correct_date = datetime(1900, 1, 1)
		if "dateTimeOriginal" in self._attributes:
			correct_date = self._attributes["dateTimeOriginal"]
		elif "dateTime" in self._attributes:
			correct_date = self._attributes["dateTime"]
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
		#~ bydateString = "_by_date"
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
	def from_dict(dictionary, basepath):
		del dictionary["date"]
		path = os.path.join(basepath, dictionary["name"])
		del dictionary["name"]
		for key, value in dictionary.items():
			if key.startswith("dateTime"):
				try:
					#~ dictionary[key] = datetime.strptime(dictionary[key], "%a %b %d %T %Y")
					dictionary[key] = datetime.strptime(dictionary[key], "%c")
				except KeyboardInterrupt:
					raise
				except:
					pass
		return Media(path, None, dictionary)
	def to_dict(self):
		#photo = { "name": self.name, "albumName": self.album_path, "completeName": self.media_file_name, "date": self.date }
		foldersAlbum = Options.config['folders_string']
		if (self.folders):
			foldersAlbum = os.path.join(foldersAlbum, self.folders)
		photo = {
				"name": self.name,
				"albumName": self.album_path,
				"yearAlbum": self.year_album_path,
				"monthAlbum": self.month_album_path,
				"dayAlbum": self.day_album_path,
				"byDateName": os.path.join(self.day_album_path, self.name),
				"foldersAlbum": foldersAlbum,
				"completeName": os.path.join(Options.config['folders_string'], self.media_file_name),
				"date": self.date,
				"cacheSubdir": cache_subdir(self.media_file_name),
				"cacheBase": cache_base(self.name)
			}
		photo.update(self.attributes)
		return photo

class PhotoAlbumEncoder(json.JSONEncoder):
	def default(self, obj):
		if isinstance(obj, datetime):
			#~ return obj.strftime("%a %b %d %H:%M:%S %Y")
			return obj.strftime("%c")
		if isinstance(obj, Album) or isinstance(obj, Media):
			return obj.to_dict()
		return json.JSONEncoder.default(self, obj)

