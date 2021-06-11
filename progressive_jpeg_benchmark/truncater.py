#!/usr/bin/python

import sys

input_filename = sys.argv[1]
output_filename = sys.argv[2]
scans_to_truncate = -int(sys.argv[3])
scan_offsets = []
with open(input_filename, "rb") as f:
  # Read the input file
  jpeg = f.read()
  offset = 0
  while offset < len(jpeg):
    if jpeg[offset] == "\xff" and jpeg[offset + 1] == "\xda":
      scan_offsets.append(offset)
    offset += 1
  print(scan_offsets)
  offset_to_truncate = scan_offsets[scans_to_truncate]
  print(offset_to_truncate)
  with open(output_filename, "wb") as of:
    of.write(jpeg[0:offset_to_truncate])