#!/bin/sh

# Create dir
mkdir -p images/original
cd images/original

# Download all images
cat ../../image_benchmark_urls | xargs curl --remote-name-all
cd ../../

# Modify all images to our progressive scan
mkdir images/progressive
cd images/progressive
for f in `ls ../original/`;do jpegtran -outfile $f -progressive -scans ../../scanfile ../original/$f;done
cd ../../

# Truncate scans from the progressive JPEGs and put each truncation level in a separate directory
for trunc in 3 4 7 8 10 11  ;do
  mkdir images/truncated_$trunc
  for f in `ls images/progressive`;do ./truncater.py images/progressive/$f images/truncated_$trunc/$f $trunc;done
done

# Create a list of URLs in JSON format
printf "const urls = [ " > urls.js
for f in `ls images/progressive/` ;do printf '"%s", ' "$f";done >> urls.js
printf "]" >> urls.js
