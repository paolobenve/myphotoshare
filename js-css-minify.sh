#!/bin/bash

# minify all .js-files
cd web/js
echo
echo == Minifying js files in js directory ==
echo
rm -f *.min.js
ls -1 *.js|grep -Ev "min.js$" | while read jsfile; do
	newfile="${jsfile%.*}.min.js"
	echo "$jsfile --> $newfile"
	curl -X POST -s --data-urlencode "input@$jsfile" https://javascript-minifier.com/raw > $newfile
	# following code is unuseful, it detects curl, not javascript errors
	#~ if [ $? -ne 0 ]; then
		#~ echo
		#~ echo "*****************"
		#~ echo "error minifying $jsfile"
		#~ echo "stopping"
		#~ echo "*****************"
		#~ break
	#~ fi
done

# merge all into one single file
rm -f scripts.min.js
cat *.min.js > scripts.min.js


# minify all .css-files
cd ../css
echo
echo == Minifying css files in css directory ==
echo
rm -f *.min.css
ls -1 *.css|grep -Ev "min.css$" | while read cssfile; do
	newfile="${cssfile%.*}.min.css"
	echo "$cssfile --> $newfile"
	curl -X POST -s --data-urlencode "input@$cssfile" https://cssminifier.com/raw > $newfile
	#~ if [ $? -ne 0 ]; then
		#~ echo
		#~ echo "*****************"
		#~ echo "error minifying $cssfile"
		#~ echo "stopping"
		#~ echo "*****************"
		#~ break
	#~ fi
done

# merge all into one single file
rm -f styles.min.css
cat *.min.css > styles.min.css
