# QindaBoot: install layout used by sys-boot/qinda-boot.
PREFIX  ?= /usr
SYSCONF ?= /etc
DESTDIR ?=

SHARE    = $(DESTDIR)$(PREFIX)/share/qinda-boot
PLYMOUTH = $(DESTDIR)$(PREFIX)/share/plymouth/themes/qindaqt

.PHONY: all install check test

all:

install:
	install -Dm755 sbin/qinda-boot-sync $(DESTDIR)$(PREFIX)/sbin/qinda-boot-sync
	install -Dm755 kernel-install/95-qinda-boot.install \
		$(DESTDIR)$(PREFIX)/lib/kernel/install.d/95-qinda-boot.install
	install -Dm644 etc/qinda-boot.conf $(DESTDIR)$(SYSCONF)/qinda-boot/qinda-boot.conf
	install -dm755 $(SHARE)/modes.d
	install -m644 modes.d/*.conf $(SHARE)/modes.d/
	for scale in 1x 2x; do \
		install -dm755 $(SHARE)/refind/$$scale/icons; \
		install -m644 share/refind/$$scale/*.png $(SHARE)/refind/$$scale/; \
		install -m644 share/refind/$$scale/icons/*.png $(SHARE)/refind/$$scale/icons/; \
	done
	install -dm755 $(PLYMOUTH)
	install -m644 plymouth/qindaqt/qindaqt.plymouth plymouth/qindaqt/qindaqt.script $(PLYMOUTH)/
	install -m644 share/plymouth/qindaqt/*.png $(PLYMOUTH)/

check: test
	python3 tools/build_assets.py --check

test:
	python3 -m unittest discover -s tests -p 'test_*.py'
