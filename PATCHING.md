# Patching PocketJS for iPhone 3GS

This port intentionally reuses PocketJS's existing `ipodtouch4` target instead of adding a brand-new target.

## Files changed

### `vendor/pocketjs/tools/ipodtouch4-toolchain.ts`

Change device identity:

```ts
export const IPODTOUCH4_DEVICE = {
  productType: "iPhone2,1",
  hardwareModel: "N88AP",
  productVersion: "6.1.6",
  buildVersion: "10B500",
} as const;
```

### `vendor/pocketjs/tools/ipodtouch4-profile.ts`

Change physical framebuffer and raster density:

```ts
export const IPODTOUCH4_PHYSICAL_VIEWPORT = [320, 480] as const;
export const IPODTOUCH4_RASTER_DENSITY = 1;
```

Keep logical portrait/landscape dimensions unchanged:

```ts
export const IPODTOUCH4_LOGICAL_VIEWPORT = [320, 480] as const;
export const IPODTOUCH4_LANDSCAPE_VIEWPORT = [480, 320] as const;
```

### `vendor/pocketjs/tools/ipodtouch4.ts`

#### Device identity

Accept the 3GS machine identifier:

```ts
test "$(uname -m)" = iPhone2,1
```

#### Activation state

Our device reports `WildcardActivated`, while upstream checks only `Activated`.

Use:

```ts
!["Activated", "WildcardActivated"].includes(observed.activation)
```

and update the diagnostic text to say:

```text
Activated/WildcardActivated
```

#### SSH daemon check

Upstream requires:

```text
PasswordAuthentication no
```

The 3GS setup used here still has password login enabled, while deploy itself uses a dedicated SSH key with `BatchMode=yes`.

Keep the public-key requirement:

```sh
/usr/sbin/sshd -T | grep -q '^pubkeyauthentication yes$'
```

but remove the hard requirement that password authentication be disabled.

This is a compatibility choice for this tested setup, not a recommendation to leave password login enabled permanently. Change the root password and harden SSH if the device is exposed beyond USB-only usage.

## Apply automatically

Use:

```bash
python3 scripts/apply-iphone3gs-patch.py /path/to/pocket-shell
```

The script is idempotent for an already-patched checkout.
