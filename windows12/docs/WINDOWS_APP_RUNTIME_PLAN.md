# Windows application runtime lane

Owner `/root/release_inputs`; W12-009 research, 2026-10-24. Strict project `/workspace/scratch/3c38ab731138/AI-use/windows12/`; only this document was written. Current image/builder unchanged. No Windows binary, runner or Flatpak payload was downloaded; no executable test, package install, VM or Git mutation was performed. Metadata/docs were read from primary upstream services.

## Proposed reversible decision

After the first ISO's boot/install gates pass, prototype **stable Bottles from Flathub as an optional Windows Applications entry**, with runtime/component downloads on demand. Retain Debian's Wine packages as a separately measured fallback, particularly if offline Windows-app startup becomes necessary. Do not preload both stacks, all game launchers, proprietary runtimes or test applications into the base ISO.

This is a candidate integration recommendation, not an implemented feature. Bottles supplies an existing graphical bottle/installer workflow; using it avoids building and maintaining a second prefix manager. The current image already selects Flatpak and Discover but does not deliberately select Discover's Flatpak backend or configure a remote. An entry that merely opens a dead store link would fail acceptance.

Keep Office web launchers explicitly partial, LibreOffice the offline alternative, and native current Microsoft365 desktop Office unsupported. Passing a small editor/archive test never implies Office, all EXEs or Windows drivers work.

## Evidence and comparison

| Choice | Practical benefit | Required work and tradeoff |
|---|---|---|
| Debian13 native Wine | Standard Debian package/update/signature route; versions can be recorded with the OS. Preinstalling the full tested runtime can avoid downloading Wine itself at first app launch. | Trixie currently lists wine/wine64/wine32 10.0~repack-6. `wine` accepts either loader; selecting it does not guarantee both architectures. On amd64, explicitly enable/test i386 and install wine32:i386 for the classic Debian32-bit lane. Avoid substituting upstream new-WoW64 claims for tests of these Debian binaries. A project-managed GUI/prefix/shortcut/uninstall flow would still be needed. [W1–W3] |
| Stable Bottles Flatpak | Maintained GUI for separate bottles, choosing/running installers, dependencies and program organization. Flatpak carries its own runtime/multiarch extensions rather than requiring OS-wide i386 APT configuration for that bundle. [B1–B4] | Adds Flathub trust/update and component-download paths. Initial install requires network; runner/component availability, offline behavior, graphics and file chooser integration require measured tests. Flatpak confinement is useful but the actual permission set is broad, not malware-proof. Do not assume all runner downloads are covered by Flatpak's package signature. |
| Own Wine wrapper/front end | Maximum direct control and potentially small UI surface. | Recreates prefix management, dependency/version selection, desktop integration and recovery already supplied upstream. Not the smallest first usable lane. A small integration launcher may still be useful, but should delegate actual runtime management. |

### Size is a measurement gate

Debian's package page currently lists **libwine alone** as742,841kB installed on amd64 and623,166kB on i386, with compressed package sizes108,754.9kB and101,682.6kB. Their sum is1,366,007kB installed before loaders,32-bit system/graphics/audio dependencies, prefixes, Mono/Gecko or applications. This is neither a full dependency closure nor an ISO-size estimate; existing64-bit dependencies may already be shared. [W4]

For Bottles, record the actual Flatpak transaction's additional download/installed sizes, runtime refs, selected GL/32-bit extensions, runner archive size and one fresh bottle's size. No reliable fixed total was established here. The old documentation's approximate70MB first-run claim is not a current budget promise. Optional installation reduces initial ISO growth but moves cost and network dependence to first use.

### Current upstream details that prevent stale assumptions

- Official release metadata currently lists Bottles67.4 dated2026-09-07 for Cpak; its notes explicitly say Flathub67.3 receives Soda11.0-10 through the Components catalog. This demonstrates continuing maintenance, not that those exact versions are installed in our image. Do not adopt experimental Bottles Next or Cpak for this first lane merely because they exist. [B5]
- The Flathub manifest was read at commit `ab194a53a873cb1c04279c0a05fa4d760dd372f9`, file blob `e9be5448bb0478187b38349b87dc5e4728237010`. It names GNOME Platform50, Wine base stable-25.08 and Freedesktop25.08 i386/GL extensions. The installed stable ref/commit/runtime must still be queried; repository master is not proof of what Flathub has deployed. [B6]
- That manifest grants network, IPC, X11/Wayland, audio, `device=all`, selected UMU directories and UDisks2 communication. Never label this a safe container for untrusted Windows programs. App permissions and portal/file sharing must be inspected on the actual installed ref. [B6,F1]
- Some older Bottles pages still mention Caffe,2021 CLI transitions and an approximate first-run download. Use them for workflow intent, then verify actual GUI/CLI behavior and Soda/component identity. They are not authoritative current version pins. [B2–B4]

