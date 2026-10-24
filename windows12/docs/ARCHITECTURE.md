# Architecture investigation

Research date: 2026-10-23 (America/Chicago). This document records engineering choices, not completed product capabilities. See PROJECT_STATE.md for actual build and test results.

## Recommended first milestone

Use an amd64 Debian 13 KDE live installation image as the first derivative substrate. Preserve the upstream boot chain, package database, installer and update channels. Add a small project-owned filesystem overlay for desktop defaults, application launchers, and local compatibility/help content. Execute any package installation, image preparation and runtime validation inside an isolated VM or equivalent contained environment with writable storage under windows12. If isolation cannot be established, stop the affected operation and record a blocker.

This is an installable Linux derivative, not an implementation of Windows NT, a universal Windows binary runtime, or a browser mockup. The working project name reflects the requested experience; public UI must identify independent Linux software and avoid implying Microsoft authorship.

Debian explicitly offers an amd64 KDE live image with Calamares installation from the live system [A1]. Its trixie release page currently reports Debian 13.7, released 2026-09-12 [A2]. Do not resolve a moving “latest” image without recording its exact URL, size and authenticated checksum.

## Options assessed

| Option | Evidence and strengths | Engineering consequence |
|---|---|---|
| Debian 13 KDE live derivative | Official live KDE image and Calamares; Debian 13 support timeline is documented [A1,A2]. | Recommended for a small initial overlay and conservative base. Validate all inherited behavior after customization. |
| Kubuntu 26.04 LTS | Released 2026-04-23; project promises fixes through April 2029 [A3]. | Credible alternative with Ubuntu packaging. Switching would require revalidating image construction, branding, defaults and installer. |
| Fedora KDE | Fedora describes approximately 13 months of updates per release [A4]. | Attractive newer desktop stack; higher release-upgrade cadence than desired for the first conservative baseline. |
| Fresh desktop/kernel or Windows API reimplementation | No evidence that this is needed to satisfy the familiar-workflow requirement. | Would consume effort recreating working upstream components. Keep customization small and improve measured gaps. |

The recommendation is an engineering inference from upstream facilities and maintenance scope, not a claim that Debian has the best Windows application compatibility. Compatibility depends on each application, runtime, device and version.

## Component boundaries

| Component | Initial implementation direction | Acceptance before release |
|---|---|---|
| Kernel, firmware, bootloader, installer | Inherit upstream Debian live-image components. | UEFI and BIOS boot; Calamares installation to a disposable virtual disk; reboot installed disk without ISO. |
| Desktop | Plasma, bottom panel, launcher, pinned applications, tray, clock and familiar file/settings entry points. Use documented Plasma scripting/configuration [A5]. | First login and second login; no duplicate panels; user changes persist; keyboard and multi-monitor smoke checks. |
| Office | Explicit web launchers; retain an available offline office suite as an alternative. | Signed-out navigation, account sign-in, create/edit/save/export sample Word/Excel/PowerPoint documents; disclose web limitations. |
| Windows applications | Evaluate Wine and managed prefixes later; no blanket “EXE support” statement. | Record exact app/version/runtime and reproducible functional tests, including uninstall. |
| Updates | Retain upstream package identity/update sources; keep project overlay versioned. | Updates work after installation; security update process and overlay upgrade/recovery tested. |
| Build reproducibility | Pin signed input images and project revision; record tools, commands, manifests and output digests. | Repeated build procedure works; distinguish repeatable inputs from byte-identical ISO output. |

A remastered base ISO is a bootstrap milestone. Long-term source-built releases should move to a pinned live-build configuration after the first install/reboot tests. Do not call an unexecuted recipe a built distribution.

## Release gates

1. Input authenticity and checksum validation, source/license manifest and overlay review.
2. Contained image build with logs and output checksum; no host package installs, mounts or writes outside the boundary.
3. Boot to usable desktop; inspect logs; exercise file manager, settings, network, audio and web launchers.
4. Install to project-contained disposable disk, reboot, create another user and apply updates.
5. Report tested hardware and known failures. Secure Boot, GPU, Wi-Fi, Bluetooth, printing, suspend, accessibility and non-English input require separate verification; inherited support is not derivative certification.

## Primary sources

- [A1] Debian, Live install images: https://www.debian.org/CD/live/ (accessed 2026-10-23).
- [A2] Debian, trixie release information: https://www.debian.org/releases/trixie/ (accessed 2026-10-23).
- [A3] Kubuntu, 26.04 LTS release notes, published 2026-04-23: https://kubuntu.org/news/kubuntu-26-04-release-notes/ (accessed 2026-10-23).
- [A4] Fedora, KDE Plasma Desktop: https://fedoraproject.org/kde/ (accessed 2026-10-23).
- [A5] KDE, Plasma Desktop scripting: https://develop.kde.org/docs/plasma/scripting/ (accessed 2026-10-23).
