#!/usr/bin/env python2.7
import os
import re
import sys
import errno
import tarfile
import json
import subprocess
from cStringIO import StringIO
from collections import namedtuple

DATA="""
$$$DATA$$$
"""

class InstallError(Exception): pass

def probe_image(item):
    return 10

def probe_video(item):
    output = subprocess.Popen(
        ["avprobe", item.source], 
        stderr = subprocess.PIPE, 
        stdout = file("/dev/null", "wb")
    ).stderr.read()
    duration = re.search("Duration: ([0-9]+):([0-9]+):([0-9]+).([0-9]+),", output)
    if duration is None:
        raise InstallError("Cannot use 'avprobe' to find duration of video: %s" % output)
    hours, minutes, seconds, hundreds = map(int, duration.groups())
    return hours * 3600 + minutes * 60 + seconds + hundreds * 0.01

ResourceType = namedtuple("ResourceType", "type probe")

RESOURCE_TYPES = {
    ".jpg": ResourceType("image", probe_image),
    ".png": ResourceType("image", probe_image),
    ".mp4": ResourceType("video", probe_video),
}

def make_dir(target):
    try:
        os.makedirs(target)
    except OSError, err:
        if err.errno != errno.EEXIST:
            raise

def extract_data(target):
    with tarfile.open(mode='r:gz', fileobj=StringIO(DATA.decode("base64"))) as tar:
        tar.extractall(target)

PlayListItem = namedtuple("PlayListItem", "filename source")

def build_playlist(target, playlist_filename):
    config_json = dict(
        background_color = dict(
            r=0, g=0, b=0, a=1,
        ),
        fade = "crossfade",
        switch_time = 2,
        show_title = False,
        title_size = 20,
        title_duration = 3,
        title_font = dict(
           asset_name = "silkscreen.ttf"
        ),
        playlist = []
    )
    playlist = config_json['playlist']

    playlist_dir = os.path.abspath(os.path.dirname(playlist_filename))

    items = []
    with file(playlist_filename, "rb") as inf:
        for line in inf:
            filename = line.strip()
            if not filename or filename.startswith('#'):
                continue
            items.append(PlayListItem(
                filename = os.path.basename(filename),
                source = os.path.join(playlist_dir, filename)
            ))

    for item in items:
        _, extension = os.path.splitext(item.filename)
        resource_type = RESOURCE_TYPES.get(extension.lower())
        if resource_type is None:
            raise InstallError("file extension %s not supported" % extension)

        duration = resource_type.probe(item)
        playlist.append(dict(
            file = dict(
                type = resource_type.type,
                asset_name = item.filename,
            ),
            duration = duration
        ))

    with file(os.path.join(target, "config.json"), "wb") as outf:
        outf.write(json.dumps(config_json, indent=4))

    for item in items:
        target_filename = os.path.join(target, item.filename)
        try:
            os.symlink(item.source, target_filename)
        except OSError, err:
            if err.errno != errno.EEXIST:
                raise

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print "%s <playlist> <target_directory>" % sys.argv[0]
        sys.exit(1)
    playlist, target = sys.argv[1:]
    make_dir(target)
    build_playlist(target, playlist)
    extract_data(target)
    print "Node directory %s ready. Now start info-beamer like this:\ninfo-beamer %s" % (target, target)
