# Project state
Milestone M1: contained Debian 13 amd64 KDE live-build VM and initial desktop integration. Not a released OS yet.
Repository: avision1/AI-use, branch main. Latest synchronized checkpoint before this change: d987c2cf133a20a3cf49d7c8c79744c768097665 (GitHub connector; native push has no credentials). Always push directly main, only windows12 paths. Local pre-sync commit 5edbd90 is superseded by equivalent remote checkpoint, retained in reflog.
Absolute project: /workspace/scratch/3c38ab731138/AI-use/windows12. Root README/LICENSE intentionally not materialized; apparent deletions are unrelated and must not be staged.
Implemented: six persistent memory files; primary-source architecture/options/compatibility matrix; Python Office web allowlist launcher and offline welcome; desktop menu entries; KDE new-user double-click/Breeze defaults; first-login taskbar/pins/wallpaper script. GUI not yet verified.
Build tools: agent developing project-local QEMU package bootstrap plus full-VM live-build. All package installs happen in contained VM disks, never host. Source image/ is target filesystem overlay.
Validation so far: repository and boundary inspection; Git staged whitespace check passed initial memory checkpoint. No runtime or image tests yet. Agent writing tests/test_overlay.py for VM execution.
Environment: ~30 GiB initial free, no /dev/kvm. Native bwrap fails process namespace lookup, unshare user mapping denied, Landlock ENOSYS. QEMU must use TCG. Debian HTTPS/public Git fetch work. Proxy loopback ports change per exec; derive from current environment, never hardcode.
Running work: build agent bootstrap/probe (inspect .work and artifacts logs before restart); research agent tests. No ISO or installed-system test yet.
Next: complete QEMU probe, run overlay tests inside guest, build image, boot/install disposable virtual disk. Record precise blocker if VM unavailable.
