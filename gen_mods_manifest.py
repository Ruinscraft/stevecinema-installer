jcef_dir = "./mods"

import os
import sys
import hashlib

if not os.path.isdir(jcef_dir):
    print('no \'mods\' directory found')
    exit()

manifest = []

for currentpath, folders, files in os.walk(jcef_dir):
    for file in files:
        rel_path = os.path.join(currentpath, file)
        sha1 = hashlib.sha1()
        with open(rel_path, 'rb') as f:
            while True:
                data = f.read(65536) # read in chunks to save memory
                if not data:
                    break
                sha1.update(data)
        manifest.append([rel_path[7:], sha1.hexdigest()])

with open('mods_manifest.txt', 'w') as cef_manifest_file:
    for entry in manifest:
        cef_manifest_file.write(entry[0] + " " + entry[1] + "\n")

print('wrote to mods_manifest.txt')
