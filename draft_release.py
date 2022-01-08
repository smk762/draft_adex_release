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
from lib_color import *

SCRIPT_PATH = sys.path[0]

def get_formatted_name(name):
    f = name.split(".")
    fn = f[0]
    ext = '.'.join(f[-1:])
    fn = fn.split("-qt-")[0]
    fn = fn.replace('installer-osx', 'osx-installer')
    fn = fn.replace('installer-windows', 'windows-installer')
    if ext == "zip":
        fn = f"{fn}-portable"
    elif ext in ["exe", "dmg", "AppImage"]:
        ext = "zip"


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


def get_new_name(fn, formatted_name):
    ext = '.'.join(fn.split(".")[-1:])
    # drop os and type
    fn = '-'.join(formatted_name.split("-")[:-2])
    return f"{fn}.{ext}"




# Get archives from GH run
print("")
RUN_NUMBER = color_input("Enter Github run number: ")
VERSION = color_input("Enter release version: ")
REPO = "atomicDEX-Desktop"
OWNER = "smk762"
KP_OWNER = "KomodoPlatform"

run_url = f"{lib_github.base_url}/repos/{KP_OWNER}/{REPO}/actions/runs/{RUN_NUMBER}"
run_html_url = f"https://github.com/{KP_OWNER}/{REPO}/actions/runs/{RUN_NUMBER}"
artefacts_url = f"{run_url}/artifacts"

run_info = lib_github.get_run_info(run_url)
if "head_branch" in run_info:
    release_branch = run_info["head_branch"]
    commit_hash = run_info["head_sha"]
else:
    error_print(f"{run_html_url} is not valid!")
    sys.exit()


formatted_names = []
status_print(f"Getting archives from {run_html_url}...")
r = gh.get(artefacts_url)

for a in r.json()['artifacts']:
    if not a["name"].endswith('.zst'):
        project, formatted_name = get_formatted_name(a["name"])
        release_name = f'{project.title().replace("dex", "DEX")} v{VERSION} beta'
        archive_download_url = a["archive_download_url"]
        formatted_names.append(formatted_name)
        if not os.path.exists(f"raw_{formatted_name}"):
            status_print(f"Downloading {a['name']} as raw_{formatted_name}...")
            r = gh.get(archive_download_url)
            with open(f"raw_{formatted_name}", "wb") as f:
                f.write(r.content)
        else:
            status_print(f"raw_{formatted_name} already exists in this folder!")

## TODO: Need to extract and rename files in zip and recompress
##       and add extras like the make_executable.gif

formatted_names.sort()


for name in formatted_names:
    if os.path.exists(f"raw_{name}"):
        # Extract 
        with ZipFile(f"raw_{name}", 'r') as za:
            za.extractall(f"{SCRIPT_PATH}/raw_{name}_temp")
            # rename as required
            with ZipFile(f"{name}", 'w') as zb:
                for file in os.listdir(f"{SCRIPT_PATH}/raw_{name}_temp"):
                    new_name = get_new_name(file, name)
                    zb.write(filename=f"{SCRIPT_PATH}/raw_{name}_temp/{file}", arcname=new_name)
                    if f"{name}".find("appimage") > -1:
                        for extra_file in [
                                "README.txt",
                                "prerequisites.sh",
                                "make_executable.gif"
                            ]:
                            zb.write(extra_file)
    else:
        status_print(f"{formatted_name} already exists in this folder!")

release_tag = f"{VERSION}-beta"
release_body = "### Release Notes\n\n\
**Features:**\n\n\
**Enhancements:**\n\n\
**Fixes:**\n\n\
**Checksum & VirusTotal Analysis:**\n\n\
| Link   | SHA256      |\n\
|--------|-------------|"


for name in formatted_names:
    status_print(f"Getting hash for {name}")
    vt_hash = lib_virustotal.get_vt_hash(name)
    release_body = f"{release_body}\n| [{name}](https://www.virustotal.com/gui/file/{vt_hash}) | `{vt_hash}` |"

# Draft release
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
    table_print(f"Release name: {release_name}")
    table_print(f"Release tag: {release_tag}")
    table_print(f"Release branch: {release_branch}")
    table_print(release_body)
    release_info = lib_github.create_release(f"{OWNER}", f"{REPO}", json.dumps(release_data))
    table_print(release_info)
    release_id = release_info["id"]
    upload_url = release_info["upload_url"].replace("{?name,label}", "")


    for name in formatted_names:
        upload_data = {
            "accept": "application/vnd.github.v3+json",
            "owner": f"{OWNER}",
            "repo": f"{REPO}",
            "release_id": release_id,
            "name": f"{name}", 
            "label": name
        }
        params = (
          ('name', f"{name}"),
          ('label', name),
        )
        print(upload_data)
        upload_reponse = lib_github.upload_release_asset(upload_url, upload_data, params, f"{SCRIPT_PATH}/{name}")
        print(upload_reponse)
