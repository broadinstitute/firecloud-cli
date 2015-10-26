# firecloud-cli
Command line tools for Firecloud

## Installation Instructions for Linux/OSX
The FireCloud CLI requires:
* Python 2.7+
* Pip (run `sudo easy_install pip`)
* Virtualenv (run `sudo pip install virtualenv`)
* Google Cloud SDK (see https://cloud.google.com/sdk/)

To install run `./install.sh` and follow the instructions to add ~/.firecloud-cli/venv/bin to your default path

## Usage

After installation run `firecloud` for usage

## Dockerized Version

No installation necessary. Run:
```bash
docker run --rm -it -v "$HOME"/.config:/.config broadinstitute/firecloud-cli gcloud auth login
```

then:
```bash
docker run --rm -it -v "$HOME"/.config:/.config broadinstitute/firecloud-cli firecloud --help
```

for usage. To read/write files from your current directory, be sure to mount it:
```bash
docker run --rm -it -v "$HOME"/.config:/.config -v "$PWD":/working broadinstitute/firecloud-cli firecloud -m push my-file.wdl
```
