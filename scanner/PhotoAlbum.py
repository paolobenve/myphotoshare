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

def make_photo_thumbs(self, original_path, thumb_path, size):
	# The pool methods use a queue.Queue to pass tasks to the worker processes.
	# Everything that goes through the queue.Queue must be pickable, and since 
	# self._photo_thumbnail is not defined at the top level, it's not pickable.
	# This is why we have this "dummy" function, so that it's pickable.
	self._photo_thumbnail(original_path, thumb_path, size[0], size[1])

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
	def cache_path(self):
		return json_cache(self.path)
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
		return cmp(self.date, other.date)
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
		fp = open(os.path.join(base_dir, self.cache_path), 'w')
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
			album.add_photo(Photo.from_dict(photo, untrim_base(album.path)))
		if not cripple:
			for subalbum in dictionary["albums"]:
				album.add_album(Album.from_dict(subalbum), cripple)
		album._sort()
		return album
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
		return { "path": self.path, "date": self.date, "albums": subalbums, "photos": self._photos }
	def photo_from_path(self, path):
		for photo in self._photos:
			if trim_base(path) == photo._path:
				return photo
		return None

class Photo(object):
	thumb_sizes = [ (75, True), (150, True), (640, False), (1024, False), (1600, False) ]
	def __init__(self, path, thumb_path=None, attributes=None):
		self._path = trim_base(path)
		self.is_valid = True
		image = None
		try:
			mtime = file_mtime(path)
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
			image = Image.open(path)
		except KeyboardInterrupt:
			raise
		except:
			self._video_metadata(path)

		if isinstance(image, Image.Image):
			self._photo_metadata(image)
			self._photo_thumbnails(path, thumb_path)
		elif self._attributes["mediaType"] == "video":
			self._video_thumbnails(thumb_path, path)
			self._video_transcode(thumb_path, path)
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
	
        	
        def _photo_thumbnail(self, original_path, thumb_path, size, square=False):
	        try:
			image = Image.open(original_path)
		except KeyboardInterrupt:
			raise
		except:
			self.is_valid = False
			return
		
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
                self._thumbnail(image, original_path, thumb_path, size, square)

        def _thumbnail(self, image, original_path, thumb_path, size, square):
		thumb_path = os.path.join(thumb_path, image_cache(self._path, size, square))
		info_string = "%s -> %spx" % (os.path.basename(original_path), str(size))
		if square:
			info_string += ", square"
		message("thumbing", info_string)
		if os.path.exists(thumb_path) and file_mtime(thumb_path) >= self._attributes["dateTimeFile"]:
			return
		gc.collect()
		try:
			image = image.copy()
		except KeyboardInterrupt:
			raise
		except:
			try:
				image = image.copy() # we try again to work around PIL bug
			except KeyboardInterrupt:
				raise
			except:
				message("corrupt image", os.path.basename(original_path))
				self.is_valid = False
				return
		if square:
			if image.size[0] > image.size[1]:
				left = (image.size[0] - image.size[1]) / 2
				top = 0
				right = image.size[0] - ((image.size[0] - image.size[1]) / 2)
				bottom = image.size[1]
			else:
				left = 0
				top = (image.size[1] - image.size[0]) / 2
				right = image.size[0]
				bottom = image.size[1] - ((image.size[1] - image.size[0]) / 2)
			image = image.crop((left, top, right, bottom))
			gc.collect()
		image.thumbnail((size, size), Image.ANTIALIAS)
		try:
			image.save(thumb_path, "JPEG", quality=88)
		except KeyboardInterrupt:
			try:
				os.unlink(thumb_path)
			except:
				pass
			raise
		except:
			message("save failure", os.path.basename(thumb_path))
			try:
				os.unlink(thumb_path)
			except:
				pass
                                
        def _photo_thumbnails(self, original_path, thumb_path):
                # get number of cores on the system, and use all minus one
                num_of_cores = os.sysconf('SC_NPROCESSORS_ONLN') - 1
                pool = Pool(processes=num_of_cores)
                
                try:
                        for size in Photo.thumb_sizes:
                	        pool.apply_async(make_photo_thumbs, args = (self, original_path, thumb_path, size))
                except:
                        pool.terminate()
                        
                pool.close()
                pool.join()

	def _video_thumbnails(self, thumb_path, original_path):
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
			message("couldn't extract video frame", os.path.basename(original_path))
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
			message("couldn't open video thumbnail", tfn)
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
		for size in Photo.thumb_sizes:
			if size[1]:
				self._thumbnail(mirror, original_path, thumb_path, size[0], size[1])
		try:
                        os.unlink(tfn)
                except:
                        pass

	def _video_transcode(self, transcode_path, original_path):
		transcode_path = os.path.join(transcode_path, video_cache(self._path))
                # get number of cores on the system, and use all minus one
                num_of_cores = os.sysconf('SC_NPROCESSORS_ONLN') - 1
		transcode_cmd = [	
			'-i', original_path,		# original file to be encoded
			'-c:v', 'libx264',		# set h264 as videocodec
			'-preset', 'slow',		# set specific preset that provides a certain encoding speed to compression ratio
			'-profile:v', 'baseline',	# set output to specific h264 profile
			'-level', '3.0',		# sets highest compatibility with target devices
			'-crf', '20',			# set quality 
			'-b:v', '4M',			# set videobitrate to 4Mbps
			'-strict', 'experimental',	# allow native aac codec below
			'-c:a', 'aac',			# set aac as audiocodec
			'-ac', '2',			# force two audiochannels
			'-ab', '160k',			# set audiobitrate to 160Kbps
			'-maxrate', '10000000',		# limits max rate, will degrade CRF if needed
			'-bufsize', '10000000',		# define how much the client should buffer
			'-f', 'mp4',			# fileformat mp4
			'-threads', str(num_of_cores),	# number of cores (all minus one)
			'-loglevel', 'quiet',		# don't display anything
			'-y' 				# don't prompt for overwrite
		]
		filters = []
		info_string = "%s -> mp4, h264" % (os.path.basename(original_path))
		message("transcoding", info_string)
		if os.path.exists(transcode_path) and file_mtime(transcode_path) >= self._attributes["dateTimeFile"]:
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
                        message("transcoding failure, trying yuv420p", os.path.basename(original_path))
                        tmp_transcode_cmd.append('-pix_fmt')
                        tmp_transcode_cmd.append('yuv420p')
                        tmp_transcode_cmd.append(transcode_path)
                        p = VideoTranscodeWrapper().call(*tmp_transcode_cmd)
                
                if p == False:
                        message("transcoding failure", os.path.basename(original_path))
                        try:
                                os.unlink(transcode_path)
                        except:
                                pass
                                self.is_valid = False
                        return
                self._video_metadata(transcode_path, False)

	@property
	def name(self):
		return os.path.basename(self._path)
	def __str__(self):
		return self.name
	@property
	def path(self):
		return self._path
	@property
	def image_caches(self):
		caches = []
		if "mediaType" in self._attributes and self._attributes["mediaType"] == "video":
			for size in Photo.thumb_sizes:
				if size[1]:
					caches.append(image_cache(self._path, size[0], size[1]))
			caches.append(video_cache(self._path))
		else:
			caches = [image_cache(self._path, size[0], size[1]) for size in Photo.thumb_sizes]
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

	def __cmp__(self, other):
		date_compare = cmp(self.date, other.date)
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
					dictionary[key] = datetime.strptime(dictionary[key], "%a %b %d %H:%M:%S %Y")
				except KeyboardInterrupt:
					raise
				except:
					pass
		return Photo(path, None, dictionary)
	def to_dict(self):
		photo = { "name": self.name, "date": self.date }
		photo.update(self.attributes)
		return photo

class PhotoAlbumEncoder(json.JSONEncoder):
	def default(self, obj):
		if isinstance(obj, datetime):
			return obj.strftime("%a %b %d %H:%M:%S %Y")
		if isinstance(obj, Album) or isinstance(obj, Photo):
			return obj.to_dict()
		return json.JSONEncoder.default(self, obj)
		
