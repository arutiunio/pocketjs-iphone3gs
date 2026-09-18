# PocketJS / Pocket Shell on iPhone 3GS (iOS 6.1.6)

Практический порт и пошаговая инструкция по запуску [pocket-stack/pocket-shell](https://github.com/pocket-stack/pocket-shell) и [pocket-stack/pocketjs](https://github.com/pocket-stack/pocketjs) на **jailbroken iPhone 3GS**.

> Статус: **работает на реальном iPhone 3GS**.  
> Проверено на `iPhone2,1 / N88AP / iOS 6.1.6 (10B500)`, framebuffer `320×480 @1x`, renderer `GLES1`.

Этот репозиторий не является форком PocketJS. Он содержит воспроизводимый патч, инструкции и заметки по реальному переносу существующего iPod touch 4 target на iPhone 3GS.

## Что получилось

Финальный build/deploy на устройстве:

```text
built .../PocketShellTouch.app
PocketShellTouch: Mach-O executable arm_v7
deployed User app ... with byte-exact readback
```

После `launch` runtime вернул:

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

То есть Pocket Shell реально запущен как ARMv7 user app на iOS 6.1.6, рендерит через OpenGL ES 1 и использует родной экран 3GS `320×480 @1x`.

## Проверенная конфигурация

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
- ActivationState в нашем случае: `WildcardActivated`

### Mac

- Apple Silicon Mac
- macOS 27
- Bun 1.4.x
- Rust via rustup
- Rust toolchain: `nightly-2026-07-02`
- Xcode **26.6 Apple Silicon** для `ld-classic`
- Xcode 27 может быть установлен параллельно, но для сборки legacy ARMv7 target не подходит
- Homebrew `libimobiledevice`, `libusbmuxd`, `ldid`, `rustup`

## Почему штатный iPod touch 4 target почти подходит

В PocketJS уже есть target для iPod touch 4:

```text
iPod4,1 / N81AP
iOS 6.1.6 / 10B500
320×480 logical
640×960 physical
@2x
```

У iPhone 3GS для нашей задачи очень похожая legacy iOS среда, но экран другой:

```text
iPhone2,1 / N88AP
iOS 6.1.6 / 10B500
320×480 logical
320×480 physical
@1x
```

Поэтому мы переиспользуем существующий iPod touch 4 host/toolchain path и меняем identity + physical viewport + raster density.

---

# Быстрый путь

Если iPhone уже подготовлен (SSH, AppSync, свободное место), основная последовательность такая:

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

Но первый запуск требует подготовить jailbreak-транспорт, SSH keys, ARMv7 sysroot и Xcode 26.6. Полная инструкция ниже.

---

# 1. Подготовка Mac

Установите Homebrew-инструменты:

```bash
brew install libimobiledevice libusbmuxd rustup ldid bun
```

Добавьте rustup в PATH:

```bash
echo 'export PATH="$(brew --prefix rustup)/bin:$PATH"' >> ~/.zshrc
export PATH="$(brew --prefix rustup)/bin:$PATH"
```

Установите toolchain, который ожидает текущий PocketJS:

```bash
rustup toolchain install nightly-2026-07-02
rustup component add rust-src --toolchain nightly-2026-07-02
```

Проверка USB:

```bash
idevice_id -l
```

Должен появиться UDID устройства. В дальнейших примерах он обозначен как `<YOUR_UDID>`.

---

# 2. OpenSSH на iPhone 3GS

В нашем случае OpenSSH из Cydia не устанавливался: старые репозитории отдавали timeout. Рабочим обходным путём оказался [Legacy iOS Kit](https://github.com/LukeZGD/Legacy-iOS-Kit).

## Через Legacy iOS Kit SSH Ramdisk

```bash
git clone --filter=blob:none https://github.com/LukeZGD/Legacy-iOS-Kit
cd Legacy-iOS-Kit
./restore.sh --no-internet-check --sshrd
```

Если первый запуск только установил dependencies и завершился — запустите команду ещё раз.

Для 3GS:

1. войти в DFU;
2. выбрать `pwnDFU`;
3. загрузить SSH ramdisk;
4. в меню выбрать **Install OpenSSH (iOS 10 and lower)**;
5. после `Done` выбрать **Reboot Device**.

После загрузки обычной iOS:

```bash
iproxy 2222:22
```

В другом Terminal:

```bash
ssh \
  -o HostKeyAlgorithms=+ssh-rsa \
  -o PubkeyAcceptedAlgorithms=+ssh-rsa \
  -p 2222 root@127.0.0.1
```

Стандартный пароль root на старом jailbreak обычно:

```text
alpine
```

Рекомендуется сменить его после настройки.

Проверьте на iPhone:

```bash
uname -m
which ldid
which uicache
which uiopen
dpkg -l | grep -Ei 'appsync|openssh|openssl'
```

В нашем случае:

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

# 3. Если системный раздел забит на 100%

На 3GS root filesystem очень маленький. У нас перед установкой дополнительных компонентов было:

```text
/dev/disk0s1s1  1.3G  1.3G  0  100% /
/dev/disk0s1s2  6.2G  1.3G  5.0G  21% /private/var
```

Cydia умеет штатно перенести `/Applications` на большой data-раздел:

```bash
ls -l /usr/libexec/cydia/free.sh
/usr/libexec/cydia/free.sh
```

После этого у нас стало:

```text
/dev/disk0s1s1  1.3G  1.1G  174M  87% /
```

а `/Applications` превратился в symlink в `/var/stash/...`.

**Не делайте ручной перенос `/Applications`, если доступен штатный `free.sh`.**

---

# 4. Клонируем Pocket Shell

```bash
cd ~/Downloads

git clone --recurse-submodules https://github.com/pocket-stack/pocket-shell.git
cd pocket-shell

bun run setup
```

---

# 5. Применяем патч iPhone 3GS

Скачайте этот репозиторий рядом или используйте файл из него:

```bash
python3 /path/to/pocketjs-iphone3gs/scripts/apply-iphone3gs-patch.py ~/Downloads/pocket-shell
```

Патч делает четыре вещи:

1. `iPod4,1 / N81AP` → `iPhone2,1 / N88AP`;
2. physical viewport `640×960` → `320×480`;
3. raster density `2` → `1`;
4. doctor принимает `WildcardActivated` и не требует принудительно выключать password authentication, сохраняя проверку public-key SSH.

Подробнее: [PATCHING.md](PATCHING.md).

Проверьте:

```bash
grep -nE 'productType|hardwareModel' \
  vendor/pocketjs/tools/ipodtouch4-toolchain.ts

grep -nE 'PHYSICAL_VIEWPORT|RASTER_DENSITY' \
  vendor/pocketjs/tools/ipodtouch4-profile.ts

grep -n 'uname -m' \
  vendor/pocketjs/tools/ipodtouch4.ts
```

Ожидаем:

```text
productType: "iPhone2,1"
hardwareModel: "N88AP"
PHYSICAL_VIEWPORT = [320, 480]
RASTER_DENSITY = 1
uname -m ... iPhone2,1
```

---

# 6. SSH key для автоматического deploy

PocketJS deploy работает в `BatchMode=yes`, поэтому одного входа по паролю недостаточно.

```bash
mkdir -p ~/.cache/pocket-stack/ipodtouch4/ssh

ssh-keygen \
  -t rsa \
  -b 2048 \
  -m PEM \
  -N "" \
  -f ~/.cache/pocket-stack/ipodtouch4/ssh/id_rsa
```

При запущенном `iproxy 2222:22` добавьте ключ на iPhone:

```bash
cat ~/.cache/pocket-stack/ipodtouch4/ssh/id_rsa.pub | \
ssh \
  -o HostKeyAlgorithms=+ssh-rsa \
  -o PubkeyAcceptedAlgorithms=+ssh-rsa \
  -p 2222 root@127.0.0.1 \
  'umask 077; mkdir -p /var/root/.ssh; cat >> /var/root/.ssh/authorized_keys; chmod 700 /var/root/.ssh; chmod 600 /var/root/.ssh/authorized_keys'
```

Проверка входа без пароля:

```bash
ssh \
  -i ~/.cache/pocket-stack/ipodtouch4/ssh/id_rsa \
  -o BatchMode=yes \
  -o HostKeyAlgorithms=+ssh-rsa \
  -o PubkeyAcceptedAlgorithms=+ssh-rsa \
  -p 2222 root@127.0.0.1 \
  'echo POCKETJS-SSH-OK'
```

Ожидаем:

```text
POCKETJS-SSH-OK
```

Теперь pinned host key:

```bash
ssh-keyscan -p 2222 -t rsa 127.0.0.1 2>/dev/null | \
sed 's/\[127.0.0.1\]:2222/[127.0.0.1]:2224/' \
> ~/.cache/pocket-stack/ipodtouch4/ssh/known_hosts
```

---

# 7. Guest build

```bash
cd ~/Downloads/pocket-shell

bun run touch guest
```

На 3GS-профиле в нашем случае build сообщил:

```text
target=ipodtouch4-dev, raster=1x
...
PocketJS build: done
```

Это важная проверка: guest assets и шрифты уже генерируются для `@1x`.

---

# 8. ARMv7 sysroot

PocketJS iPod touch 4 target переиспользует валидированный iPhone 4S iOS 6.1.3 ARMv7 sysroot.

Подготовьте исходники:

```bash
bun run touch setup-sources
```

Затем `prepare-sysroot` попросит `POCKETJS_IPHONE4S_IPSW`.

## Как мы получили подходящий IPSW

Мы использовали Legacy iOS Kit **только на Mac как генератор rootfs source**. Этот IPSW НЕ прошивался на 3GS.

Оригинальный target:

```text
iPhone4,1
iOS 6.1.3
10B329
SHA1: 7a62ee60b574301a6aafc48dcc9cccf0894ffb27
```

Legacy iOS Kit запускался в no-device режиме:

```bash
cd ~/Downloads/Legacy-iOS-Kit

./restore.sh \
  --no-device \
  --device=iPhone4,1 \
  --ecid=1 \
  --jailbreak \
  --no-internet-check
```

Далее:

```text
Misc Utilities
→ Create Custom IPSW
→ iOS 6.1.3
→ Select Target IPSW
→ Create IPSW
```

В результате получился файл вида:

```text
iPhone4,1_6.1.3_10B329_CustomJ.ipsw
```

Передайте его PocketJS явно:

```bash
export POCKETJS_IPHONE4S_IPSW="/path/to/iPhone4,1_6.1.3_10B329_CustomJ.ipsw"

bun run touch prepare-sysroot
```

Проверка через `doctor` должна показать:

```text
[ok] validated iOS 6.1.3 ARMv7 sysroot (shared with iphone4s)
[ok] Apple Csu source
[ok] pinned QuickJS source
```

---

# 9. Xcode 26.6 и ld-classic

Это один из главных нюансов.

У нас был Xcode 27 из App Store, но PocketJS legacy ARMv7 build требует `ld-classic`. Поэтому Xcode 26.6 Apple Silicon был установлен параллельно:

```text
/Applications/Xcode.app        # текущий Xcode 27
/Applications/Xcode-26.6.app   # для PocketJS
```

После скачивания `.xip`:

```bash
cd ~/Downloads
xip --expand Xcode_26.6_Apple_silicon.xip
sudo mv Xcode.app /Applications/Xcode-26.6.app
```

Первичная настройка:

```bash
sudo env \
  DEVELOPER_DIR=/Applications/Xcode-26.6.app/Contents/Developer \
  xcodebuild -license accept

sudo env \
  DEVELOPER_DIR=/Applications/Xcode-26.6.app/Contents/Developer \
  xcodebuild -runFirstLaunch
```

Проверка:

```bash
DEVELOPER_DIR=/Applications/Xcode-26.6.app/Contents/Developer \
  xcrun --find ld-classic
```

Не обязательно менять глобальный `xcode-select`. Для PocketJS достаточно задавать `DEVELOPER_DIR` на конкретную команду.

---

# 10. Doctor

```bash
export POCKETJS_IPODTOUCH4_UDID="<YOUR_UDID>"

bun run touch doctor
```

Успешный doctor в нашем случае проверил:

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

Если последняя строка начинается с `[ok]`, AppSync найден; текст подсказки после двоеточия в текущем doctor может выглядеть как инструкция по установке даже при успешной проверке.

---

# 11. Build + deploy

```bash
export POCKETJS_IPODTOUCH4_UDID="<YOUR_UDID>"

DEVELOPER_DIR=/Applications/Xcode-26.6.app/Contents/Developer \
  bun run touch deploy
```

Первый build может потребовать:

```bash
rustup component add rust-src --toolchain nightly-2026-07-02
```

Успешный результат:

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

Проверенный runtime:

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

Готово: Pocket Shell работает на iPhone 3GS.

---

# Полезные команды после запуска

Status:

```bash
bun run touch status
```

Capture framebuffer:

```bash
bun run touch capture
```

Повторный deploy после изменений:

```bash
bun run touch guest

DEVELOPER_DIR=/Applications/Xcode-26.6.app/Contents/Developer \
  bun run touch deploy

DEVELOPER_DIR=/Applications/Xcode-26.6.app/Contents/Developer \
  bun run touch launch
```

---

# Что НЕ нужно коммитить

Никогда не публикуйте:

- свой UDID;
- `~/.cache/pocket-stack/ipodtouch4/ssh/id_rsa`;
- `authorized_keys`, если там есть другие личные ключи;
- Xcode;
- IPSW;
- приватные activation records;
- локальные cache directories PocketJS.

Этот репозиторий содержит только патч, инструкции и вспомогательные скрипты.

---

# Troubleshooting

Полный журнал проблем и решений: [TROUBLESHOOTING.md](TROUBLESHOOTING.md).

Коротко, реальные проблемы, с которыми мы столкнулись:

- Cydia не могла скачать OpenSSH;
- OpenSSH пришлось установить через Legacy iOS Kit SSH ramdisk;
- старый OpenSSH требует RSA compatibility options;
- root filesystem был заполнен на 100%;
- помог `/usr/libexec/cydia/free.sh`;
- `ActivationState=WildcardActivated` не проходил жёсткую проверку PocketJS;
- sysroot потребовал Custom iPhone 4S 6.1.3 IPSW;
- AppleDB/raw GitHub DNS lookup в Legacy iOS Kit периодически ломался;
- Xcode 27 не подходил из-за legacy linker path;
- понадобился Xcode 26.6 и `ld-classic`;
- Rust nightly потребовал компонент `rust-src`.

---

# Upstream

Все основные технологии принадлежат upstream-проектам:

- [pocket-stack/pocket-shell](https://github.com/pocket-stack/pocket-shell)
- [pocket-stack/pocketjs](https://github.com/pocket-stack/pocketjs)
- [LukeZGD/Legacy-iOS-Kit](https://github.com/LukeZGD/Legacy-iOS-Kit)

Этот репозиторий документирует отдельный экспериментальный iPhone 3GS target на базе существующего iPod touch 4 workflow.

## Дисклеймер

Это эксперимент с legacy jailbroken hardware. Делайте backup устройства. Команды, изменяющие jailbreak/system partition, выполняются на ваш риск. Custom iPhone 4S IPSW в этой инструкции используется как источник sysroot для сборки и **не предназначен для прошивки iPhone 3GS**.
