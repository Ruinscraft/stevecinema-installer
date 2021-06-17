installer_manifest_url          = "https://storage.googleapis.com/stevecinema-us-download/installer/manifest.txt"
profile_icon_url                = "https://storage.googleapis.com/stevecinema-us-download/installer/profile_icon"
mods_url                        = "https://storage.googleapis.com/stevecinema-us-download/mods/"
mods_manifest_url               = "https://storage.googleapis.com/stevecinema-us-download/mods/manifest.txt"
# {0} = CEF branch
# {1} = native platform [linux64, win64, macos, macos_arm]
cef_release_url_format          = "https://storage.googleapis.com/stevecinema-us-download/chromium/{0}/{1}/nocodec/Release/"
cef_manifest_url_format         = "https://storage.googleapis.com/stevecinema-us-download/chromium/{0}/{1}/nocodec/manifest.txt"
cef_bsdiff_url_format           = "https://storage.googleapis.com/stevecinema-us-download/chromium/{0}/{1}/bsdiff/"
cef_bsdiff_manifest_url_format  = "https://storage.googleapis.com/stevecinema-us-download/chromium/{0}/{1}/bsdiff/manifest.txt"
# {0} = minecraft version
# {1} = fabric loader version
fabric_profile_url_format       = "https://meta.fabricmc.net/v2/versions/loader/{0}/{1}/profile/json"

import os
import sys
import json
import hashlib
import urllib.request

def make_executable_linux(path):
    mode = os.stat(path).st_mode
    mode |= (mode & 0o444) >> 2
    os.chmod(path, mode)

def sha1_of_file(file_name):
    sha1 = hashlib.sha1()
    with open(file_name, "rb") as file:
        while True:
            data = file.read(65536)
            if not data:
                break
            sha1.update(data)
    return sha1.hexdigest()

def split_remote_file(url):
    split = []
    for line in urllib.request.urlopen(url):
        split.append(line.decode("utf-8").split())
    return split

def download_file(url, dest_path):
    print(url + " -> " + dest_path)
    urllib.request.urlretrieve(url, dest_path)
    print("Complete")

def download_installer_manifest():
    installer_manifest = split_remote_file(installer_manifest_url)

    if installer_manifest:
        return installer_manifest
    else:
        print("Could not download installer manifest")
        exit()

def download_mods_manifest():
    mods_manifest = split_remote_file(mods_manifest_url)

    if (mods_manifest):
        return mods_manifest
    else:
        print("Could not download mods manifest")
        exit()

def download_cef_manifest():
    cef_manifest = split_remote_file(cef_manifest_url)

    if (cef_manifest):
        return cef_manifest
    else:
        print("Could not download CEF manifest")
        exit()

def verify_manifest_entry(entry, local_path, remote_path):
    skip_file = False

    file_name = entry[0]
    sha1 = entry[1]
    file_path = os.path.join(local_path, file_name)

    # Check if file exists, and if so, verify it
    if (os.path.exists(file_path)):
        local_sha1 = sha1_of_file(file_path)
        if local_sha1 == sha1:
            skip_file = True
        else:
            print("Mismatched hash for: " + file_name + "! Will redownload.")

    if not skip_file:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        remote_url = remote_path + file_name
        download_file(remote_url, file_path)

def verify_cef(cef_manifest, minecraft_path):
    if sys.platform == "linux":
        cef_path = os.path.join(minecraft_path, "chromium", "linux64")
    elif sys.platform == "darwin":
        cef_path = os.path.join(minecraft_path, "chromium", "macos")
    elif sys.platform == "win32":
        cef_path = os.path.join(minecraft_path, "chromium", "win64")

    if not os.path.isdir(cef_path):
        os.makedirs(cef_path, exist_ok=True)

    for entry in cef_manifest:
        verify_manifest_entry(entry, cef_path, cef_release_url)

        # If on linux, make cef binaries executable
        if sys.platform == "linux":
            if entry[0] == "jcef_helper" or entry[0] == "chrome-sandbox":
                make_executable_linux(os.path.join(cef_path, entry[0]))
    
    print("CEF verified")

def verify_mods(mods_manifest, minecraft_path):
    mods_path = os.path.join(minecraft_path, "mods", "stevecinema.com")

    if not os.path.isdir(mods_path):
        os.makedirs(mods_path, exist_ok=True)

    for entry in mods_manifest:
        verify_manifest_entry(entry, mods_path, mods_url)

    print("Mods verified")

