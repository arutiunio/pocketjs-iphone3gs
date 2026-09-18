# Troubleshooting notes

These are the actual failures encountered while getting Pocket Shell running on a jailbroken iPhone 3GS.

## Cydia OpenSSH downloads time out

Symptom: OpenSSH cannot be installed from legacy Cydia repos.

Working workaround:

```bash
./restore.sh --no-internet-check --sshrd
```

in Legacy iOS Kit, then use:

```text
Install OpenSSH (iOS 10 and lower)
```

from the SSH ramdisk menu.

## SSH works by password but PocketJS fails

PocketJS deploy uses `BatchMode=yes`, so password-only SSH is insufficient.

Create a dedicated RSA key under:

```text
~/.cache/pocket-stack/ipodtouch4/ssh/id_rsa
```

and append its public key to:

```text
/var/root/.ssh/authorized_keys
```

Old OpenSSH on iOS 6 also needs:

```text
HostKeyAlgorithms=+ssh-rsa
PubkeyAcceptedAlgorithms=+ssh-rsa
```

The post-quantum SSH warning from modern macOS OpenSSH is expected against an old iOS 6 server.

## Root partition at 100%

Observed:

```text
/dev/disk0s1s1  1.3G  1.3G  0  100% /
```

Use Cydia's own stashing helper when present:

```bash
/usr/libexec/cydia/free.sh
```

Afterward, `/Applications` was moved under `/var/stash` and the root filesystem had usable free space again.

## MobileTerminal package fails with duplicate Pre-Depends

Old iOS dpkg may reject packages with duplicate control fields.

If you manually repackage legacy .deb files, merge duplicate dependency fields into one line.

## Old iOS dpkg cannot unpack xz

Modern `dpkg-deb` may emit `data.tar.xz`, which old dpkg cannot unpack.

Rebuild legacy packages with gzip:

```bash
dpkg-deb --root-owner-group -Zgzip -z9 -b package-dir output.deb
```

This was needed for MobileTerminal/coreutils during setup, but MobileTerminal itself is not required for PocketJS.

## Doctor rejects ActivationState

Observed:

```text
activation=WildcardActivated
```

Upstream expects only:

```text
Activated
```

The 3GS patch accepts both.

## `prepare-sysroot` asks for `POCKETJS_IPHONE4S_IPSW`

The iPod touch 4 target delegates sysroot creation to the iPhone 4S ARMv7 path.

We generated a CustomJ iPhone 4S 6.1.3 IPSW with Legacy iOS Kit in no-device mode and used it only as the sysroot source.

Do not flash that IPSW to the 3GS.

## Legacy iOS Kit DNS failures

We saw failures resolving:

```text
api.appledb.dev
raw.githubusercontent.com
```

The tool could continue once required source material was already downloaded/validated locally.

## `xcrun --find ld-classic` fails

Symptom:

```text
xcrun: error: unable to find utility "ld-classic"
```

Command Line Tools alone are insufficient.

Xcode 27 also does not provide the linker path expected by this legacy build.

Install Xcode 26.6 separately and invoke builds with:

```bash
DEVELOPER_DIR=/Applications/Xcode-26.6.app/Contents/Developer \
  bun run touch deploy
```

No global `xcode-select` switch is required.

## Xcode license blocks clang

Symptom:

```text
You have not agreed to the Xcode license agreements
```

Fix:

```bash
sudo env \
  DEVELOPER_DIR=/Applications/Xcode-26.6.app/Contents/Developer \
  xcodebuild -license accept

sudo env \
  DEVELOPER_DIR=/Applications/Xcode-26.6.app/Contents/Developer \
  xcodebuild -runFirstLaunch
```

## Rust build asks for rust-src

Fix:

```bash
rustup component add rust-src --toolchain nightly-2026-07-02
```

## Success criteria

A good deploy ends with:

```text
Mach-O executable arm_v7
deployed User app ... with byte-exact readback
```

A good launch reports:

```text
state: running
renderer: gles1
clock: displaylink
raster_density: 1
drawable_width: 320
drawable_height: 480
error: ""
```
