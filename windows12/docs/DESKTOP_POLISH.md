# Fresh-profile desktop polish

Source changes made by desktop_polish on 2026-11-06 UTC. These changes are a future image candidate only. The retained builder, frozen checks.tar, package version, package recipe and current guest disk were not changed.

## Concrete defects addressed

- A partially populated Plasma panel repaired by the existing script appended a missing Kickoff or icon task manager to the end. That could place the application menu on the right despite the guide promising a bottom-left menu. The fresh-profile script now sets the launcher to index 0 and icon task manager to index 1 after creating either. Existing widgets stay present. This remains a fresh-profile initialization script and must not be deployed as an upgrade that resets established user panels.
- The compatibility table had no explicit overflow container, so its minimum content width could widen the whole help page at small display widths or high zoom. It now scrolls inside a named keyboard-focusable region, with instructions, a caption and explicit column/row headers.
- Fixed large header spacing and text could crowd the page at high zoom. Responsive spacing, heading size and grid minimums now adapt to the available width. A visible focus outline and in-page links make the long offline guide easier to navigate by keyboard. Dolphin path and Downloads guidance explains a common Linux workflow without installing additional software.

## Changed files

- image/usr/share/plasma/shells/org.kde.plasma.desktop/contents/updates/windows12-layout.js
- image/usr/local/share/windows12/welcome.html
- docs/DESKTOP_POLISH.md

## Verification and limits

Only source inspection, HTML parsing and diff/whitespace checks were performed. No target module, test suite, package, desktop session, VM or network operation ran. No GUI success is claimed. The guide keeps its offline CSP, contains no scripts or external assets, and adds no dependencies, services, startup applications or network calls.

Before including this candidate in a release: run the normal contained overlay/package checks; boot a fresh profile plus a deliberately partial disposable panel; verify menu/task ordering, no lost widgets and persistence across login. Inspect the offline guide at 320 CSS pixels, ordinary/high zoom and keyboard-only use; confirm the whole page stays within the viewport while only the table scrolls. Verify the selected Plasma version supports writable Widget.index as used by its scripting API. Existing-source tests are not GUI certification.
