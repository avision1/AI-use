# Preview4 normal UEFI live evidence

Observed on 2026-11-06 in `artifacts/uefi-live-001/`, controller session 55315. This session booted the original read-only ISO under authenticated normal OVMF, KVM, host CPU and plain 2D virtio-vga, with `q35,smm=off`. No disk or NIC was attached. Secure Boot was not requested. The controller completed with exit 0 and outcome `guest-exited` after direct guest `sudo poweroff`, without an additional Enter prompt.

ISO SHA256: `7d36b5847fba7240ee2795bb42ff3ea841652569b7eb983cfec6ea96968ae11c`. `run.json` retains the actual command and read-only ISO/CODE graph. `firmware-verification.json` records authentication against the firmware lock and cached `ovmf` package `2024.02-2ubuntu0.10`, package SHA256 `78a6a3a4ffa666f1cb25e9069e4ec9270b5ceac7987b6eefc2674bd3f58a1473`. The writable `uefi-vars.fd` is a fresh output-local copy of the authenticated 540672-byte template; the original template is not opened writable.

The parent operator observed these retained captures:

| Capture | Observation |
| --- | --- |
| `screen-0001.ppm` | UEFI GRUB menu after actual OVMF startup. |
| `screen-0003.ppm` | Default live Plasma desktop with configured wallpaper, bottom panel and welcome window. |
| `screen-0005.ppm` | Guest terminal reports `UEFI_BOOT_CONFIRMED` after testing `/sys/firmware/efi`, `SESSION=wayland`, root filesystem type `overlay`, and zero failed systemd units. |
| `screen-0006.ppm` | Running `windows12-welcome` as the normal user opens `file:///usr/local/share/windows12/welcome.html` in Firefox, displaying the local offline guide. An extra first-run offline “Problem Loading Page” tab does not establish failure of the local guide. |

The final result reports `firmware_inputs_unchanged=true`, without setup, cleanup or firmware errors. The final output-local VARS file is 540672 bytes, SHA256 `4428c124743be542a4a85c5852f2aff5345c6b9c8bfc6959a1d73496cc44f814`.

This establishes actual normal UEFI live boot and visible Wayland desktop in this contained VM profile. It does not establish UEFI installation, ISO-free UEFI disk boot, Secure Boot or physical-device compatibility. All automatic controller verification flags remain false; the runtime observations are separate evidence.

Separate source validation completed successfully in `artifacts/overlay-check-1c5ce6050a112c056f393ef804426e5e/`: 87 guest tests, deterministic package/dpkg checks and shutdown, source archive SHA256 `1ff780bdf3f646fded697968b8edf4a880e2cc8630c4987d9324f615b64ac419`. That archive excludes the later seven-file builder integration. A fresh contained source check, session 47507, is active with all seven newer builder files and ten additional guest tests; its result remains pending. Source checks do not change the original ISO bytes.

Next gates are successful validation of the newer builder source, a fresh build with the reviewed clock fix, then an actual contained UEFI Calamares installation followed by ISO-free disk boot with preserved final NVRAM and installed desktop evidence. UEFI manual continuation has not yet been exercised.
