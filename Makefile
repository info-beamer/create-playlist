VERSION = $(shell git rev-parse --short=6 HEAD)

release: build.py README-build.txt main.py
	rm -rf build
	mkdir -p build/playlist-$(VERSION)
	python build.py $(VERSION) data main.py build/playlist-$(VERSION)/create-playlist
	chmod 755 build/playlist-$(VERSION)/create-playlist
	ln COPYRIGHT example-playlist.txt build/playlist-$(VERSION)
	ln README-build.txt build/playlist-$(VERSION)/README.txt
	tar cfz build/create-playlist-$(VERSION).tar.gz -C build playlist-$(VERSION)
	ls -l build/*.gz

clean:
	rm -rf build

.PHONY: clean
