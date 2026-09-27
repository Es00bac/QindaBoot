"""qinda-boot-sync against a throwaway ESP: parsing, rendering, idempotence."""

import importlib.machinery
import importlib.util
import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def load_sync(share: Path, etc: Path):
    os.environ["QINDA_BOOT_SHARE"] = str(share)
    os.environ["QINDA_BOOT_ETC"] = str(etc)
    loader = importlib.machinery.SourceFileLoader("qinda_boot_sync", str(ROOT / "sbin/qinda-boot-sync"))
    spec = importlib.util.spec_from_loader("qinda_boot_sync", loader)
    module = importlib.util.module_from_spec(spec)
    sys.modules["qinda_boot_sync"] = module
    loader.exec_module(module)
    return module


ENTRY = """# Boot Loader Specification type#1 entry
title      Gentoo Linux
version    {ver}
options    root=UUID=abcd rw systemd.machine_id=0123
linux      /0123/{ver}/linux
initrd     /0123/{ver}/initrd
"""


class SyncTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        base = Path(self.tmp.name)
        self.esp, self.share, self.etc = base / "esp", base / "share", base / "etc"
        (self.esp / "loader/entries").mkdir(parents=True)
        for ver in ("6.18.9-gentoo-dist-bin", "6.18.48-gentoo-dist-bin"):
            (self.esp / f"loader/entries/0123-{ver}.conf").write_text(ENTRY.format(ver=ver))
        (self.share / "modes.d").mkdir(parents=True)
        (self.share / "modes.d/10-qindaqt.conf").write_text((ROOT / "modes.d/10-qindaqt.conf").read_text())
        (self.share / "modes.d/50-llm-server.conf").write_text(
            'TITLE="LLM Server"\nICON="llm-server"\nOPTIONS="systemd.unit=qinda-llm-server.target"\n')
        (self.share / "refind").symlink_to(ROOT / "share/refind")
        (self.etc / "modes.d").mkdir(parents=True)
        self.sync = load_sync(self.share, self.etc)

    def tearDown(self):
        self.tmp.cleanup()

    def test_kernels_newest_first(self):
        kernels = self.sync.load_kernels(self.esp)
        self.assertEqual([k.version for k in kernels],
                         ["6.18.48-gentoo-dist-bin", "6.18.9-gentoo-dist-bin"])

    def test_modes_ordered_and_overridable(self):
        (self.etc / "modes.d/50-llm-server.conf").write_text("DISABLED=yes\n")
        self.assertEqual([m.ident for m in self.sync.load_modes()], ["qindaqt"])

    def test_entries_carry_mode_options_and_submenus(self):
        modes = self.sync.load_modes()
        kernels = self.sync.load_kernels(self.esp)
        text = self.sync.render_entries(modes, kernels, "quiet splash", self.esp)
        self.assertIn('menuentry "LLM Server"', text)
        self.assertIn("systemd.unit=qinda-llm-server.target", text)
        self.assertIn('submenuentry "Kernel 6.18.9-gentoo-dist-bin"', text)
        self.assertIn('submenuentry "Text boot (no splash)"', text)
        self.assertNotIn("Advanced", text)          # no systemd-boot on this ESP
        head = text.split('menuentry "LLM Server"')[1]
        self.assertIn("loader  /0123/6.18.48-gentoo-dist-bin/linux", head)

    def test_systemd_boot_auto_entries(self):
        conf = self.esp / "loader/loader.conf"
        conf.write_text("timeout 3\nauto-entries yes\n")
        writer = self.sync.Writer(dry_run=False)
        self.sync.systemd_boot_auto_entries(self.esp, "no", writer)
        self.assertEqual(conf.read_text(), "timeout 3\nauto-entries no\n")
        writer = self.sync.Writer(dry_run=False)
        self.sync.systemd_boot_auto_entries(self.esp, "no", writer)
        self.assertEqual(writer.changed, [])

    def test_second_run_changes_nothing(self):
        self.sync.REFIND_EFI = ROOT / "tests/fake-refind.efi"
        self.sync.REFIND_EFI.write_bytes(b"MZ fake")
        try:
            for expected_change in (True, False):
                writer = self.sync.Writer(dry_run=False)
                target = self.esp / self.sync.ESP_DIR
                writer.copy(self.sync.REFIND_EFI, target / "refind_x64.efi")
                writer.tree(self.share / "refind/1x", target / "theme")
                writer.text(target / "entries.conf", self.sync.render_entries(
                    self.sync.load_modes(), self.sync.load_kernels(self.esp), "", self.esp))
                self.assertEqual(bool(writer.changed), expected_change)
        finally:
            self.sync.REFIND_EFI.unlink()


if __name__ == "__main__":
    unittest.main()
