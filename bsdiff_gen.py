nocodec_dir = "nocodec"
codec_dir = "codec"

import os
import bsdiff4

for currentpath, folders, files in os.walk(nocodec_dir):
    for file in files:
        nocodec_file_path = os.path.join(currentpath, file)
        codec_file_path = codec_dir + nocodec_file_path[7:]
        bsdiff4.file_diff(nocodec_file_path, codec_file_path, codec_file_path + ".bsdiff")

