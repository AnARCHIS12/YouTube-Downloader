#!/usr/bin/env bash
set -euo pipefail

APP_NAME="youtube-downloader"
BIN_NAME="YouTubeDownloader"
VERSION="${VERSION:-1.0.0}"
ARCH_DEB="${ARCH_DEB:-amd64}"
ARCH_RPM="${ARCH_RPM:-x86_64}"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DIST_DIR="$ROOT_DIR/dist"
BUILD_DIR="$ROOT_DIR/build"
APPDIR="$BUILD_DIR/appdir"
PKG_DIR="$DIST_DIR/packages"

cd "$ROOT_DIR"

command -v python >/dev/null
command -v dpkg-deb >/dev/null
command -v rpmbuild >/dev/null
command -v ffmpeg >/dev/null
command -v ffprobe >/dev/null

python - <<'PY'
import importlib.util
missing = [name for name in ("PyInstaller", "customtkinter", "yt_dlp") if importlib.util.find_spec(name) is None]
if missing:
    raise SystemExit("Missing build modules: " + ", ".join(missing) + "\nRun: python -m pip install -r requirements-build.txt")
PY

rm -rf "$BUILD_DIR" "$DIST_DIR/$BIN_NAME"
mkdir -p "$PKG_DIR"

python -m PyInstaller --clean --noconfirm YouTubeDownloader.spec

rm -rf "$APPDIR"
mkdir -p \
  "$APPDIR/usr/bin" \
  "$APPDIR/usr/lib/$APP_NAME" \
  "$APPDIR/usr/share/applications" \
  "$APPDIR/usr/share/icons/hicolor/scalable/apps"

cp "$DIST_DIR/$BIN_NAME" "$APPDIR/usr/lib/$APP_NAME/$BIN_NAME"
cp "$(command -v ffmpeg)" "$APPDIR/usr/lib/$APP_NAME/ffmpeg"
cp "$(command -v ffprobe)" "$APPDIR/usr/lib/$APP_NAME/ffprobe"
cp "$ROOT_DIR/packaging/youtube-downloader.desktop" "$APPDIR/usr/share/applications/$APP_NAME.desktop"
cp "$ROOT_DIR/assets/youtube-logo.svg" "$APPDIR/usr/share/icons/hicolor/scalable/apps/$APP_NAME.svg"

cat > "$APPDIR/usr/bin/$APP_NAME" <<EOF
#!/usr/bin/env bash
exec /usr/lib/$APP_NAME/$BIN_NAME "\$@"
EOF
chmod 755 \
  "$APPDIR/usr/bin/$APP_NAME" \
  "$APPDIR/usr/lib/$APP_NAME/$BIN_NAME" \
  "$APPDIR/usr/lib/$APP_NAME/ffmpeg" \
  "$APPDIR/usr/lib/$APP_NAME/ffprobe"

tar -C "$APPDIR" -czf "$PKG_DIR/$APP_NAME-$VERSION-linux-$ARCH_RPM.tar.gz" .

DEB_ROOT="$BUILD_DIR/deb"
rm -rf "$DEB_ROOT"
mkdir -p "$DEB_ROOT/DEBIAN"
cp -a "$APPDIR/." "$DEB_ROOT/"
cat > "$DEB_ROOT/DEBIAN/control" <<EOF
Package: $APP_NAME
Version: $VERSION
Section: video
Priority: optional
Architecture: $ARCH_DEB
Maintainer: Anar
Description: YouTube Downloader
 A modern fullscreen YouTube-style desktop downloader powered by yt-dlp with ffmpeg bundled.
EOF
dpkg-deb --build "$DEB_ROOT" "$PKG_DIR/${APP_NAME}_${VERSION}_${ARCH_DEB}.deb"

RPM_TOP="$BUILD_DIR/rpmbuild"
RPM_TMP="$BUILD_DIR/rpmtmp"
RPM_SOURCE_DIR="$RPM_TOP/SOURCES/$APP_NAME-$VERSION"
rm -rf "$RPM_TOP"
mkdir -p "$RPM_TOP"/{BUILD,RPMS,SOURCES,SPECS,SRPMS} "$RPM_SOURCE_DIR" "$RPM_TMP"
cp -a "$APPDIR/." "$RPM_SOURCE_DIR/"
tar -C "$RPM_TOP/SOURCES" -czf "$RPM_TOP/SOURCES/$APP_NAME-$VERSION.tar.gz" "$APP_NAME-$VERSION"

cat > "$RPM_TOP/SPECS/$APP_NAME.spec" <<EOF
%global debug_package %{nil}

Name:           $APP_NAME
Version:        $VERSION
Release:        1%{?dist}
Summary:        YouTube Downloader
License:        MIT
URL:            https://example.invalid/youtube-downloader
Source0:        %{name}-%{version}.tar.gz
BuildArch:      $ARCH_RPM

%description
A modern fullscreen YouTube-style desktop downloader powered by yt-dlp with ffmpeg bundled.

%prep
%setup -q

%build

%install
mkdir -p %{buildroot}
cp -a . %{buildroot}/

%files
/usr/bin/$APP_NAME
/usr/lib/$APP_NAME/$BIN_NAME
/usr/lib/$APP_NAME/ffmpeg
/usr/lib/$APP_NAME/ffprobe
/usr/share/applications/$APP_NAME.desktop
/usr/share/icons/hicolor/scalable/apps/$APP_NAME.svg

%changelog
* Thu Apr 30 2026 Anar <anar@example.invalid> - $VERSION-1
- Initial package
EOF

rpmbuild \
  --define "_topdir $RPM_TOP" \
  --define "_tmppath $RPM_TMP" \
  -bb "$RPM_TOP/SPECS/$APP_NAME.spec"
find "$RPM_TOP/RPMS" -type f -name "*.rpm" -exec cp {} "$PKG_DIR/" \;

echo
echo "Packages generated in: $PKG_DIR"
ls -lh "$PKG_DIR"
