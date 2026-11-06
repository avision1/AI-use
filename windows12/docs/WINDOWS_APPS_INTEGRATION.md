# Optional Windows Applications entry

The source now provides one application-menu entry and a small Python standard-library launcher. This is a future image candidate; it does not change the retained frozen preview2 build, install a Wine runtime, or establish tested Windows application compatibility. The next package version must identify its changed payload separately.

## Behavior

- A regular user with Bottles already installed opens it directly. The launcher queries the user Flatpak scope first, then the default system scope, and runs the exact scope that answered successfully. A user installation takes precedence over a system installation. Custom named system installations are not discovered by this first prototype.
- Without an installed Bottles package, it opens an offline setup guide in the normal browser. The guide links to the official Bottles installation site and the HTTPS Flathub package page. It explains opening the Flatpak reference in Discover, reviewing source/permissions/download size and then returning to the menu entry. It does not rely on an `appstream://` link or assume a remote is already configured.
- The entry never adds a Flatpak remote, starts an installation, invokes a shell, changes file associations, accepts an arbitrary command, executes an installer or silently downloads a runtime. All installation decisions remain in the existing upstream installer/software-center flow. Ordinary runtime/component downloads are performed by Bottles only after the user sets it up.
- The page explains network and disk costs without inventing a size promise. It distinguishes application-specific Wine compatibility from untested native Office support and retains native Linux/LibreOffice/web alternatives. It identifies Wine as a compatibility layer, not a security boundary.
- Root execution and command-line installer arguments are refused. No `.exe`/`.msi` MIME handler is registered until real file forwarding and bottle selection are validated.

The setup page is bounded to 64 KiB and replaces a single `windows-apps.html` cache file. Cache ancestry must consist of real directories; the final directory must be owned by the current user and not group/world-writable. Temporary files are exclusive mode0600, accessed through a no-follow directory descriptor and atomically renamed. The launcher does not follow an existing destination symlink. A cache failure falls back to the official HTTPS Bottles site. A browser, Flatpak query or app launch can still fail at runtime; no GUI success is inferred from source checks.

## Owned files

- `image/usr/local/bin/windows12-windows-apps` (executable)
- `image/usr/share/applications/windows12-windows-apps.desktop`
- This document

The desktop packager already includes overlay files recursively. Parent integration must update desktop-entry routing checks, bump the future package version, and keep the active frozen archive untouched.

## Verification and remaining acceptance

Only Python AST parsing and source/desktop-entry inspection were performed for this change. No launcher/module was executed on the host; no network request, package install, Flatpak query, VM or application run was performed. `bottles_command(find=..., run=...)` allows guest tests to mock user/system routing, missing Flatpak, query failures/timeouts and exact argv without launching apps or using the network.

Before presenting this as working integration, validate in the contained graphical target: missing-Bottles local guide; official links and reference file opening in Discover; absent Flatpak remote; user/system install routing; actual first-run downloads and cancellation; regular-user launch; offline warm launch; x86 and x64 fixture workflows; shortcuts after reboot; removal; browser/cache failures. Record actual additional download/storage cost. Existing `WINDOWS_APP_RUNTIME_PLAN.md` and `COMPAT_FIXTURES.md` provide the per-app acceptance matrix. A passed launcher route is not a passed Wine application.

Contained verification: the integrated31-test guest suite passed, including mocked scope selection, missing/failed Flatpak queries and root refusal. No real Flatpak/Bottles/application/GUI execution occurred.
