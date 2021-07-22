installer_manifest_url          = "https://storage.googleapis.com/stevecinema-us-download/installer/manifest.txt"
profile_url_format              = "https://storage.googleapis.com/stevecinema-us-download/installer/profiles/{0}.json"
profile_icon_url                = "https://storage.googleapis.com/stevecinema-us-download/installer/profile_icon"
mods_url                        = "https://storage.googleapis.com/stevecinema-us-download/mods/"
mods_manifest_url               = "https://storage.googleapis.com/stevecinema-us-download/mods/manifest.txt"
# {0} = CEF branch
# {1} = native platform [linux64, win64, macos, macos_arm]
cef_nocodec_release_url_format  = "https://storage.googleapis.com/stevecinema-us-download/chromium/{0}/{1}/nocodec/Release/"
cef_nocodec_manifest_url_format = "https://storage.googleapis.com/stevecinema-us-download/chromium/{0}/{1}/nocodec/manifest.txt?test=test"
cef_codec_release_url_format    = "https://storage.googleapis.com/stevecinema-us-download/chromium/{0}/{1}/codec/Release/"
cef_codec_manifest_url_format   = "https://storage.googleapis.com/stevecinema-us-download/chromium/{0}/{1}/codec/manifest.txt"
cef_bsdiff_release_url_format   = "https://storage.googleapis.com/stevecinema-us-download/chromium/{0}/{1}/bsdiff/Release/"
cef_bsdiff_manifest_url_format  = "https://storage.googleapis.com/stevecinema-us-download/chromium/{0}/{1}/bsdiff/manifest.txt"

import os
import sys
import json
import hashlib
import urllib
import urllib.request
import threading
import mc_finder

import wx

# Find Minecraft
minecraft_path = mc_finder.find_minecraft()

class MainFrame(wx.Frame):

    def __init__(self, parent, title):
        super(MainFrame, self).__init__(parent, title=title, size=(600, 400))

        self.InitUI()
        self.Centre()
        self.total_files_downloaded = 0

    def InitUI(self):
        panel = wx.Panel(self)
        sizer = wx.GridBagSizer(5, 4)

        text1 = wx.StaticText(panel, label="Minecraft Location")
        sizer.Add(text1, pos=(0, 0), flag=wx.TOP|wx.LEFT|wx.BOTTOM)
        
        self.mcLocText = wx.TextCtrl(panel, value=minecraft_path)
        sizer.Add(self.mcLocText, pos=(1, 0), span=(1, 4), flag=wx.EXPAND|wx.LEFT|wx.RIGHT)
        mcLocButton = wx.Button(panel, label="Choose")
        mcLocButton.Bind(wx.EVT_BUTTON, self.onChooseButtonPress) 
        sizer.Add(mcLocButton, pos=(1, 4))

        self.logCtrl = wx.TextCtrl(panel, style=wx.TE_MULTILINE|wx.TE_READONLY|wx.HSCROLL)
        sizer.Add(self.logCtrl, pos=(2, 0), span=(1, 5), flag=wx.EXPAND|wx.LEFT|wx.RIGHT)

        self.uninstallButton = wx.Button(panel, label="Uninstall")
        self.uninstallButton.Bind(wx.EVT_BUTTON, self.onUninstallButtonPress) 
        sizer.Add(self.uninstallButton, pos=(3, 0))

        self.gauge = wx.Gauge(panel, size=(250, 25), style=wx.GA_HORIZONTAL)
        sizer.Add(self.gauge, pos=(3, 1))

        self.installButton = wx.Button(panel, label="Install / Verify")
        self.installButton.Bind(wx.EVT_BUTTON, self.onInstallButtonPress) 
        sizer.Add(self.installButton, pos=(3, 4))

        text2 = wx.StaticText(panel, label="© 2021 Ruinscraft, LLC")
        sizer.Add(text2, pos=(4, 0))

        sizer.AddGrowableCol(1)
        sizer.AddGrowableCol(2)
        sizer.AddGrowableRow(2)

        panel.SetSizer(sizer)

    def setGaugeRange(self, range):
        self.gauge.SetRange(range)

    def updateGauge(self):
        self.total_files_downloaded = self.total_files_downloaded + 1
        wx.CallAfter(self.gauge.SetValue, self.total_files_downloaded)

    def onChooseButtonPress(self, event):
        dialog = wx.DirDialog(None, "Choose Minecraft Location:")
        if dialog.ShowModal() == wx.ID_OK:
            self.mcLocText.SetValue(dialog.GetPath())
        dialog.Destroy()

    def onUninstallButtonPress(self, event):
        uninstallThread = threading.Thread(target=self.uninstall)
        uninstallThread.start()

    def onInstallButtonPress(self, event):
        installThread = threading.Thread(target=self.install)
        installThread.start()

    def log(self, msg):
        wx.CallAfter(self.logCtrl.write, msg + "\n")

    def uninstall(self):
        self.disableButtons()
        import uninstall
        uninstall.uninstall(minecraft_path)
        self.log("Uninstall Complete!")
        wx.CallAfter(wx.MessageBox, "Steve Cinema content has been removed from your system.", "Complete!")
        self.enableButtons()

    def install(self):
        self.total_files_downloaded = 0
        self.disableButtons()
        verify_codec_cef(cef_nocodec_manifest, cef_codec_manifest, cef_bsdiff_manifest, minecraft_path)
        verify_mods(mods_manifest, minecraft_path)
        verify_launcher_profile(minecraft_path, profile_name)
        verify_profiles_json(minecraft_path, profile_name)
        self.log("Installation Complete!")
        wx.CallAfter(wx.MessageBox, "You may close this program. Open Minecraft with the new Steve Cinema profile to play!", "Complete!")
        self.enableButtons()

    def disableButtons(self):
        wx.CallAfter(self.installButton.Disable)
        wx.CallAfter(self.uninstallButton.Disable)

    def enableButtons(self):
        wx.CallAfter(self.installButton.Enable)
        wx.CallAfter(self.uninstallButton.Enable)

