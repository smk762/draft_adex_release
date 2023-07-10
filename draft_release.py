#!/usr/bin/env python3
import os
import sys
import json
import requests
import shutil
import shlex
import subprocess
from zipfile import ZipFile
import io
import lib_virustotal
import lib_github
from lib_github import gh
from lib_color import *

SCRIPT_PATH = sys.path[0]

def get_formatted_name(name):
    for i in ["osx", "windows", "ubuntu"]:
        if name.find(i) > -1:
            opsys = i

    f = name.split(".")
    fn = f[0]
    ext = '.'.join(f[-1:])

    # drops hash and qt string
    fn = fn.split("-qt-")[0]

    # handle whitelabels
    raw_fn = fn.split("-")
    project_name = f"{raw_fn[0]}"

    fn_std = f"{project_name}-wallet-{VERSION}-beta-{opsys}"
    if "installer" in name:
        fn_std = f"{fn_std}-installer"
    elif "dmg" in name:
        fn_std = f"{fn_std}-dmg"
    elif "AppImage" in name:
        fn_std = f"{fn_std}-appimage"
    else:
        fn_std = f"{fn_std}-portable"
    return project_name, f"{fn_std}.{ext}"

def get_new_name(file, formatted_name):
    print(f"file: {file}")
    new_name = '.'.join(formatted_name.split('.')[:-1]) +"."+file.split(".")[1]
    for i in ['-dmg','-appimage']:
        new_name = new_name.replace(i, '')
    print(f"new_name: {new_name}")
    return new_name

# Get Inputs
print("")

RUN_NUMBER = color_input("Enter Github run number: ")
VERSION = color_input("Enter release version (e.g. 0.5.4): ")
REPO = color_input("Enter repository name (e.g. atomicDEX-Desktop): ")
SRC_OWNER = color_input("Enter archive source repository organisation (e.g. KomodoPlatform): ")
DEST_OWNER = color_input("Enter release destination repository organisation (e.g. smk762): ")

'''
RUN_NUMBER = 1675209975
VERSION = "0.5.test"
REPO = "atomicDEX-Desktop"
SRC_OWNER = "KomodoPlatform"
DEST_OWNER = "smk762"
'''

valid_token = False
# Validate input to protect against injection
for i in ["ghp_", "gho_", "ghu_", "ghs_", "ghr_"]:
    if lib_github.GH_TOKEN.startswith(i):
        valid_token = True

for i in [" ", ";", "passwd", "*"]:
    if lib_github.GH_TOKEN.find(" ") > -1:
        valid_token = False

if not valid_token:
    print("Invalid github token!")
    sys.exit()



# Prepare run
run_url = f"{lib_github.base_url}/repos/{SRC_OWNER}/{REPO}/actions/runs/{RUN_NUMBER}"
run_html_url = f"https://github.com/{SRC_OWNER}/{REPO}/actions/runs/{RUN_NUMBER}"
artefacts_url = f"{run_url}/artifacts"
release_tag = f"{VERSION}-beta"

# Get run info
run_info = lib_github.get_run_info(run_url)
if "head_branch" in run_info:
    release_branch = run_info["head_branch"]
    commit_hash = run_info["head_sha"]
else:
    error_print(f"{run_html_url} is not valid!")
    sys.exit()

# Create tag
tag_data = {
    "accept": "application/vnd.github.v3+json",
    "owner": f"{DEST_OWNER}",
    "repo": f"{REPO}",
    "tag": release_tag,
    "message": f"create {release_tag}",
    "object": f"{commit_hash}", 
    "type": "commit",
    "tagger": {
        "name": lib_github.GH_USER,
        "email": lib_github.GH_EMAIL
    }
}

tag_resp = lib_github.create_tag(f"{DEST_OWNER}", f"{REPO}", tag_data)
tag_sha = tag_resp["sha"]

# Create reference
ref_data = {
    "accept": "application/vnd.github.v3+json",
    "owner": f"{DEST_OWNER}",
    "repo": f"{REPO}",
    "ref": f"refs/tags/{release_tag}",
    "sha": f"{tag_sha}"
}

ref_resp = lib_github.create_reference(f"{DEST_OWNER}", f"{REPO}", ref_data)

# Get artifacts info
status_print(f"Getting archives from {run_html_url}...")
r = gh.get(artefacts_url)

