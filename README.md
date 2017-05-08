YouTube Collaborative Playlist
==============================

## setup (ubuntu)

```sh
sudo apt install build-essential python3-dev python3-venv libmpv-dev mpv
python3 -m venv venv
. venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
wget -O mpv.py https://raw.githubusercontent.com/jaseg/python-mpv/master/mpv.py
```

## config

Set a password in `ytcp.cfg`

```sh
echo 'PASS = "music"' >> ytcp.cfg
```

## running

There can only be one instance running, because each process will spawn a separate media player. For most uses it is probalby OK to use the built in flask server (probably).

```sh
env FLASK_APP=ytcp.py flask run --host=0.0.0.0
```
