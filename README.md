A simple script to translate CI archives from Github Actions into a draft release with VirusTotal results.


## Setup

- Run `pip3 install -r requirements.txt`
- Create a `.env` file, and enter values for `VIRUSTOTAL_API_KEY`, `GH_TOKEN` and `GH_USER`

## Usage

- Run `./draft_release.py`
- Input a valid Github Actions run number (e.g. `1647045169`)
- Input a release version (e.g. `0.5.x`


## Todo

- Create tag matching release
