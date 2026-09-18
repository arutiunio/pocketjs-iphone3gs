#!/usr/bin/env python3
from pathlib import Path
import sys

if len(sys.argv) != 2:
    raise SystemExit("usage: apply-iphone3gs-patch.py /path/to/pocket-shell")

root = Path(sys.argv[1]).expanduser().resolve()
pocketjs = root / "vendor" / "pocketjs"

files = {
    "toolchain": pocketjs / "tools" / "ipodtouch4-toolchain.ts",
    "profile": pocketjs / "tools" / "ipodtouch4-profile.ts",
    "tool": pocketjs / "tools" / "ipodtouch4.ts",
}

for name, path in files.items():
    if not path.exists():
        raise SystemExit(f"missing {name}: {path}")

def replace_once(text, old, new, label):
    if new in text:
        return text, False
    if old not in text:
        raise SystemExit(f"could not find expected pattern for {label}")
    return text.replace(old, new, 1), True

changed = []

p = files["toolchain"]
s = p.read_text()
for old, new, label in [
    ('productType: "iPod4,1"', 'productType: "iPhone2,1"', "ProductType"),
    ('hardwareModel: "N81AP"', 'hardwareModel: "N88AP"', "HardwareModel"),
]:
    s, did = replace_once(s, old, new, label)
    if did: changed.append(label)
p.write_text(s)

p = files["profile"]
s = p.read_text()
for old, new, label in [
    ('IPODTOUCH4_PHYSICAL_VIEWPORT = [640, 960] as const',
     'IPODTOUCH4_PHYSICAL_VIEWPORT = [320, 480] as const', "physical viewport"),
    ('IPODTOUCH4_RASTER_DENSITY = 2',
     'IPODTOUCH4_RASTER_DENSITY = 1', "raster density"),
]:
    s, did = replace_once(s, old, new, label)
    if did: changed.append(label)
p.write_text(s)

p = files["tool"]
s = p.read_text()

s, did = replace_once(
    s,
    'observed.activation !== "Activated"',
    '!["Activated", "WildcardActivated"].includes(observed.activation)',
    "activation state",
)
if did: changed.append("activation state")

s, did = replace_once(
    s,
    '(${DEVICE_BUILD}) Activated`,',
    '(${DEVICE_BUILD}) Activated/WildcardActivated`,',
    "activation diagnostic",
)
if did: changed.append("activation diagnostic")

s, did = replace_once(
    s,
    'test \"$(uname -m)\" = iPod4,1',
    'test \"$(uname -m)\" = iPhone2,1',
    "uname identity",
)
if did: changed.append("uname identity")

password_line = (
    '        "/usr/sbin/sshd -T | grep -q \'^passwordauthentication no$\'; '
    'echo jailbreak-key-only-usb-ready",'
)
replacement = '        "echo jailbreak-key-usb-ready",'
if replacement not in s:
    if password_line not in s:
        raise SystemExit("could not find passwordauthentication doctor check")
    s = s.replace(password_line, replacement, 1)
    changed.append("SSH doctor policy")

p.write_text(s)

print("PocketJS iPhone 3GS patch applied.")
if changed:
    print("Changed:")
    for item in changed:
        print(f"  - {item}")
else:
    print("Checkout was already patched.")
