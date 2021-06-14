#!/usr/bin/python

import os
import json

original_dir_name = "images/progressive/"
truncated_dir_names = ["3", "4", "7", "8", "10", "11"]
truncated_dir_prefix = "images/truncated_"
output_object = []
urls = os.listdir(original_dir_name)
for url in urls:
  original_size = os.path.getsize(original_dir_name + url)
  truncated_sizes = {}
  for trunc in truncated_dir_names:
    truncated_sizes[trunc] = os.path.getsize(truncated_dir_prefix + trunc + "/" + url)
  url_object = {}
  url_object["url"] = url
  url_object["original_size"] = original_size
  url_object["truncated_sizes"] = truncated_sizes
  output_object.append(url_object)
output_json = json.dumps(output_object);
print "const urls = " + output_json

