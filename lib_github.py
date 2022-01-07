#!/usr/bin/env python3
import os
import json
import requests
from dotenv import load_dotenv
from lib_color import *

load_dotenv()


# from https://github.com/user/settings/tokens
GH_USER = os.getenv('GH_USER')
GH_EMAIL = os.getenv('GH_EMAIL')
GH_TOKEN = os.getenv('GH_TOKEN')


gh = requests.Session()
gh.auth = (GH_USER, GH_TOKEN)
base_url = "https://api.github.com"


def get_recent_user_activity(username):
    return requests.get(f"{base_url}/users/{username}/events/public?per_page=100").json()


def get_recent_repo_activity(org, repo):
    return requests.get(f"{base_url}/repos/{org}/{repo}/events?per_page=100").json()



def summarise_activity_by_repo(activity=None):
    summary = {}
    for event in activity:
        event_type = event["type"]
        repo = event["repo"]["name"]


def check_release_exists(release_name):
    r = gh.get(f"{base_url}/repos/smk762/atomicDEX-Desktop/releases").json()
    # name
    # body
    # tag_name
    # target_commitish (branch)
    # "draft" True
    for release in r:
        if release["name"] == release_name:
            status_print(f"A release with the name '{release_name}' already exists at {release['html_url']}!")
            return True
    return False


# https://docs.github.com/en/rest/reference/releases#create-a-release
def create_release(owner, repo, data):
    url = f"{base_url}/repos/{owner}/{repo}/releases"    
    r = gh.post(url, data=data)
    if 'html_url' in r.json():
        success_print(f"Draft release created at {r.json()['html_url']}")
    else:
        error_print("Error creating release!")
        error_print(data)
        error_print(r.json())
    return r.json()

# https://docs.github.com/en/rest/reference/releases#upload-a-release-asset
def upload_release_asset(upload_url, upload_data):
    r = gh.post(upload_url, data=upload_data)
    return r.json()


def get_run_info(run_url):
    r = requests.get(f"{run_url}")
    return r.json()


# https://docs.github.com/en/rest/reference/git#create-a-tag-object
def create_tag(owner, repo, data):
    url = f"{base_url}/repos/{owner}/{repo}/git/tags"
    r = gh.post(url, data=data)
    return r.json()



# https://docs.github.com/en/rest/reference/git#create-a-reference
def create_reference(owner, repo, data):
    url = f"{base_url}/repos/{owner}/{repo}/git/refs"
    r = gh.post(url, data=data)
    return r.json()