## Smallest next-candidate integration

1. First validate the existing Debian/KDE ISO, ordinary account, networking, Discover repository operations and installed reboot. Keep this Windows lane off the active frozen build.
2. In a later candidate, ensure `plasma-discover-backend-flatpak` and the KDE portal integration are actually installed and working. Retain native Debian package management. Do not add an entire alternate desktop/store.
3. Add a clearly labeled Windows Applications entry. If Bottles is installed, open it as the regular user. Otherwise offer its official stable Flathub package through the validated software UI, explaining the initial network/download requirement and that app compatibility varies. Show real transaction size where available. Do not silently download executables at login or promise offline first use.
4. Add the official Flathub remote deliberately, preferably per-user for the first prototype. If a remote called flathub already exists, inspect its URL/key configuration before using it; never overwrite it or trust the name alone. Preserve GPG verification; do not copy the documentation's manual-build `--no-gpg-verify` example into product setup. Flatpak distinguishes per-user from system installations and `.flatpakrepo` files carry remote/key information. [F2]
5. Let the user create a separate bottle for each application, choose an installer with the normal file chooser and use Bottles' actual Run executable flow. Use an ordinary Application/custom environment appropriate to the tested runner; do not enable gaming tweaks/Vulkan-only paths just for a text editor. No administrator/root Wine execution.
6. Implement a friendly .exe/.msi Open With action only after querying the installed Bottles CLI and proving the exact file forwarding/bottle-selection path. Use argument arrays, real local paths and validated MIME types, handle spaces/non-ASCII/cancel/multiple files, and refuse shell interpolation. Do not install wine-binfmt or globally execute all PE files automatically. If forwarding is unverified, keep it planned rather than claiming double-click support.
7. Verify/export a real application shortcut using the current supported mechanism, then test launch after logout/reboot and uninstall cleanup. Older installer docs explicitly caveat Flatpak shortcut behavior, so menu integration cannot be inferred from installing Bottles. [B4]

Proposed QA commands **inside the contained target guest only**, not on the execution host, after the remote identity has been inspected:

```sh
flatpak remotes --user
# Only if the trusted remote is absent; review existing-name conflicts first:
flatpak remote-add --user flathub https://dl.flathub.org/repo/flathub.flatpakrepo
flatpak install --user flathub com.usebottles.bottles
flatpak info --user com.usebottles.bottles
flatpak info --user --show-commit com.usebottles.bottles
flatpak info --user --show-permissions com.usebottles.bottles
flatpak run com.usebottles.bottles
```

Record actual app/runtime commits, permissions, component catalog revision, chosen runner/version/architecture, downloaded component URLs/hashes and bottle configuration. Signed Flatpak package provenance and separately downloaded Wine/dependency components are different trust records. Follow upstream checksum checks but do not call an unsigned component catalog independently authenticated unless that chain is established.

If evaluating Debian Wine instead, simulate and record the complete amd64+i386 package transaction inside a disposable guest first, then install only there. A proposed starting set is wine,wine64,wine32:i386,fonts-wine after `dpkg --add-architecture i386` and a signed APT update. Verify Mono/Gecko/font prompts,32/64-bit behavior and offline readiness rather than assuming a package list settles them. Do not mix sid, WineHQ and stable Debian packages casually or add Winetricks/proprietary redistributables by default.

## Privacy, sharing, accounts and isolation

Bottles' documented local bottle workflow has no account step, while individual applications may require their own accounts, licenses or activation. Flathub/GitHub/component hosts receive ordinary network requests for metadata/downloads; exact analytics behavior was not audited. Windows apps may also use the network. Do not claim documents cannot leave the machine just because Wine runs locally.

Prefer portals for file selection. If a Wine-native chooser cannot reach a required folder, expose only a dedicated guest test/user-selected folder, not the whole home or host filesystem. Bottles documents per-directory access and advises against broad home/system exposure. [B7] All development test downloads, caches, prefixes and fixture outputs ultimately remain inside the project-contained VM disks/artifact directories. Never map host source, home or physical devices to satisfy an application's file access.

Separate bottles isolate configuration and simplify removal; they are not independent security sandboxes from one another within the same Bottles application. Only benign official fixtures belong in this smoke lane. No Microsoft credentials, proprietary app bundles or test-user private files go into the ISO/repository/logs.

