#!/bin/bash
# Executed ONLY inside the project build VM by cloud-init.
set -Eeuo pipefail
[[ -f /run/windows12-build-vm ]] || { echo 'Refusing host execution'; exit 70; }
mkdir -p /project-output
mount -t 9p -o trans=virtio,version=9p2000.L output /project-output
exec > >(tee -a /project-output/guest-build.log /dev/ttyS0) 2>&1
trap 'rc=$?; printf "%s\n" "$rc" > /project-output/build.exit; sync; shutdown -h now' EXIT
mkdir -p /root/windows12-checks
python3 - <<'PYTEST'
import urllib.request,tarfile,io
data=urllib.request.urlopen("http://10.0.2.2:8765/checks.tar").read()
with tarfile.open(fileobj=io.BytesIO(data)) as archive:archive.extractall("/root/windows12-checks",filter="data")
PYTEST
python3 -B -m unittest discover -s /root/windows12-checks/tests -v
python3 -B /root/windows12-checks/scripts/package-desktop.py
package=$(find /root/windows12-checks/artifacts/packages -name '*.deb' -print -quit)
first_digest=$(sha256sum "$package" | cut -d' ' -f1)
python3 -B /root/windows12-checks/scripts/package-desktop.py
[[ $(sha256sum "$package" | cut -d' ' -f1) == "$first_digest" ]]
dpkg-deb --info "$package"
dpkg-deb --contents "$package"
cp "$package" /project-output/
cp /root/windows12-checks/artifacts/packages/SHA256SUMS /project-output/desktop-SHA256SUMS
export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y live-build debootstrap ca-certificates curl
mkdir -p /root/windows12-build
cd /root/windows12-build
lb config --mode debian --distribution trixie --architectures amd64 \
 --binary-images iso-hybrid --archive-areas 'main contrib non-free non-free-firmware' \
 --debian-installer live --bootappend-live 'boot=live components username=user hostname=windows12' \
 --iso-application 'Windows12 independent Linux preview' \
 --iso-publisher 'AI-use community project' --iso-volume WINDOWS12_PREVIEW \
 --mirror-bootstrap http://deb.debian.org/debian \
 --mirror-chroot http://deb.debian.org/debian \
 --mirror-binary http://deb.debian.org/debian
mkdir -p config/package-lists config/includes.chroot config/hooks/live config/packages.chroot
cp "$package" config/packages.chroot/
cat > config/package-lists/windows12.list.chroot <<'PKGS'
linux-image-amd64
live-boot
live-config
live-config-systemd
systemd-sysv
task-kde-desktop
sddm
calamares
calamares-settings-debian
chromium
firefox-esr
python3
libreoffice
network-manager
plasma-nm
bluedevil
cups
system-config-printer
smbclient
kio-extras
ntfs-3g
exfatprogs
ark
okular
konsole
flatpak
plasma-discover
desktop-file-utils
xdg-utils
PKGS

# The proxy is build infrastructure only: remove any generated proxy config from ISO.
cat > config/hooks/live/0990-remove-proxy.hook.chroot <<'HOOK'
#!/bin/sh
set -eu
rm -f /etc/apt/apt.conf.d/80windows12-build-proxy
find /usr/share/applications -name 'windows12*.desktop' -exec desktop-file-validate {} +
python3 -m py_compile /usr/local/bin/windows12-webapp
HOOK
chmod +x config/hooks/live/0990-remove-proxy.hook.chroot
lb build
cp live-image-amd64.hybrid.iso /project-output/windows12-amd64-preview.iso
cp live-image-amd64.packages /project-output/windows12-amd64-preview.packages
cd /project-output
sha256sum windows12-amd64-preview.iso > SHA256SUMS
