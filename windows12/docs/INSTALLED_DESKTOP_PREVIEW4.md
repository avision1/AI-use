# Preview4 installed desktop evidence

Observed on 2026-11-06 in `artifacts/installed-desktop-virtio-001/`, controller session 51793. This is an actual installed-disk graphical boot, with no ISO attached and no network. Guest `sudo poweroff` completed; controller exited0 with guest-exited, baseline_unchanged=true and no cleanup/baseline error.

The source ISO is `artifacts/vm-build/windows12-amd64-preview.iso`, SHA256 `7d36b5847fba7240ee2795bb42ff3ea841652569b7eb983cfec6ea96968ae11c`. Installation provenance is `artifacts/install-passstdout-001/result.json`, SHA256 `8d249b730b785c4235c719d5ab2f036184c40c92574761556001fe0a01f0d675`. The sealed baseline SHA256 is `58bcaea9b07c88797ac80fd8aed126862a1459561d061763a94764fecf74ffad`.

`run.json` records BIOS, KVM, host CPU, two virtual CPUs, 4096 MiB RAM and plain 2D virtio-vga. Its block graph explicitly opens the stopped installation baseline read-only and places writes in a new `installed-desktop.qcow2` child. There is no CD device. This successful profile does not establish the cause of the earlier TCG/standard-VGA failures.

The parent operator observed these retained captures:

| Capture | Observation |
| --- | --- |
| `screen-0001.ppm` | SDDM login for the public test account `testuser`, selecting the default Wayland session. |
| `screen-0002.ppm` | Visible default Plasma Wayland desktop, configured blue SVG wallpaper, bottom 48 px panel, pinned application icons and system tray. |
| `screen-0006.ppm` | Application menu responds to interaction. |
| `screen-0007.ppm` | Terminal reports `SESSION=wayland`, root filesystem `/dev/vda1`, and zero failed systemd units. Installed versions: Chromium `156.0.8078.79-1~deb13u1`, LibreOffice Writer `4:25.2.3-2+deb13u8`, Plasma workspace `4:6.3.6-2`, Windows12 desktop `0.1.0~preview4`. |
| `screen-0011.ppm` | Kate displays the renamed public test file `renamed.txt`. An initially duplicated filename extension was operator input, corrected with Ctrl+A. |
| `screen-0016.ppm`, `screen-0017.ppm` | Idle screen lock and successful unlock. A controller input approval timeout was not a guest failure. |
| `screen-0018.ppm` | Direct `libreoffice --writer` from Konsole launches Writer. An earlier Alt+F2 attempt unexpectedly opened Discover; that does not establish a missing Writer binary. |
| `screen-0019.ppm`, `screen-0025.ppm`, `screen-0027.ppm` | Writer Save dialog selects Word 2010–365 DOCX, followed by format confirmation. |
| `screen-0031.ppm` | Reopened `desktop-check.docx` displays both test text lines intact. |
| `screen-0034.ppm`, `screen-0035.ppm` | Logout reaches SDDM; login returns to Wayland with the same wallpaper and panel, without duplicate widgets. |
| `screen-0037.ppm` | Terminal confirms the edited 72-byte text file and DOCX hash. |

Public test files were exported from the guest as a tar archive encoded in base64 through serial frames marked `W12_QA`; extracted files and checked manifest are retained under `artifacts/installed-desktop-virtio-001/public-files/`. Guest sudo authorization worked for this export. The 5121-byte DOCX SHA256 is `8642d21f06dcea1d7f22b8b4d900e973ea6f905cf902a6573cce925ac6b96d5e`; its ZIP member `word/document.xml` contains both test text lines. The 72-byte `renamed.txt` SHA256 is `ccf7c5a0ed35d101b03922401252a96d55240816651356d390eec13f52227a0d`.

These observations establish installed boot, visible login, a responding Windows-style desktop, lock/unlock, logout/login and a basic Writer DOCX save/reopen in this contained VM profile. This is a partial Writer check, not the full Office fixture suite, PDF export or Microsoft application compatibility. The controller's automatic verification flags remain false; do not rewrite them from this narrative.

Pending release checks:

- Complete Dolphin, Chromium, Discover and offline Welcome workflows and graphical administration prompts. Extend Writer testing to the full document fixtures and PDF export. Microsoft 365 web workflows additionally require network and an eligible account.
- Verify saved files and settings after a subsequent disk boot; logout/login persistence alone does not establish reboot persistence.
- Final session reconciliation PASSED: guest-exited, QEMU return0, baseline_unchanged=true, no setup/cleanup/baseline error. Automatic boot/login/install/workflow flags remainfalse by design; manually reviewed observations above are separate evidence. The fresh Calamares VM is now the sole active guest.
- Exercise the actual Calamares GUI installation path, inspect its disk summary, and repeat ISO-free boot and desktop checks for that installation. The current evidence comes from the automated Debian Installer path.
- Test UEFI boot and installation separately. BIOS success does not certify UEFI, Secure Boot, USB-media writing or physical-device compatibility.
