# QindaBoot

The graphical boot menu and boot splash of QindaQt machines, packaged as
`sys-boot/qinda-boot` in the QindaGentoo overlay.

- **Boot menu**: rEFInd with the QindaQt theme (the "reclaimed" palette and
  artwork of the SDDM greeter), installed in `EFI/qinda` on the EFI system
  partition and registered first in the firmware boot order. Each row is a
  *boot mode*; every mode boots the newest kernel, and its submenu (F2,
  Insert or Tab) offers a text boot without the splash and every older
  kernel. **Advanced** chains to systemd-boot, which stays installed as the
  firmware fallback.
- **Boot splash**: the `qindaqt` Plymouth theme (script plugin): the mark,
  a breathing halo and a progress bar, with captions for shutdown and
  restart and a passphrase field for encrypted volumes.

## Boot modes

A mode is a small file in `/usr/share/qinda-boot/modes.d` (installed by
packages) or `/etc/qinda-boot/modes.d` (local; the same file name replaces a
packaged mode, `DISABLED=yes` hides it):

```sh
TITLE="LLM Server"                                # menu caption
ICON="llm-server"                                 # theme icon os_<ICON>.png
OPTIONS="systemd.unit=qinda-llm-server.target"    # extra kernel arguments
```

QindaBoot ships `10-qindaqt.conf` (the desktop). `sci-ml/qinda-llm-server`
adds `50-llm-server.conf`. Nothing else is scanned: the menu never lists
other operating systems or removable media.

## Keeping the ESP current

`qinda-boot-sync` writes `EFI/qinda/{refind_x64.efi,refind.conf,entries.conf,theme/}`
from the kernels in `$ESP/loader/entries` (written by kernel-install) and the
modes above, touching only files whose contents changed. It runs:

- from kernel-install (`95-qinda-boot.install`) after every kernel change,
- from `pkg_postinst` when the package is updated,
- by hand after editing `/etc/qinda-boot/qinda-boot.conf` or a mode.

First deployment on a machine, as root:

```sh
emerge --config sys-boot/qinda-boot   # theme, ESP files, firmware boot entry
emerge --config sys-kernel/gentoo-kernel-bin   # initramfs with the splash
```

## Artwork

`tools/build_assets.py` draws everything under `share/` (1x for displays up to
1920 px wide, 2x above) from `art/reclaimed.png` and the QindaQt mark. The
outputs are committed so the package needs no build tools:

```sh
python3 tools/build_assets.py           # regenerate share/
make check                              # unit tests + share/ is current
```

rEFInd inverts its font over dark backgrounds, so the font strip is drawn in
black. Its own entry label reads "Boot <title> from <volume>", so the menu
hides it and each icon carries its caption.

## License and provenance

Original code authored for QindaBoot is released under the GNU General Public
License, version 3 or (at your option) any later version
(`GPL-3.0-or-later`). See [LICENSE](LICENSE) for the GPL version 3 text.
Third-party components retain their own licenses and notices.

The reused `art/reclaimed.png` wallpaper is the QindaQt Reclaimed artwork
identified in [QindaThemes artwork provenance](https://github.com/Es00bac/QindaThemes/blob/main/docs/ARTWORK.md).
It and the generated image/font assets retain their existing applicable terms;
this code license does not newly relicense artwork or fonts. The generator
uses separately installed Inter and IBM Plex Mono fonts; no font binaries are
bundled here. rEFInd and Plymouth retain their respective upstream licenses.
