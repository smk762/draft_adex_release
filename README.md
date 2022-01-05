A simple script to translate CI archives from Github Actions into a draft release with VirusTotal results.

![image](https://user-images.githubusercontent.com/35845239/148229576-738c2b62-65c0-46fc-b969-fd9aa21d5967.png)

## Setup

- Run `pip3 install -r requirements.txt`
- Create a `.env` file, and enter values for `VIRUSTOTAL_API_KEY`, `GH_TOKEN` and `GH_USER`

## Usage

- Run `./draft_release.py`
- Input a valid Github Actions run number (e.g. `1647045169`)
- Input a release version (e.g. `0.5.x`


## Todo

- Create tag matching release
- Add tests
