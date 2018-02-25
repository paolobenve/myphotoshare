#!/bin/bash
###########
# Create a default MyPhotoShare 'album.ini' file based on media content files in a directory.
# Append new media sections if 'album.ini' already exists.

# All media file extensions that will be considered
# jpg,jpeg,JPG,JPEG,mp4,avi,MP4,AVI


DIR=${1%/}

if [ -z "$DIR" ]; then
	echo "$0 FOLDER"
	echo "Create template of 'album.ini' file in 'FOLDER' based on its media content."
	echo "When the file 'album.ini' already exists in 'FOLDER', new media are added to the file."
	exit 1
elif [ ! -d "$DIR" ]; then
	( >&2 echo "Argument must be a directory containing media." )
	exit 1
fi


if [ ! -f "$DIR/album.ini" ]; then
	touch "$DIR/album.ini"
fi

# Count the number of media added
SECTION_COUNT=0

# The [album] section
SECTION_EXISTS=$(grep -c "\[album\]" "$DIR/album.ini")
if [ $SECTION_EXISTS -eq 0 ]; then
	TITLE=${DIR##*/}
	echo "# User defined metadata for MyPhotoShare" >> "$DIR/album.ini"
	echo >> "$DIR/album.ini"
	echo "[album]" >> "$DIR/album.ini"
	echo "#title = $TITLE" >> "$DIR/album.ini"
	echo "#description = " >> "$DIR/album.ini"
	echo "#tags = " >> "$DIR/album.ini"
	echo >> "$DIR/album.ini"
	echo >> "$DIR/album.ini"
	((SECTION_COUNT+=1))
fi

# Loop on album content
SAVEIFS="$IFS"
IFS=$(echo -en "\n\b")
for media in $(ls "$DIR"/*.{jpg,jpeg,JPG,JPEG,mp4,avi,MP4,AVI} 2> /dev/null); do
	SECTION=${media##*/}
	TITLE=${SECTION%.*}
	SECTION_EXISTS=$(grep -c "\[$SECTION\]" "$DIR/album.ini")
	if [ $SECTION_EXISTS -eq 0 ]; then
		echo "[$SECTION]" >> "$DIR/album.ini"
		echo "#title = $TITLE" >> "$DIR/album.ini"
		echo "#description = " >> "$DIR/album.ini"
		echo "#tags = " >> "$DIR/album.ini"
		echo "#latitude = " >> "$DIR/album.ini"
		echo "#longitude = " >> "$DIR/album.ini"
		echo >> "$DIR/album.ini"
		echo >> "$DIR/album.ini"
		((SECTION_COUNT+=1))
	fi
done
IFS=$SAVEIFS

echo "$SECTION_COUNT media added to '$DIR/album.ini'."

