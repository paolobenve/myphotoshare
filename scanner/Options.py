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
num_video = 0
num_video_processed = 0
# set this variable to a new integer number whenever the json files structure changes
json_version = 1
