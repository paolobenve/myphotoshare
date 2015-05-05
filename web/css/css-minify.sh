#!/bin/bash

# minify all .css-files
ls -1 *.css|grep -Ev "min.css$" | while read cssfile; do
	newfile="${cssfile%.*}.min.css"
	echo "$cssfile --> $newfile"
	curl -X POST -s --data-urlencode "input@$cssfile" http://cssminifier.com/raw > $newfile
done

# merge all into one single file
rm -f scripts.min.css
cat *.min.css > scripts.min.css