mcpApp = wx.App()
mainFrame = MainFrame(None, title='Steve Cinema Installer for Minecraft')

def make_executable_nix(file_path):
    mode = os.stat(file_path).st_mode
    mode |= (mode & 0o444) >> 2
    os.chmod(file_path, mode)

def make_executable_recursive_nix(path):
    for root, dirs, files in os.walk(path):  
        for momo in dirs:  
            make_executable_nix(os.path.join(root, momo))
        for momo in files:
            make_executable_nix(os.path.join(root, momo))

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
    mainFrame.log("Downloading " + url + " -> " + dest_path)
    urllib.request.urlretrieve(url.replace(" ", "%20"), dest_path)
    mainFrame.log("Complete")
    mainFrame.updateGauge()

def manifest_entry_get_file(entry):
    return ' '.join(entry[0:len(entry) - 1])

def manifest_entry_get_hash(entry):
    return entry[-1]

def download_installer_manifest():
    installer_manifest = split_remote_file(installer_manifest_url)

    if installer_manifest:
        return installer_manifest
    else:
        mainFrame.log("Could not download installer manifest")

def download_mods_manifest():
    mods_manifest = split_remote_file(mods_manifest_url)

    if mods_manifest:
        return mods_manifest
    else:
        mainFrame.log("Could not download mods manifest")

def download_cef_nocodec_manifest():
    manifest = split_remote_file(cef_nocodec_manifest_url)

    if manifest:
        return manifest
    else:
        mainFrame.log("Could not download CEF nocodec manifest")

def download_cef_codec_manifest():
    manifest = split_remote_file(cef_codec_manifest_url)

    if manifest:
        return manifest
    else:
        mainFrame.log("Could not download CEF codec manifest")

def download_cef_bsdiff_manifest():
    manifest = split_remote_file(cef_bsdiff_manifest_url)

    return manifest;
    # temp fix for macos
    # if manifest:
    #     return manifest
    # else:
    #     mainFrame.log("Could not download CEF bsdiff manifest")

def verify_manifest_entry(entry, local_path, remote_path):
    skip_file = False

    file_name = manifest_entry_get_file(entry)
    sha1 = manifest_entry_get_hash(entry)
    file_path = os.path.join(local_path, file_name)

    # Check if file exists, and if so, verify it
    if os.path.exists(file_path):
        local_sha1 = sha1_of_file(file_path)
        if local_sha1 == sha1:
            skip_file = True
        else:
            mainFrame.log("Mismatched hash for: " + file_name + "! Will redownload.")

    if not skip_file:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        remote_url = remote_path + file_name
        download_file(remote_url, file_path)

def verify_manifest_bsdiff_entry(non_patched_entry, patched_entry, local_path, remote_path, remote_patch_path):
    download = True
    patch = True

    file_name = manifest_entry_get_file(non_patched_entry)
    non_patched_sha1 = manifest_entry_get_hash(non_patched_entry)
    patched_sha1 = manifest_entry_get_hash(patched_entry)
    file_path = os.path.join(local_path, file_name)

    if os.path.exists(file_path):
        local_sha1 = sha1_of_file(file_path)
        if local_sha1 == patched_sha1:
            download = False
            patch = False
        elif local_sha1 == non_patched_sha1:
            download = False
        else:
            mainFrame.log("Mismatched hash for: " + file_name + "! Will redownload.")

    # Download unpatched file if needed
    if download:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        remote_url = remote_path + file_name
        download_file(remote_url, file_path)

    # Patch file if needed
    if patch:
        # Download patch file
        remote_url = cef_bsdiff_release_url + file_name + ".bsdiff"
        bsdiff_file_path = file_path + ".bsdiff"
        download_file(remote_url, bsdiff_file_path)

        mainFrame.log("Patching " + file_path + " with " + bsdiff_file_path)
        import bsdiff4
        bsdiff4.file_patch_inplace(file_path, bsdiff_file_path)
        mainFrame.log("Complete")

def make_cef_dir():
    if sys.platform == "linux":
        cef_platform = "linux64"
    elif sys.platform == "darwin":
        cef_platform = "macos"
    elif sys.platform == "win32":
        cef_platform = "win64"

    cef_path = os.path.join(minecraft_path, "chromium", cef_platform)

    if not os.path.isdir(cef_path):
        os.makedirs(cef_path, exist_ok=True)

    return cef_path