# Download artifacts
formatted_names = {}
for a in r.json()['artifacts']:
    if not a["name"].endswith('.zst'):
        artifact_zip_name = f"{a['name']}.zip"
        artifact_zip_url = a["archive_download_url"]
        project, formatted_name = get_formatted_name(artifact_zip_name)
        formatted_names.update({
            artifact_zip_name:formatted_name
        })
        release_name = f'{project.title().replace("dex", "DEX")} v{VERSION} beta'
        
        if not os.path.exists(artifact_zip_name):
            status_print(f"Downloading {artifact_zip_name}...")

            dl_command = f'wget -q --header="Authorization: token {lib_github.GH_TOKEN}" -O {artifact_zip_name} {artifact_zip_url}'
            args = shlex.split(dl_command)
            subprocess.run(args)

        else:
            status_print(f"{artifact_zip_name} already exists in this folder!")

# Repackage with extra files and formatted file names
for name in formatted_names:
    if os.path.exists(name):
        # Extract 
        with ZipFile(name, 'r') as za:
            extract_path = f"{SCRIPT_PATH}/temp_{formatted_names[name]}"
            za.extractall(extract_path)
            files = os.listdir(extract_path)
            # rename as required

            status_print(f"Repackaging as {formatted_names[name]}...")
            with ZipFile(f"{formatted_names[name]}", 'w') as zb:
                for file in os.listdir(extract_path):

                    new_name = get_new_name(file, formatted_names[name])

                    zb.write(filename=f"{extract_path}/{file}", arcname=new_name)
                    if f"{formatted_names[name]}".lower().find("appimage") > -1:
                        for extra_file in [
                                "README.txt",
                                "prerequisites.sh",
                                "make_executable.gif"
                            ]:
                            print(extra_file)
                            zb.write(extra_file)

        if formatted_names[name].endswith("portable.zip"):
            zipname = formatted_names[name].split(".zip")[0]
            os.rename(formatted_names[name], f"{zipname}_old.zip")
            print(f"unzip repackaging {zipname}")
            with ZipFile(f"{zipname}_old.zip", 'r') as zc:
                zc.extractall(f"{SCRIPT_PATH}")
            os.remove(f"{zipname}_old.zip")


        shutil.rmtree(f"{SCRIPT_PATH}/temp_{formatted_names[name]}")
    else:
        status_print(f"{formatted_names[name]} already exists in this folder!")

# Create Release data
release_body = "### Release Notes\n\n\
**Features:**\n\n\
**Enhancements:**\n\n\
**Fixes:**\n\n\
**Checksum & VirusTotal Analysis:**\n\n\
| Link   | SHA256      |\n\
|--------|-------------|"

# Get VirusTotal results
for name in formatted_names:
    status_print(f"Getting hash for {formatted_names[name]}")
    vt_hash = lib_virustotal.get_vt_hash(formatted_names[name])
    release_body = f"{release_body}\n| [{formatted_names[name]}](https://www.virustotal.com/gui/file/{vt_hash}) | `{vt_hash}` |"

# Create draft release
release_data = {
    "accept": "application/vnd.github.v3+json",
    "owner": f"{DEST_OWNER}",
    "repo": f"{REPO}",
    "tag_name": release_tag,
    "target_commitish": release_branch,
    "name": f"{release_name}", 
    "body": release_body,
    "draft": True,
    "prerelease": False
}

# Upload artifacts
if not lib_github.check_release_exists(release_name):
    table_print(f"Release name: {release_name}")
    table_print(f"Release tag: {release_tag}")
    table_print(f"Release branch: {release_branch}")
    release_info = lib_github.create_release(f"{DEST_OWNER}", f"{REPO}", release_data)
    if 'id' in release_info:
        release_id = release_info["id"]
        upload_url = release_info["upload_url"].replace("{?name,label}", "")

        for name in formatted_names:
            upload_data = {
                "accept": "application/vnd.github.v3+json",
                "owner": f"{DEST_OWNER}",
                "repo": f"{REPO}",
                "release_id": release_id,
                "name": formatted_names[name],
                "label": formatted_names[name]
            }
            params = (
              ('name', formatted_names[name]),
              ('label', formatted_names[name]),
            )
            status_print(f"Uploading {formatted_names[name]}...")

            # This is adding extra bytes and causing fails on mac archive utility
            # upload_reponse = lib_github.upload_release_asset(upload_url, upload_data, params, formatted_names[name])

            args = [
                'curl',
                '-H',
                'Accept: application/vnd.github.v3+json',
                '-H',
                f'Authorization: token {lib_github.GH_TOKEN}',
                '-H',
                'Content-Type: application/zip',
                '--data-binary',
                f'@{formatted_names[name]}',
                f'{upload_url}?name={formatted_names[name]}'
            ]
            subprocess.run(args)

            #os.system(f'curl -H "Accept: application/vnd.github.v3+json" -H "Authorization: token {lib_github.GH_TOKEN}" -H "Content-Type: $(file -b --mime-type {formatted_names[name]})" --data-binary @{formatted_names[name]} "{upload_url}?name=$(basename {formatted_names[name]})"')

    else:
        print(release_info)
