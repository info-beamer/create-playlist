#!/usr/bin/env python2.7
#
# Copyright (c) 2014,2015 Florian Wesch <fw@dividuum.de>
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
#
#     Redistributions of source code must retain the above copyright
#     notice, this list of conditions and the following disclaimer.
#
#     Redistributions in binary form must reproduce the above copyright
#     notice, this list of conditions and the following disclaimer in the
#     documentation and/or other materials provided with the
#     distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS
# IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
# THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
# PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
# CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
# PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
import os
import re
import sys
import errno
import tarfile
import json
import subprocess
import hashlib
from cStringIO import StringIO
from collections import namedtuple

DATA="""
%%%DATA%%%
"""

if len(DATA) < 100:
    print "Do not run this python program directly. Run 'make' to build"
    print "a distributable version. Inside the build/ directory you'll"
    print "find the tar.gz you can use and distribute."
    print
    print "Have a look at README.md to learn more."
    sys.exit(1)

class InstallError(Exception): pass

def probe_image(item):
    if not os.path.exists(item.source):
        raise InstallError("Image %s does not exist" % item.source)
    if 'time' in item.metadata:
        return item.metadata['time']
    return 10

def probe_video(item):
    if not os.path.exists(item.source):
        raise InstallError("Video %s does not exist" % item.source)
    if 'time' in item.metadata:
        return item.metadata['time']
    try:
        output = subprocess.Popen(
            ["avprobe", item.source],
            stderr = subprocess.PIPE,
            stdout = file("/dev/null", "wb")
        ).stderr.read()
    except Exception:
        raise InstallError("Cannot start avprobe: %s. Please have a look at README.txt" % err)
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
    ".mov": ResourceType("video", probe_video),
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

def get_extension(filename):
    _, extension = os.path.splitext(filename)
    return extension

PlayListItem = namedtuple("PlayListItem", "filename asset_name source metadata")

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

    def parse_metadata(line):
        extracted = {}
        def parse_time(val):
            try:
                return float(val)
            except ValueError:
                raise InstallError("Invalid value for time: %s" % val)
        known_meta = {
            'time': parse_time,
        }
        def found_meta(m):
            meta, val = m.groups()
            if not meta in known_meta:
                raise InstallError("Unknown meta type %s" % meta)
            extracted[meta] = known_meta[meta](val)
            return ''
        return re.sub(" ([a-z]+):([^ ]+)", found_meta, line).strip(), extracted

    items = []
    with file(playlist_filename, "rb") as inf:
        for line in inf:
            filename = line.strip()
            filename, metadata = parse_metadata(filename)
            if not filename or filename.startswith('#'):
                continue
            items.append(PlayListItem(
                filename = os.path.basename(filename),
                asset_name = hashlib.md5(filename).hexdigest() + get_extension(filename),
                source = os.path.join(playlist_dir, filename),
                metadata = metadata,
            ))

    for item in items:
        extension = get_extension(item.filename)
        resource_type = RESOURCE_TYPES.get(extension.lower())
        if resource_type is None:
            raise InstallError("File extension %s not supported" % extension)

        duration = resource_type.probe(item)
        playlist.append(dict(
            file = dict(
                type = resource_type.type,
                filename = item.filename,
                asset_name = item.asset_name,
            ),
            duration = duration
        ))

    with file(os.path.join(target, "config.json"), "wb") as outf:
        outf.write(json.dumps(config_json, indent=4))

    for item in items:
        target_filename = os.path.join(target, item.asset_name)

        if os.path.exists(target_filename) and not os.path.islink(target_filename):
            raise InstallError("File %s exists but is not a symlink. refusing to delete it" %
                    target_filename)

        if os.path.islink(target_filename) and os.readlink(target_filename) != item.source:
            os.unlink(target_filename)

        try:
            os.symlink(item.source, target_filename)
        except OSError, err:
            if err.errno != errno.EEXIST:
                raise

if __name__ == "__main__":
    print "create-playlist version %%%VERSION%%%. A play list node generator for info-beamer."
    print "Source code is available on https://github.com/info-beamer/create-playlist"
    print
    if len(sys.argv) != 3:
        print "%s <playlist> <target_directory>" % sys.argv[0]
        sys.exit(1)
    playlist, target = sys.argv[1:]
    try:
        make_dir(target)
        build_playlist(target, playlist)
        extract_data(target)
    except InstallError, err:
        print "Installation failed: %s" % err
        sys.exit(1)
    else:
        print "Node directory %s ready. Now start info-beamer like this:\ninfo-beamer %s" % (target, target)