def verify_launcher_profile(minecraft_path, profile_name):
    profile_path = os.path.join(minecraft_path, "versions", profile_name)

    if not os.path.isdir(profile_path):
        os.makedirs(profile_path, exist_ok=True)

    profile_json_path = os.path.join(profile_path, profile_name + ".json")
    profile_jar_path = os.path.join(profile_path, profile_name + ".jar")

    if not os.path.exists(profile_json_path):
        download_file(fabric_profile_url, profile_json_path)

        # Change the profile identity and save the file back
        with open(profile_json_path, "r") as file_r:
            profile = json.load(file_r)
            profile["id"] = profile_name
            
            with open(profile_json_path, "w") as file_w:
                json.dump(profile, file_w)

    # Create empty jar file if it doesn't exist
    # https://github.com/FabricMC/fabric-installer/blob/master/src/main/java/net/fabricmc/installer/client/ClientInstaller.java#L45
    open(profile_jar_path, "w").close()

def verify_profiles_json(minecraft_path, profile_name):
    profiles_json_path = os.path.join(minecraft_path, "launcher_profiles.json")

    if not os.path.exists(profiles_json_path):
        print("Could not find launcher_profiles.json. Is Minecraft fully installed and has been run at least once?")
        exit()

    with open(profiles_json_path, "r") as file_r:
        root = json.load(file_r)
        profiles = root["profiles"]
        
        if profile_name in profiles:
            profile = profiles[profile_name]
        else:
            import datetime
            iso_time = datetime.datetime.now().isoformat()[:-6] + 'Z'
            with urllib.request.urlopen(profile_icon_url) as response:
                profile_icon = response.read().decode("utf-8")
            profile = {
                "name": profile_name,
                "type": "custom",
                "created": iso_time,
                "lastUsed": iso_time,
                "icon": "data:image/png;base64," + profile_icon
            }

        profile["lastVersionId"] = profile_name
        profiles[profile_name] = profile
        root["profiles"] = profiles

        with open(profiles_json_path, "w") as file_w:
            json.dump(root, file_w)
        
def find_minecraft():
    from pathlib import Path
    home_dir = str(Path.home())

    if sys.platform == "linux":
        if (os.path.isdir(os.path.join(home_dir, ".minecraft"))):
            minecraft_path = os.path.join(home_dir, ".minecraft")
    elif sys.platform == "darwin":
        if os.path.isdir(os.path.join(home_dir, "Library", "Application Support", "minecraft")):
            minecraft_path = os.path.join(home_dir, "Library", "Application Support", "minecraft")
    elif sys.platform == "win32":
        app_data_dir = os.getenv("APPDATA")
        if (app_data_dir):
            if os.path.isdir(os.path.join(app_data_dir, ".minecraft")):
                minecraft_path = os.path.join(app_data_dir, ".minecraft")

    if minecraft_path:
        print("Found Minecraft at: " + minecraft_path)
        return minecraft_path
    else:
        print("Could not find Minecraft install location")
        exit()

# ======== Manifests ========
installer_manifest = download_installer_manifest()
mods_manifest = download_mods_manifest()

cef_branch = installer_manifest[1][1]

if sys.platform == "linux":
    platform_name = "linux64"
elif sys.platform == "darwin":
    platform_name = "macos"
elif sys.platform == "win32":
    platform_name = "win64"

cef_release_url = cef_release_url_format.format(cef_branch, platform_name)
cef_manifest_url = cef_manifest_url_format.format(cef_branch, platform_name)
cef_bsdiff_url = cef_bsdiff_url_format.format(cef_branch, platform_name)
cef_bsdiff_manifest_url = cef_bsdiff_manifest_url_format.format(cef_branch, platform_name)

cef_manifest = download_cef_manifest()
# ======== Manifests ========

# Find Minecraft
minecraft_path = find_minecraft()

verify_cef(cef_manifest, minecraft_path)
verify_mods(mods_manifest, minecraft_path)

# Format fabric meta URL
minecraft_version = installer_manifest[2][1]
fabric_loader_version = installer_manifest[3][1]
fabric_profile_url = fabric_profile_url_format.format(minecraft_version, fabric_loader_version)

# Verify profile information
profile_name = "stevecinema-" + fabric_loader_version + "-" + minecraft_version
verify_launcher_profile(minecraft_path, profile_name)
verify_profiles_json(minecraft_path, profile_name)
