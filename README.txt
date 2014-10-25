Simple tool for creating playlist nodes for info-beamer
=======================================================

Installation
------------

Make the script create_playlist executable:

  $ chmod +x create_playlist

Install the package libav-tools:

  $ apt-get install libav-tools

You should be ready to go.

How to use?
-----------

Create a file called (for example) playlist.txt. Each line
specifies a media file to play. Empty lines or lines starting
with # are skipped. An example playlist.txt might look like
this:

videos/1.mp4
/home/foo/foo.jpg
/home/foo/bar.jpg
/home/foo/foo.jpg

Supported file formats are:

 * JPEG - max size is 2048x2048
 * PNG - max size is 2048x2048
 * MP4 - only H264 supported

Call the script create_playlist like this to create an 
info-beamer node in the directory /tmp/playlist:

 $ ./create_playlist playlist.txt /tmp/playlist

This will create a ready-to-use info-beamer node directory
in /tmp/playlist. Now start info-beamer like this:

 $ info-beamer /tmp/playlist
