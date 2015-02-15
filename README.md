Simple tool for creating playlist nodes for info-beamer
=======================================================

This directory contains everything needed to build a
self contained tool that you can use to create play
lists for info-beamer.

Building the tool
-----------------

Run 

    $ make

This will create a tar.gz file in the directory `build`.
This file can be distributed. When unpacked it contains
a single python program that can be used to create a
directory that instructs info-beamer to play a play list.

See the `README.txt` file in the distributable file on
how to use the create-playlist tool.
