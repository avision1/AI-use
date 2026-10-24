# Compatibility and evidence

Research date: 2026-10-23 (America/Chicago). No derivative boot, install, hardware, Office account, Wine application or game tests have been completed at the time of this research. Integration source code and inherited upstream capability are not proof of working product support. PROJECT_STATE.md and validation reports are authoritative for subsequent results.

## Status vocabulary

- **Full support** requires a specified workflow to pass the project's acceptance checks on stated versions/hardware. No workflow has earned this label yet.
- **Partial** means a usable route with important limits. The route still needs project validation.
- **Alternative** provides a similar outcome using different software or service, without claiming feature parity.
- **Unsupported** means the project currently supplies no supported implementation. This need not imply that no third-party solution exists.
- **Planned / unverified** distinguishes intended integration from completed execution.

## Workflow matrix

| Requested workflow | Classification / intended route | Current evidence and limits | Validation required |
|---|---|---|---|
| Familiar launcher, taskbar, tray, file browsing and settings | Planned Linux-native desktop support through KDE Plasma | Plasma exposes documented customization APIs [C1]. Familiar controls do not reproduce every Windows behavior. | First/second login, launcher search, pinned apps, file operations, shortcuts, personalization persistence. |
| Install to a PC and boot installed OS | Planned Linux-native support via inherited Debian live installer | Debian documents KDE live media and Calamares [C2]; custom image has not been booted or installed. | BIOS/UEFI live boot, disposable-disk installation, ISO removal and installed reboot. |
| Microsoft Word, Excel and PowerPoint everyday editing | Partial: Microsoft web applications through explicit desktop launchers | Launchers do not install native Office or add web features. Account, connectivity, licensing and organization policy may limit access. No authenticated workflow tested. | Create/edit/save/download representative DOCX/XLSX/PPTX documents and validate results in expected consumer. |
| Outlook mail/calendar | Partial: Outlook on the web | Microsoft explicitly lists Firefox or Chrome on Linux, with some unavailable features [C3]. | Account sign-in, compose/send to a test address only when authorized, attachments, calendar and notifications. |
| Excel VBA automation | Unsupported in web route | Microsoft states Excel web cannot create, run or edit VBA, although macro-containing workbooks can be edited while retaining macros [C4]. | Do not advertise VBA execution. Any future licensed Windows VM route needs separate scope and testing. |
| Native current Microsoft 365 desktop Office | Unsupported as a native Linux product | Microsoft's client OS requirements list Windows, macOS, Android and iOS; Linux is absent [C5]. This is an inference about supported platforms, not proof that every Wine experiment fails. | Do not claim native Office support from successful website loading. |
| Offline documents and office-file interchange | Alternative: LibreOffice if included in the selected image | LibreOffice documents Office-format workflows, but its macro environment differs; VBA support is limited [C6,C7]. Layout, fonts, complex formulas, macros and round trips need representative tests. | Open/edit/export a fixture corpus; compare pagination, formulas, charts and presentations; document losses. |
| General Windows EXE/MSI programs | Planned partial route: evaluate Wine per application | Wine is a Windows application compatibility layer [C8], not a universal certification. No app/version has been tested here and runtime inclusion is not yet established. | Separate prefixes; record app/runtime/architecture; install, use, save, reopen and uninstall. |
| Windows games | Planned partial route: native Linux games or Steam/Proton evaluation | Valve documents compatibility work and per-title anti-cheat integration. Kernel-space anti-cheat is unsupported by Proton [C9]. Steam/Proton are not promised preinstalled. | Exact title/version, GPU/driver, launcher, multiplayer and anti-cheat checks. Never infer support for all games. |
| Windows kernel drivers and vendor-only utilities | Unsupported Windows driver route; use Linux drivers or vendor Linux tools | Project is a Linux distribution. It supplies no Windows kernel/driver runtime. Device functionality depends on Linux support and firmware. | Device-specific peripherals and vendor tools; no generic driver-compatibility badge. |
| Wi-Fi, GPU, Bluetooth, sound, cameras, printers and suspend | Planned Linux-native support; hardware unverified | Debian notes required firmware may be missing even on official media [C10]. A VM pass cannot establish physical hardware support. | Publish exact device IDs/driver versions and hardware results before claims. |
| Windows Store/UWP, Xbox PC Game Pass local installs, Windows Hello, Windows Security, BitLocker management, WSL and Group Policy parity | Unsupported project implementations | No corresponding Windows service/runtime integration exists in this milestone. Linux alternatives may address parts of these workflows but must be specified and tested separately. | Gather actual needed workflows before choosing alternatives; do not present similarly named Linux features as full replacements. |
| OneDrive sync, enterprise domain management and Windows remote-management parity | Unsupported integrated parity; web/manual alternatives may be possible | A OneDrive website launcher is not background filesystem sync, and Linux account controls are not AD/Intune parity. No credentials or enterprise tenant tested. | Define selected workflow and policy requirements; test chosen solution separately. |

## Practical user-facing rules

Label launchers “Word (web)”, “Excel (web)”, “PowerPoint (web)” and “Outlook (web)”. Explain that uploaded documents go to the selected Microsoft service. Keep browser security/update mechanisms enabled; never disable certificate checks or Chromium sandboxing to make a launcher work. Do not store account credentials in the image or repository.

Prefer maintained system browsers to an embedded webview that silently diverges from Microsoft's supported web platform. A separate browser window is useful integration but is not an offline desktop Office port. A future app-mode browser or PWA must be tested for authentication, downloads, file picking, accessibility and updates.

## Primary sources

All accessed 2026-10-23. URLs are recorded for future revalidation; online policies and app behavior can change.

- [C1] KDE, Plasma Desktop scripting: https://develop.kde.org/docs/plasma/scripting/
- [C2] Debian, Live install images: https://www.debian.org/CD/live/
- [C3] Microsoft, Supported browsers for Outlook on the web and Outlook.com: https://support.microsoft.com/en-us/outlook/supported-browsers-for-outlook-on-the-web-and-outlook-com
- [C4] Microsoft, Work with VBA macros in Excel for the web: https://support.microsoft.com/en-us/excel/work-with-vba-macros-in-excel-for-the-web
- [C5] Microsoft, System requirements for Microsoft 365 for business, education and government use: https://support.microsoft.com/en-us/office/system-requirements/system-requirements-for-microsoft-365-for-business-education-and-government-use
- [C6] LibreOffice, Using Microsoft Office and LibreOffice: https://help.libreoffice.org/latest/en-US/text/shared/guide/ms_user.html
- [C7] LibreOffice, Support for VBA Macros: https://help.libreoffice.org/latest/en-US/text/sbasic/shared/vbasupport.html
- [C8] WineHQ, About Wine: https://www.winehq.org/about (search index summary retrieved; direct page returned 403). The primary Wine source README also links project documentation: https://github.com/wine-mirror/wine/blob/master/README.md . No app compatibility rating has been inferred from this source.
- [C9] Valve, Steam Hardware and Proton: https://partner.steamgames.com/doc/steamhardware/proton
- [C10] Debian, Loading Missing Firmware: https://www.debian.org/releases/trixie/amd64/ch06s04.en.html

Evidence caution: the historical Microsoft “Which browsers work with Microsoft 365 for the web and Microsoft 365 Add-ins” support URL redirected during this research to Office Add-ins browser-control documentation (https://learn.microsoft.com/en-us/office/dev/add-ins/concepts/browsers-used-by-office-web-add-ins). That page is not evidence that every Office web feature is supported on Linux. Use the explicit Outlook statement only for Outlook, and perform separate Office web tests.
