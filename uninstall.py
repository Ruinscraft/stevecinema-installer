import os
import shutil
import json

def uninstall(minecraft_path):
    shutil.rmtree(os.path.join(minecraft_path, "chromium"), ignore_errors=True)
    shutil.rmtree(os.path.join(minecraft_path, "mods", "stevecinema.com"), ignore_errors=True)
    remove_profiles(minecraft_path)

def remove_profiles(minecraft_path):
    profiles_json_path = os.path.join(minecraft_path, "launcher_profiles.json")

    if not os.path.exists(profiles_json_path):
        return

    with open(profiles_json_path, "r") as file_r:
        root = json.load(file_r)
        profiles = root["profiles"]

        for profile_name in list(profiles.keys()):
            if "stevecinema" in profile_name:
                del profiles[profile_name]
                shutil.rmtree(os.path.join(minecraft_path, "versions", profile_name), ignore_errors=True)

        with open(profiles_json_path, "w") as file_w:
            json.dump(root, file_w)
