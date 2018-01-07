from datetime import datetime

config = {}
date_time_format = "%Y-%m-%d %H:%M:%S"
exif_date_time_format = "%Y:%m:%d %H:%M:%S"
video_date_time_format = "%Y-%m-%d %H:%M:%S"
last_time = datetime.now()
elapsed_times = {}
elapsed_times_counter = {}
num_photo = 0
num_photo_processed = 0
num_photo_geotagged = 0
num_photo_with_exif_date = 0
num_video = 0
num_video_processed = 0
photos_without_geotag = []
photos_without_exif_date = []
options_not_to_be_saved = ['cache_path', 'index_html_path', 'album_path']
# set this variable to a new integer number whenever the json files structure changes
# json_version = 1 since ...
# json_version = 2 since checksums have been added
json_version = 2
