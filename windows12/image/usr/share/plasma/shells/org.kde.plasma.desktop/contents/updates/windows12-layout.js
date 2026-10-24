// Initial derivative defaults; Plasma records update scripts per user.
// Intended for fresh image users; first execution adjusts the initial panel.
// Plasma records execution; do not distribute as an upgrade to existing profiles.
var allPanels = panels();
var panel = allPanels.length ? allPanels[0] : new Panel;
panel.location = "bottom";
panel.height = 48;
var widgets = panel.widgets();
var launcher = null;
var tasks = null;
for (var i = 0; i < widgets.length; ++i) {
    if (widgets[i].type === "org.kde.plasma.kickoff") launcher = widgets[i];
    if (widgets[i].type === "org.kde.plasma.icontasks") tasks = widgets[i];
}
if (!launcher) launcher = panel.addWidget("org.kde.plasma.kickoff");
launcher.currentConfigGroup = ["General"];
launcher.writeConfig("icon", "start-here-kde");
if (!tasks) tasks = panel.addWidget("org.kde.plasma.icontasks");
tasks.currentConfigGroup = ["General"];
tasks.writeConfig("launchers", ["applications:org.kde.dolphin.desktop", "applications:chromium.desktop", "applications:windows12-office.desktop", "applications:org.kde.discover.desktop"]);
if (!widgets.length) {
    panel.addWidget("org.kde.plasma.systemtray");
    panel.addWidget("org.kde.plasma.digitalclock");
    panel.addWidget("org.kde.plasma.showdesktop");
}
var screens = desktops();
for (var j = 0; j < screens.length; ++j) {
    screens[j].wallpaperPlugin = "org.kde.image";
    screens[j].currentConfigGroup = ["Wallpaper", "org.kde.image", "General"];
    screens[j].writeConfig("Image", "file:///usr/share/wallpapers/Windows12/contents/images/3840x2160.svg");
}
