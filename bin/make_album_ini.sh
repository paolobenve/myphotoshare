#!/bin/bash
###########
# Create a default MyPhotoShare 'album.ini' file base on media content files in a directory.


# All media file extensions that will be considered
# jpg,jpeg,JPG,mp4,avi,MP4,AVI


if [ -z "$1" ]; then
	echo "$0 FOLDER"
	echo "Create template of 'album.ini' file in 'FOLDER' based on its media content."
	exit 1
fi


DIR=${1%/}
if [ ! -d "$DIR" ]; then
	( >&2 echo "Argument must be a directory containing media." )
	exit 1
fi

if [ -e "$DIR/album.ini" ]; then
	( >&2 echo "'$DIR/album.ini' already exists. Nothing done.")
	exit 2
fi



TITLE=${DIR##*/}
echo "# User defined metadata for MyPhotoShare" >> "$DIR/album.ini"
echo > "$DIR/album.ini"
echo "[album]" >> "$DIR/album.ini"
echo "#title = $TITLE" >> "$DIR/album.ini"
echo "#description = " >> "$DIR/album.ini"
echo "#tags = " >> "$DIR/album.ini"
echo >> "$DIR/album.ini"
echo >> "$DIR/album.ini"

SAVEIFS="$IFS"
IFS=$(echo -en "\n\b")
for media in $(ls "$DIR"/*.{jpg,jpeg,JPG,mp4,avi,MP4,AVI} 2> /dev/null); do
	MEDIA=${media##*/}
	MEDIA=${MEDIA%.*}
	echo "[$MEDIA]" >> "$DIR/album.ini"
	echo "#title = $MEDIA" >> "$DIR/album.ini"
	echo "#description = " >> "$DIR/album.ini"
	echo "#tags = " >> "$DIR/album.ini"
	echo "#latitude = " >> "$DIR/album.ini"
	echo "#longitude = " >> "$DIR/album.ini"
	echo >> "$DIR/album.ini"
	echo >> "$DIR/album.ini"
done
IFS=$SAVEIFS