def verify_nocodec_cef(cef_nocodec_manifest, minecraft_path):
    cef_path = make_cef_dir()

    for entry in cef_nocodec_manifest:
        verify_manifest_entry(entry, cef_path, cef_nocodec_release_url)

        if sys.platform == "linux":
            file_name = manifest_entry_get_file(entry)
            if file_name == "jcef_helper" or file_name == "chrome-sandbox":
                make_executable_nix(os.path.join(cef_path, file_name))
        elif sys.platform == "darwin":
            make_executable_recursive_nix(cef_path)
    
    mainFrame.log("Nocodec-CEF verified")

def verify_codec_cef(cef_nocodec_manifest, cef_codec_manifest, cef_bsdiff_manifest, minecraft_path):
    cef_path = make_cef_dir()

    for non_patched_entry in cef_nocodec_manifest:
        non_patched_file_name = manifest_entry_get_file(non_patched_entry)

        has_patch = False

        for diff_entry in cef_bsdiff_manifest:
            diff_file_name = manifest_entry_get_file(diff_entry)
            diff_hash = manifest_entry_get_hash(diff_entry)

            if diff_file_name.replace(".bsdiff", "") == non_patched_file_name:
                has_patch = True

        if has_patch:
            for patched_entry in cef_codec_manifest:
                patched_file_name = manifest_entry_get_file(patched_entry)

                if patched_file_name == non_patched_file_name:
                    verify_manifest_bsdiff_entry(non_patched_entry, patched_entry, cef_path, cef_nocodec_release_url, cef_bsdiff_release_url)
        else:
            verify_manifest_entry(non_patched_entry, cef_path, cef_nocodec_release_url)

        if sys.platform == "linux":
            if non_patched_file_name == "jcef_helper" or non_patched_file_name == "chrome-sandbox":
                make_executable_nix(os.path.join(cef_path, non_patched_file_name))
        elif sys.platform == "darwin":
            make_executable_recursive_nix(cef_path)

    mainFrame.log("Codec-CEF verified")

def verify_mods(mods_manifest, minecraft_path):
    mods_path = os.path.join(minecraft_path, "mods", "stevecinema.com")

    if not os.path.isdir(mods_path):
        os.makedirs(mods_path, exist_ok=True)

    for entry in mods_manifest:
        verify_manifest_entry(entry, mods_path, mods_url)

    mainFrame.log("Mods verified")

def verify_launcher_profile(minecraft_path, profile_name):
    profile_path = os.path.join(minecraft_path, "versions", profile_name)

    if not os.path.isdir(profile_path):
        os.makedirs(profile_path, exist_ok=True)

    profile_json_path = os.path.join(profile_path, profile_name + ".json")
    profile_jar_path = os.path.join(profile_path, profile_name + ".jar")

    if not os.path.exists(profile_json_path):
        download_file(profile_url, profile_json_path)

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
        mainFrame.log("Could not find launcher_profiles.json. Is Minecraft fully installed and has been run at least once?")
        return

    with open(profiles_json_path, "r") as file_r:
        root = json.load(file_r)
        profiles = root["profiles"]
        
        if profile_name in profiles:
            profile = profiles[profile_name]
        else:
            import datetime
            iso_time = datetime.datetime.now().isoformat() + 'Z'
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

cef_nocodec_release_url = cef_nocodec_release_url_format.format(cef_branch, platform_name)
cef_nocodec_manifest_url = cef_nocodec_manifest_url_format.format(cef_branch, platform_name)
cef_codec_release_url = cef_codec_release_url_format.format(cef_branch, platform_name)
cef_codec_manifest_url = cef_codec_manifest_url_format.format(cef_branch, platform_name)
cef_bsdiff_release_url = cef_bsdiff_release_url_format.format(cef_branch, platform_name)
cef_bsdiff_manifest_url = cef_bsdiff_manifest_url_format.format(cef_branch, platform_name)

cef_nocodec_manifest = download_cef_nocodec_manifest()
cef_codec_manifest = download_cef_codec_manifest()
cef_bsdiff_manifest = download_cef_bsdiff_manifest()

# Format fabric meta URL
profile_name = installer_manifest[2][1]
profile_url = profile_url_format.format(profile_name)

total_files_to_download = 0
total_files_to_download += len(cef_nocodec_manifest)
total_files_to_download += len(cef_bsdiff_manifest)
mainFrame.setGaugeRange(total_files_to_download)
# ======== Manifests ========

# LETS GET THE SHOW STARTED
wx.MessageBox("stevecinema-installer Disclaimer\n\n\nThis software contains binary patches for CEF to include additional codecs (AVC & MPEG-4). The end user is responsible for compiling the final binary product via this helper-software. See the Google Chrome license for more info here: https://www.google.com/chrome/terms/", "Message", wx.OK|wx.ICON_INFORMATION)
mainFrame.Show()
mcpApp.MainLoop()

print("Exiting")
