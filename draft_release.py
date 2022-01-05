#!/usr/bin/env python3
import os
import sys
import json
import requests
from zipfile import ZipFile
import io
import lib_virustotal
import lib_github
from lib_github import gh


def get_formatted_name(name):
    f = name.split(".")
    fn = f[0]
    ext = f[1]
    fn = fn.split("-qt-")[0]
    fn = fn.replace('installer-osx', 'osx-installer')
    fn = fn.replace('installer-windows', 'windows-installer')
    if ext == "zip":
        fn = f"{fn}-portable"
    elif ext == 'tar':
        ext = "tar.zst"
    elif ext == "exe":
        ext = "zip"
    elif ext == "7z":
        pass
    elif ext == "dmg":
        ext = "zip"
    elif ext == "AppImage":
        ext = "zip"
    else:
        ext = f"-{ext}.zip"


    raw_fn = fn.split("-")
    if raw_fn[0].lower() in ['gleecdex', 'dogedex', 'firodex']:
        project_name = f"{raw_fn[0]}-desktop"
        opsys = raw_fn[1]
    else:
        project_name = f"{raw_fn[0]}-{raw_fn[1]}"
        opsys = raw_fn[2]

    fn_std = f"{project_name}-{VERSION}-beta-{opsys}"
    if "installer" in name:
        fn_std = f"{fn_std}-installer"
    elif "dmg" in name:
        fn_std = f"{fn_std}-dmg"
    elif "AppImage" in name:
        fn_std = f"{fn_std}-appimage"
    else:
        fn_std = f"{fn_std}-portable"
    return raw_fn[0], f"{fn_std}.{ext}"


# Get archives from GH run
RUN_NUMBER = input("Enter Github run number: ")
VERSION = input("Enter release version: ")
REPO = "atomicDEX-Desktop"
OWNER = "smk762"
KP_OWNER = "KomodoPlatform"


run_url = f"{lib_github.base_url}/repos/{KP_OWNER}/{REPO}/actions/runs/{RUN_NUMBER}"
run_html_url = f"https://github.com/{KP_OWNER}/{REPO}/actions/runs/{RUN_NUMBER}"
artefacts_url = f"{run_url}/artifacts"
release_branch = lib_github.get_run_branch(run_url)
if not release_branch:
    print(f"{run_html_url} is not valid!")
    sys.exit()

formatted_names = []
print(f"Getting archives from {run_html_url}...")
r = gh.get(artefacts_url)

for a in r.json()['artifacts']:
    project, formatted_name = get_formatted_name(a["name"])
    release_name = f'{project.title().replace("dex", "DEX")} v{VERSION} beta'
    archive_download_url = a["archive_download_url"]

    if not formatted_name.endswith('.tar.zst'):
        formatted_names.append(formatted_name)
        if not os.path.exists(formatted_name):
            print(f"Downloading {a['name']} ({formatted_name})...")
            r = gh.get(archive_download_url)
            with open(formatted_name, "wb") as f:
                f.write(r.content)
        else:
            print(f"{formatted_name} already exists in this folder!")


formatted_names.sort()

release_tag = f"{VERSION}-beta"
release_body = "### Release Notes\n\n\
**Features:**\n\n\
**Enhancements:**\n\n\
**Fixes:**\n\n\
**Checksum & VirusTotal Analysis:**\n\n\
| Link | SHA256 |\n\
|--------|-------------|"

for name in formatted_names:
    print(f"Getting hash for {name}")
    vt_hash = lib_virustotal.get_vt_hash(name)
    release_body = f"{release_body}\n| [{name}](https://www.virustotal.com/gui/file/{vt_hash}) | `{vt_hash}` |"

release_data = {
    "accept": "application/vnd.github.v3+json",
    "owner": f"{OWNER}",
    "repo": f"{REPO}",
    "tag_name": release_tag,
    "target_commitish": release_branch,
    "name": f"{release_name}-autotest", 
    "body": release_body,
    "draft": True,
    "prerelease": False
}

if not lib_github.check_release_exists(release_name):
    print(f"Release name: {release_name}")
    print(f"Release tag: {release_tag}")
    print(f"Release branch: {release_branch}")
    print(release_body)
    lib_github.create_release(f"{OWNER}", f"{REPO}", json.dumps(release_data))