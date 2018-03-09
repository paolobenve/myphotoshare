#!/bin/bash
###########
# Create a default MyPhotoShare 'album.ini' file based on media content files in a directory.
# Append new media sections if 'album.ini' already exists.

# All media file extensions that will be considered
# jpg,jpeg,JPG,JPEG,mp4,avi,MP4,AVI


print_usage()
{
	echo "Usage: $0 [-i METADATA_FILENAME] FOLDER"
	echo "Create template of 'album.ini' file in 'FOLDER' based on its media content."
	echo "When the file 'album.ini' already exists in 'FOLDER', new media are added to the file."
	echo
	echo "Options:"
	echo "  -i: Define the filename used to store user-defined metadata instead of default 'album.ini'"
	echo
	echo "Example:"
	echo "   $0 -i .album.ini ~/Pictures/vacations"
	echo "   Create hidden file '.album.ini' in '~/Pictures/vacations"
}


# Process options
ALBUM_INI="album.ini"

while getopts "i:" option; do
	case $option in
		i)
			ALBUM_INI="$OPTARG"
		;;
		\?)
			print_usage
			exit 1
		;;
	esac
done
shift $((OPTIND-1))

# Process parameters
DIR=${1%/}

if [ -z "$DIR" ]; then
	print_usage
	exit 1
elif [ ! -d "$DIR" ]; then
	( >&2 echo "Argument must be a directory containing media." )
	exit 1
fi


if [ ! -f "$DIR/$ALBUM_INI" ]; then
	echo "# User defined metadata for MyPhotoShare" > "$DIR/$ALBUM_INI"
	echo "########################################" >> "$DIR/$ALBUM_INI"
	echo "# Possible metadata:" >> "$DIR/$ALBUM_INI"
	echo "# - title: To give a title to the photo, video or album." >> "$DIR/$ALBUM_INI"
	echo "# - description: A long description of the media." >> "$DIR/$ALBUM_INI"
	echo "# - tags: A comma separated list of key words." >> "$DIR/$ALBUM_INI"
	echo "# - date: The date the photo was taken, in the format YYYY-MM-DD." >> "$DIR/$ALBUM_INI"
	echo "# - latitude: The latitude of the media, for instance if the media was not geotagged when captured." >> "$DIR/$ALBUM_INI"
	echo "# - longitude: The longitude of the capture of media." >> "$DIR/$ALBUM_INI"
	echo "# - country_name: The name of the country where the photo was shot." >> "$DIR/$ALBUM_INI"
	echo "# - region_name: The name of the region." >> "$DIR/$ALBUM_INI"
	echo "# - place_name: The name of the city or town to be displayed." >> "$DIR/$ALBUM_INI"
	echo >> "$DIR/$ALBUM_INI"
	echo >> "$DIR/$ALBUM_INI"
	echo "#[DEFAULT]" >> "$DIR/$ALBUM_INI"
	echo "#tags = " >> "$DIR/$ALBUM_INI"
	echo "#date = " >> "$DIR/$ALBUM_INI"
	echo "#latitude = " >> "$DIR/$ALBUM_INI"
	echo "#longitude = " >> "$DIR/$ALBUM_INI"
	echo "#place_name = " >> "$DIR/$ALBUM_INI"
	echo "#region_name = " >> "$DIR/$ALBUM_INI"
	echo "#country_name = " >> "$DIR/$ALBUM_INI"
	echo >> "$DIR/$ALBUM_INI"
	echo >> "$DIR/$ALBUM_INI"
fi

# Count the number of media added
SECTION_COUNT=0

# The [album] section
SECTION_EXISTS=$(grep -c "\[album\]" "$DIR/$ALBUM_INI")
if [ $SECTION_EXISTS -eq 0 ]; then
	TITLE=${DIR##*/}
	echo "[album]" >> "$DIR/$ALBUM_INI"
	echo "#title = $TITLE" >> "$DIR/$ALBUM_INI"
	echo "#description = " >> "$DIR/$ALBUM_INI"
	echo "#tags = " >> "$DIR/$ALBUM_INI"
	echo >> "$DIR/$ALBUM_INI"
	echo >> "$DIR/$ALBUM_INI"
	((SECTION_COUNT+=1))
fi

# Loop on album content
SAVEIFS="$IFS"
IFS=$(echo -en "\n\b")
for media in $(ls "$DIR"/*.{jpg,jpeg,JPG,JPEG,mp4,avi,MP4,AVI} 2> /dev/null); do
	SECTION=${media##*/}
	TITLE=${SECTION%.*}
	SECTION_EXISTS=$(grep -c "\[$SECTION\]" "$DIR/$ALBUM_INI")
	if [ $SECTION_EXISTS -eq 0 ]; then
		echo "[$SECTION]" >> "$DIR/$ALBUM_INI"
		echo "#title = $TITLE" >> "$DIR/$ALBUM_INI"
		echo "#description = " >> "$DIR/$ALBUM_INI"
		echo "#tags = " >> "$DIR/$ALBUM_INI"
		echo "#latitude = " >> "$DIR/$ALBUM_INI"
		echo "#longitude = " >> "$DIR/$ALBUM_INI"
		echo >> "$DIR/$ALBUM_INI"
		echo >> "$DIR/$ALBUM_INI"
		((SECTION_COUNT+=1))
	fi
done
IFS=$SAVEIFS

# Print number of media added in 'album.ini'
echo "$SECTION_COUNT media added to '$DIR/$ALBUM_INI'."