## Reproducible harmless fixtures — metadata only, not downloaded/tested

Metadata was retrieved from the official projects' GitHub release API on2026-10-24. The7-Zip official download page links the ip7z release repository. [T1,T2] Preserve the exact public URL, release metadata, SHA256, size and applicable license/source links in ignored project fixture storage before eventual execution. A same-service HTTPS digest detects byte mismatch but is not an independently signed attestation.

| Fixture | Official fixed release asset | Bytes | SHA256 |
|---|---|---:|---|
| 7-Zip26.05 Windows x64 EXE | `https://github.com/ip7z/7zip/releases/download/26.05/7z2605-x64.exe` |1663506|`fd99e86f57d8f429ef5ed045bf98315af962e2309b0f1ba87a147a44c71647d0`|
| 7-Zip26.05 Windows x86 EXE | `https://github.com/ip7z/7zip/releases/download/26.05/7z2605.exe` |1362132|`6435a470fe7c4769962dbed8a60c641ee21401c833ced06077c80e33e7845a5e`|
| 7-Zip26.05 Windows x64 MSI | `https://github.com/ip7z/7zip/releases/download/26.05/7z2605-x64.msi` |2008576|`3fe4ab99fa15629c652944309a2b2bc6e41fc933fc6b63f5df1ebcf3aea68263`|
| Notepad++8.9.8.1 Windows x64 EXE | `https://github.com/notepad-plus-plus/notepad-plus-plus/releases/download/v8.9.8.1/npp.8.9.8.1.Installer.x64.exe` |6963432|`26f3bcced788fadbac4e7e577b430ea2ce6060cf3bcad993ef4612ecd7d743da`|

7-Zip26.05 was published2026-10-21. Its observed release asset list contains no detached signature; no Authenticode validity was tested. Do not invent a signature guarantee. The official license identifies LGPL/BSD terms plus an unRAR restriction and requires related license information with binary redistribution. [T2,T3] Keep it a test fixture instead of preinstalling a duplicate archiver; the image already has Ark.

Notepad++8.9.8.1 was published2026-09-24. Its release metadata provides `npp.8.9.8.1.checksums.sha256` (1271bytes,SHA256 `78bc138eff0675589b7887ed3114d30acdcd807f19f36b3ba4095b44173d1e36`) and `.sig` (594bytes,SHA256 `c274d40e1ff3bef4f4e911f9a764c3e19c62ca4768bd75bbe99fa7eeefc2275b`), plus per-binary signatures. Its official README pins primary GPG fingerprint `14BCE4362749B2B51F8C71226C429F1D8D84F46E`, with documented expiry2027-03-13. Before execution, obtain the official public key, check the full fingerprint and validity/revocation/date context, verify the checksum signature with matching VALIDSIG identity, then enforce the binary's checksum/size. Those cryptographic checks have **not** been run here. [T4,T5]

Notepad++'s v8.9.8.1 LICENSE describes GPLv3 with clarifications/exceptions. Preserve the actual version's license and corresponding source information if ever redistributing; this plan does not add it to the ISO or provide a legal assessment. [T6]

## Acceptance before any support label

Run only after the normal desktop/installed account works. Keep each case in a fresh separate bottle, retain screenshots/logs and exact OS/browser/runtime/app metadata, and compare saved fixtures outside Wine using the native tools. Do not relax a failed gate or count an installer exit code as functional support.

| Case | Required observable result |
|---|---|
| Setup/recovery | Regular user can install/open Bottles, inspect dependency download progress, cancel/retry a failed network transfer and create a bottle. A second start works; logout/reboot preserves configuration. Record download size/time and network-failure behavior. |
| x64 EXE installer | 7-Zip x64 installs through GUI; its window opens with sensible fonts/scaling and keyboard focus. Create ZIP and7z archives from disposable fixtures, list/extract them, then verify the extracted files' hashes using native Linux tools. |
|32-bit coverage | Repeat independently with7-Zip x86. An x64 pass is not32-bit support. Record actual prefix/runner architecture and any failure; do not silently switch runtime mid-result. |
| MSI path | Install the separate7-Zip x64 MSI in a new bottle, launch/use/uninstall it. Keep it separate from the EXE case; the vendor recommends EXE for ordinary use, while MSI tests the requested installer class. |
| Editor/save | Notepad++ x64 installs/opens. Open a disposable UTF-8 fixture, edit, save to the deliberately shared test folder, close/reopen, verify bytes/native readability, and exercise clipboard, file chooser and non-ASCII filename behavior. Decline optional plugins/self-updates during the fixed-version measurement. |
| File association/menu | A selected local EXE/MSI reaches the intended bottle-selection/install UI without shell injection or execution as root. Cancel works. A generated program shortcut launches the right application/prefix after reboot. Do not globally replace native text/archive defaults merely for this test. |
| Removal/isolation | Uninstall the application through its actual Windows/Bottles-supported UI; confirm launcher cleanup and that another bottle plus shared user documents remain intact. Then stop that bottle's processes and deliberately remove its remaining bottle state with explicit data handling. Flatpak app removal and application-data removal are separate actions. |
| Offline/runtime update | After first successful warm setup, disable guest network and repeat local open/save/archive tests. Record any component prompt/failure. Update one selected runner/app revision and repeat the fixture; preserve the previous configuration/backups to distinguish regression from a fresh-prefix change. |

