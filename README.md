# PocketJS / Pocket Shell on iPhone 3GS (iOS 6.1.6)

A practical port and step-by-step guide for running [pocket-stack/pocket-shell](https://github.com/pocket-stack/pocket-shell) and [pocket-stack/pocketjs](https://github.com/pocket-stack/pocketjs) on a **jailbroken iPhone 3GS**.

> Status: **working on a real iPhone 3GS**.  
> Tested on `iPhone2,1 / N88AP / iOS 6.1.6 (10B500)`, framebuffer `320×480 @1x`, renderer `GLES1`.

This repository is not a fork of PocketJS. It contains a reproducible patch, setup instructions, and notes from a real-world port of the existing iPod touch 4 target to the iPhone 3GS.

## Result

Final build/deploy output on the device:

```text
built .../PocketShellTouch.app
PocketShellTouch: Mach-O executable arm_v7
deployed User app ... with byte-exact readback
```

After `launch`, the runtime reported:

```json
{
  "state": "running",
  "renderer": "gles1",
  "clock": "displaylink",
  "raster_density": 1,
  "drawable_width": 320,
  "drawable_height": 480,
  "error": ""
}
```

In other words, Pocket Shell is actually running as a native ARMv7 user app on iOS 6.1.6, rendering through OpenGL ES 1 and using the native iPhone 3GS framebuffer at `320×480 @1x`.

## Tested configuration

### iPhone

- iPhone 3GS
- ProductType: `iPhone2,1`
- HardwareModel: `N88AP`
- iOS: `6.1.6`
- Build: `10B500`
- Jailbreak + Cydia
- AppSync Unified
- OpenSSH
- `ldid`, `uicache`, `uiopen`
- ActivationState on the tested device: `WildcardActivated`

### Mac

- Apple Silicon Mac
- macOS 27
- Bun 1.4.x
- Rust via rustup
- Rust toolchain: `nightly-2026-07-02`
- Xcode **26.6 Apple Silicon** for `ld-classic`
- Xcode 27 can remain installed in parallel, but it is not suitable for this legacy ARMv7 build path
- Homebrew `libimobiledevice`, `libusbmuxd`, `ldid`, `rustup`

## Why the existing iPod touch 4 target is a good base

PocketJS already has a target for the iPod touch 4:

```text
iPod4,1 / N81AP
iOS 6.1.6 / 10B500
320×480 logical
640×960 physical
@2x
```

The iPhone 3GS runs a very similar legacy iOS environment for this use case, but its display is different:

```text
iPhone2,1 / N88AP
iOS 6.1.6 / 10B500
320×480 logical
320×480 physical
@1x
```

So this port reuses the existing iPod touch 4 host/toolchain path and changes only the device identity, physical viewport, and raster density.

---

# Quick path

If the iPhone is already prepared with SSH, AppSync, and enough free space, the main sequence is:

```bash
git clone --recurse-submodules https://github.com/pocket-stack/pocket-shell.git
cd pocket-shell

bun run setup

python3 /path/to/pocketjs-iphone3gs/scripts/apply-iphone3gs-patch.py .

bun run touch guest
bun run touch setup-sources

export POCKETJS_IPHONE4S_IPSW="/path/to/iPhone4,1_6.1.3_10B329_CustomJ.ipsw"
bun run touch prepare-sysroot

export POCKETJS_IPODTOUCH4_UDID="<YOUR_UDID>"

bun run touch doctor

DEVELOPER_DIR=/Applications/Xcode-26.6.app/Contents/Developer \
  bun run touch deploy

DEVELOPER_DIR=/Applications/Xcode-26.6.app/Contents/Developer \
  bun run touch launch
```

The first setup still requires preparing the jailbreak transport, SSH keys, ARMv7 sysroot, and Xcode 26.6. The complete process is documented below.

---

# 1. Prepare the Mac

Install the required Homebrew tools:

```bash
brew install libimobiledevice libusbmuxd rustup ldid bun
```

Add rustup to your PATH:

```bash
echo 'export PATH="$(brew --prefix rustup)/bin:$PATH"' >> ~/.zshrc
export PATH="$(brew --prefix rustup)/bin:$PATH"
```

Install the toolchain expected by the current PocketJS tree:

```bash
rustup toolchain install nightly-2026-07-02
rustup component add rust-src --toolchain nightly-2026-07-02
```

Check USB device detection:

```bash
idevice_id -l
```

Your device UDID should appear. The rest of this guide uses `<YOUR_UDID>` as a placeholder.

---

# 2. Install OpenSSH on the iPhone 3GS

In the tested setup, installing OpenSSH directly from Cydia failed because the old repositories repeatedly timed out. The working workaround was [Legacy iOS Kit](https://github.com/LukeZGD/Legacy-iOS-Kit).

## Using the Legacy iOS Kit SSH ramdisk

```bash
git clone --filter=blob:none https://github.com/LukeZGD/Legacy-iOS-Kit
cd Legacy-iOS-Kit
./restore.sh --no-internet-check --sshrd
```

If the first run only installs dependencies and exits, run the same command again.

For the iPhone 3GS:

1. Enter DFU mode.
2. Select `pwnDFU`.
3. Boot the SSH ramdisk.
4. Choose **Install OpenSSH (iOS 10 and lower)**.
5. After `Done`, choose **Reboot Device**.

After normal iOS boots again:

```bash
iproxy 2222:22
```

In another Terminal window:

```bash
ssh \
  -o HostKeyAlgorithms=+ssh-rsa \
  -o PubkeyAcceptedAlgorithms=+ssh-rsa \
  -p 2222 root@127.0.0.1
```

The default root password on many old jailbreak installations is:

```text
alpine
```

Change it after setup.

Verify the required tools on the iPhone:

```bash
uname -m
which ldid
which uicache
which uiopen
dpkg -l | grep -Ei 'appsync|openssh|openssl'
```

The tested device reported:

```text
iPhone2,1
/usr/bin/ldid
/usr/bin/uicache
/usr/bin/uiopen
AppSync Unified 110.0
OpenSSH 6.7p1-13
OpenSSL 0.9.8zg-13
```

---

# 3. If the root filesystem is 100% full

The iPhone 3GS system partition is very small. Before installing some additional packages, the tested device looked like this:

```text
/dev/disk0s1s1  1.3G  1.3G  0  100% /
/dev/disk0s1s2  6.2G  1.3G  5.0G  21% /private/var
```

Cydia includes its own stashing helper that can move `/Applications` to the larger data partition:

```bash
ls -l /usr/libexec/cydia/free.sh
/usr/libexec/cydia/free.sh
```

After running it, the tested device had:

```text
/dev/disk0s1s1  1.3G  1.1G  174M  87% /
```

and `/Applications` had become a symlink into `/var/stash/...`.

**Do not manually move `/Applications` if the stock Cydia `free.sh` helper is available.**

---

# 4. Clone Pocket Shell

```bash
cd ~/Downloads

git clone --recurse-submodules https://github.com/pocket-stack/pocket-shell.git
cd pocket-shell

bun run setup
```

---

# 5. Apply the iPhone 3GS patch

Clone this repository next to Pocket Shell or use the script from it:

```bash
python3 /path/to/pocketjs-iphone3gs/scripts/apply-iphone3gs-patch.py ~/Downloads/pocket-shell
```

The patch makes four important changes:

1. `iPod4,1 / N81AP` → `iPhone2,1 / N88AP`
2. Physical viewport `640×960` → `320×480`
3. Raster density `2` → `1`
4. `doctor` accepts `WildcardActivated` and no longer requires password authentication to be forcibly disabled, while still requiring public-key SSH

See [PATCHING.md](PATCHING.md) for the exact changes.

Verify the patch:

```bash
grep -nE 'productType|hardwareModel' \
  vendor/pocketjs/tools/ipodtouch4-toolchain.ts

grep -nE 'PHYSICAL_VIEWPORT|RASTER_DENSITY' \
  vendor/pocketjs/tools/ipodtouch4-profile.ts

grep -n 'uname -m' \
  vendor/pocketjs/tools/ipodtouch4.ts
```

Expected values:

```text
productType: "iPhone2,1"
hardwareModel: "N88AP"
PHYSICAL_VIEWPORT = [320, 480]
RASTER_DENSITY = 1
uname -m ... iPhone2,1
```

---

# 6. Create the SSH key used by deploy

PocketJS deploy uses `BatchMode=yes`, so password-only SSH is not sufficient.

```bash
mkdir -p ~/.cache/pocket-stack/ipodtouch4/ssh

ssh-keygen \
  -t rsa \
  -b 2048 \
  -m PEM \
  -N "" \
  -f ~/.cache/pocket-stack/ipodtouch4/ssh/id_rsa
```

With `iproxy 2222:22` running, append the public key to the iPhone:

```bash
cat ~/.cache/pocket-stack/ipodtouch4/ssh/id_rsa.pub | \
ssh \
  -o HostKeyAlgorithms=+ssh-rsa \
  -o PubkeyAcceptedAlgorithms=+ssh-rsa \
  -p 2222 root@127.0.0.1 \
  'umask 077; mkdir -p /var/root/.ssh; cat >> /var/root/.ssh/authorized_keys; chmod 700 /var/root/.ssh; chmod 600 /var/root/.ssh/authorized_keys'
```

Test passwordless authentication:

```bash
ssh \
  -i ~/.cache/pocket-stack/ipodtouch4/ssh/id_rsa \
  -o BatchMode=yes \
  -o HostKeyAlgorithms=+ssh-rsa \
  -o PubkeyAcceptedAlgorithms=+ssh-rsa \
  -p 2222 root@127.0.0.1 \
  'echo POCKETJS-SSH-OK'
```

Expected output:

```text
POCKETJS-SSH-OK
```

Now pin the SSH host key:

```bash
ssh-keyscan -p 2222 -t rsa 127.0.0.1 2>/dev/null | \
sed 's/\[127.0.0.1\]:2222/[127.0.0.1]:2224/' \
> ~/.cache/pocket-stack/ipodtouch4/ssh/known_hosts
```

---

# 7. Build the guest

```bash
cd ~/Downloads/pocket-shell

bun run touch guest
```

With the 3GS profile, the tested build reported:

```text
target=ipodtouch4-dev, raster=1x
...
PocketJS build: done
```

This is an important sanity check: guest assets and fonts are now being generated for `@1x`.

---

# 8. Prepare the ARMv7 sysroot

The PocketJS iPod touch 4 target reuses the validated iPhone 4S iOS 6.1.3 ARMv7 sysroot.

Prepare the pinned sources:

```bash
bun run touch setup-sources
```

Then `prepare-sysroot` will ask for `POCKETJS_IPHONE4S_IPSW`.

## How the working IPSW was produced

Legacy iOS Kit was used **only on the Mac as a source for the sysroot**. This IPSW was never flashed to the iPhone 3GS.

Original target firmware:

```text
iPhone4,1
iOS 6.1.3
10B329
SHA1: 7a62ee60b574301a6aafc48dcc9cccf0894ffb27
```

Run Legacy iOS Kit in no-device mode:

```bash
cd ~/Downloads/Legacy-iOS-Kit

./restore.sh \
  --no-device \
  --device=iPhone4,1 \
  --ecid=1 \
  --jailbreak \
  --no-internet-check
```

Then choose:

```text
Misc Utilities
→ Create Custom IPSW
→ iOS 6.1.3
→ Select Target IPSW
→ Create IPSW
```

The resulting file will look like:

```text
iPhone4,1_6.1.3_10B329_CustomJ.ipsw
```

Point PocketJS at it explicitly:

```bash
export POCKETJS_IPHONE4S_IPSW="/path/to/iPhone4,1_6.1.3_10B329_CustomJ.ipsw"

bun run touch prepare-sysroot
```

A later `doctor` run should show:

```text
[ok] validated iOS 6.1.3 ARMv7 sysroot (shared with iphone4s)
[ok] Apple Csu source
[ok] pinned QuickJS source
```

---

# 9. Xcode 26.6 and ld-classic

This is one of the most important compatibility details.

The tested Mac already had Xcode 27 from the App Store, but the PocketJS legacy ARMv7 build expects `ld-classic`. Xcode 26.6 Apple Silicon was therefore installed side-by-side:

```text
/Applications/Xcode.app        # current Xcode 27
/Applications/Xcode-26.6.app   # used for PocketJS
```

After downloading the `.xip`:

```bash
cd ~/Downloads
xip --expand Xcode_26.6_Apple_silicon.xip
sudo mv Xcode.app /Applications/Xcode-26.6.app
```

Run first-time setup:

```bash
sudo env \
  DEVELOPER_DIR=/Applications/Xcode-26.6.app/Contents/Developer \
  xcodebuild -license accept

sudo env \
  DEVELOPER_DIR=/Applications/Xcode-26.6.app/Contents/Developer \
  xcodebuild -runFirstLaunch
```

Verify the legacy linker:

```bash
DEVELOPER_DIR=/Applications/Xcode-26.6.app/Contents/Developer \
  xcrun --find ld-classic
```

There is no need to change the global `xcode-select`. Setting `DEVELOPER_DIR` for the PocketJS build commands is enough.

---

# 10. Run doctor

```bash
export POCKETJS_IPODTOUCH4_UDID="<YOUR_UDID>"

bun run touch doctor
```

A successful run on the tested setup checked:

```text
[ok] bun
[ok] rustup
[ok] xcrun
[ok] ldid
[ok] idevice_id
[ok] ideviceinfo
[ok] iproxy
[ok] ssh
[ok] scp
[ok] validated iOS 6.1.3 ARMv7 sysroot
[ok] Apple Csu source
[ok] pinned QuickJS source
[ok] USB deployment key
[ok] pinned SSH host key
[ok] device identity: iPhone2,1 6.1.6 (10B500)
[ok] jailbreak transport
[ok] self-signed User app installation (AppSync Unified)
```

If the AppSync line begins with `[ok]`, AppSync was detected. In the current doctor output, the detail text after the colon may still look like an installation hint even when the check succeeded.

---

# 11. Build and deploy

```bash
export POCKETJS_IPODTOUCH4_UDID="<YOUR_UDID>"

DEVELOPER_DIR=/Applications/Xcode-26.6.app/Contents/Developer \
  bun run touch deploy
```

The first native build may require:

```bash
rustup component add rust-src --toolchain nightly-2026-07-02
```

Successful output:

```text
PocketShellTouch: Mach-O executable arm_v7
deployed User app <BUILD_ID> with byte-exact readback
```

---

# 12. Launch

```bash
DEVELOPER_DIR=/Applications/Xcode-26.6.app/Contents/Developer \
  bun run touch launch
```

Verified runtime status:

```json
{
  "state": "running",
  "renderer": "gles1",
  "clock": "displaylink",
  "raster_density": 1,
  "drawable_width": 320,
  "drawable_height": 480,
  "error": ""
}
```

At this point, Pocket Shell is running on the iPhone 3GS.

---

# Useful commands after launch

Check status:

```bash
bun run touch status
```

Capture the framebuffer:

```bash
bun run touch capture
```

Redeploy after changes:

```bash
bun run touch guest

DEVELOPER_DIR=/Applications/Xcode-26.6.app/Contents/Developer \
  bun run touch deploy

DEVELOPER_DIR=/Applications/Xcode-26.6.app/Contents/Developer \
  bun run touch launch
```

---

# What you should NOT commit

Never publish:

- your UDID;
- `~/.cache/pocket-stack/ipodtouch4/ssh/id_rsa`;
- `authorized_keys` if it contains other personal keys;
- Xcode;
- IPSW files;
- private activation records;
- local PocketJS cache directories.

This repository contains only the patch, documentation, and helper scripts.

---

# Troubleshooting

The complete set of real-world problems and fixes is documented in [TROUBLESHOOTING.md](TROUBLESHOOTING.md).

The issues encountered during this port included:

- Cydia could not download OpenSSH;
- OpenSSH had to be installed through the Legacy iOS Kit SSH ramdisk;
- old OpenSSH required RSA compatibility options;
- the root filesystem was 100% full;
- `/usr/libexec/cydia/free.sh` fixed the root partition pressure;
- `ActivationState=WildcardActivated` failed the upstream PocketJS identity check;
- sysroot preparation required a custom iPhone 4S iOS 6.1.3 IPSW;
- AppleDB/raw GitHub DNS lookups in Legacy iOS Kit failed intermittently;
- Xcode 27 was unsuitable for the expected legacy linker path;
- Xcode 26.6 and `ld-classic` were required;
- the Rust nightly toolchain needed the `rust-src` component.

---

# Upstream projects

The actual runtime, shell, and tooling come from these upstream projects:

- [pocket-stack/pocket-shell](https://github.com/pocket-stack/pocket-shell)
- [pocket-stack/pocketjs](https://github.com/pocket-stack/pocketjs)
- [LukeZGD/Legacy-iOS-Kit](https://github.com/LukeZGD/Legacy-iOS-Kit)

This repository documents an experimental iPhone 3GS target built on top of the existing iPod touch 4 workflow.

## Disclaimer

This is an experiment involving legacy jailbroken hardware. Back up the device before changing the jailbreak or system partition. Any command that modifies the system is run at your own risk.

The custom iPhone 4S IPSW mentioned in this guide is used only as a **sysroot source for compilation** and is **not intended to be flashed to an iPhone 3GS**.
