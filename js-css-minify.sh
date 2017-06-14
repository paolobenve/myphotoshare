#!/bin/bash

# minify all .js-files
cd web/js
echo
echo == Minifying js files in js directory ==
echo
ls -1 *.js|grep -Ev "min.js$" | while read jsfile; do
	newfile="${jsfile%.*}.min.js"
	echo "$jsfile --> $newfile"
	curl -X POST -s --data-urlencode "input@$jsfile" http://javascript-minifier.com/raw > $newfile
done

# merge all into one single file
rm -f scripts.min.js
cat *.min.js > scripts.min.js


# minify all .css-files
cd ../css
echo
echo == Minifying css files in css directory ==
echo
ls -1 *.css|grep -Ev "min.css$" | while read cssfile; do
	newfile="${cssfile%.*}.min.css"
	echo "$cssfile --> $newfile"
	curl -X POST -s --data-urlencode "input@$cssfile" http://cssminifier.com/raw > $newfile
done

# merge all into one single file
rm -f styles.min.css
cat *.min.css > styles.min.css
