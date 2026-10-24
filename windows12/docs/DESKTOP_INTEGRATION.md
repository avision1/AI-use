# Desktop integration
The `image/` tree is copied into the target OS, never the host root. Source scripts use fixed system paths only at target runtime. Windows12 is a working name, not a Microsoft product.

- `windows12-webapp`: Python 3 launcher with a fixed app-ID/HTTPS allowlist. Chromium app window preferred; Firefox fallback is explicitly a browser window. No shell command interpolation, embedded web engine, captured credentials, forced insecure flags, custom CA or secret storage. Uses the user's existing browser profile. Does not make that browser's content a security sandbox.
- `windows12-welcome`: xdg-open of offline help. No autostart browser or network requests; launch manually from the menu.
- Plasma update script: preserve current widgets, move first panel to bottom, set common pinned applications and project wallpaper; KDE records it once per user. Existing panels are not deleted, but the first panel is adjusted on first execution. This is for fresh image users; applying it as an upgrade to preexisting profiles is not supported. First-run ordering, high DPI and multi-monitor behavior require real GUI validation.
- `/etc/skel/.config`: defaults for newly created users; existing users are not overwritten by these files. Live-user inheritance requires VM validation.
- Original SVG geometric wallpaper; no Microsoft marks or copied assets.

Target package requirements: python3, xdg-utils, chromium (preferred) or firefox-esr, Plasma desktop, Dolphin, Discover; LibreOffice alternative. Missing apps are not silently downloaded by launchers. Wine, gaming, domain join and OneDrive sync are not implemented by this overlay.

Web URLs can change and tenant policies may affect sign-in; service redirects and authenticated document editing have not been validated. Menu launchers are not native Microsoft Office applications. App class matching on Chromium/Wayland needs manual validation. No automatic file associations claim Office web can open local documents.