Full support, if eventually earned, applies only to an exact tested workflow/app/runtime/version on stated environment. Until then label this lane **planned/unverified**, and later **partial/per-application** as evidence warrants. Existing native Linux alternatives remain normal first choices for equivalent tasks.

## Unsupported or separate lanes

No Windows kernel-driver installation, vendor kernel utility support, Microsoft Store/UWP parity or native Microsoft365 desktop guarantee is introduced. This project does not supply a Windows kernel. Games, graphics acceleration and DRM require separate title/GPU/driver tests; a software-rendered VM editor pass is no gaming certification. Valve specifically documents unsupported kernel-space anti-cheat and per-title enabling steps for supported user-space systems; DRM can also delay support. These facts do not justify bypassing anti-cheat/DRM or claiming every such application fails identically. [L1]

## Primary sources

- [W1] Debian13 wine: https://packages.debian.org/trixie/wine
- [W2] Debian13 wine32: https://packages.debian.org/trixie/wine32
- [W3] Debian13 wine64: https://packages.debian.org/trixie/wine64
- [W4] Debian13 libwine sizes/dependencies: https://packages.debian.org/trixie/libwine
- [B1] Official installation guidance (older version details require revalidation): https://docs.usebottles.com/getting-started/installation ; current download recommendation: https://usebottles.com/
- [B2] First-run concept/download checks (historical component names/budget): https://docs.usebottles.com/getting-started/first-run
- [B3] Executable GUI/CLI workflow (historical CLI notes): https://docs.usebottles.com/bottles/run-.exe-.msi-.bat-.lnk-files.md
- [B4] Installer/menu caveat: https://docs.usebottles.com/bottles/installers.md ; uninstaller documentation is explicitly unfinished: https://docs.usebottles.com/utilities/uninstaller.md
- [B5] Current official release observations: https://github.com/bottlesdevs/Bottles/releases/tag/67.4 ; https://github.com/bottlesdevs/Bottles/releases/tag/67.3
- [B6] Observed immutable Flathub source manifest: https://github.com/flathub/com.usebottles.bottles/blob/ab194a53a873cb1c04279c0a05fa4d760dd372f9/com.usebottles.bottles.yml
- [B7] Per-directory sharing/portal guidance: https://docs.usebottles.com/flatpak/expose-directories.md
- [F1] Flatpak permission model/portals: https://docs.flatpak.org/en/latest/sandbox-permissions.html
- [F2] Flatpak remotes, per-user installation and IDs: https://docs.flatpak.org/en/latest/using-flatpak.html
- [T1] Official7-Zip download links: https://www.7-zip.org/download.html
- [T2] Official fixed release metadata: https://api.github.com/repos/ip7z/7zip/releases/tags/26.05
- [T3] Official7-Zip license: https://www.7-zip.org/license.txt
- [T4] Official Notepad++ fixed release: https://api.github.com/repos/notepad-plus-plus/notepad-plus-plus/releases/tags/v8.9.8.1
- [T5] Official Notepad++ signer identity: https://github.com/notepad-plus-plus/notepad-plus-plus/blob/master/README.md ; https://github.com/notepad-plus-plus/notepad-plus-plus/blob/master/nppGpgPub.asc
- [T6] Versioned license: https://github.com/notepad-plus-plus/notepad-plus-plus/blob/v8.9.8.1/LICENSE
- [L1] Valve Proton limits/anti-cheat integration: https://partner.steamgames.com/doc/steamhardware/proton

Research complete. Next action for parent: decide the optional Bottles prototype after the current ISO's real desktop/install validation, then implement and execute these gates. No app/runtime support result is implied by this document.
