A simple script to translate AtomicDEX-Desktop CI artefacts from Github Actions into a draft release with VirusTotal results.

![image](https://user-images.githubusercontent.com/35845239/148229576-738c2b62-65c0-46fc-b969-fd9aa21d5967.png)

## Setup

- Run `pip3 install -r requirements.txt`
- Create a `.env` file, and enter values for `VIRUSTOTAL_API_KEY`, `GH_TOKEN`, `GH_USER` and `GH_EMAIL`

## Usage

- Run `./draft_release.py`
- Input a valid Github Actions run number (e.g. `1647045169`)
- Input a release version (e.g. `0.5.x`)
- Input repo (e.g. `AtomicDEX-desktop`)
- Input org to download artifacts from (e.g. `KomodoPlatform`)
- Input org to upload artifacts to (e.g. `smk762`)

## Todo

- Add tests
