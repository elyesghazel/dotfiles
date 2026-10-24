# label - Y41BT thermal label printer

CLI for the YXWL **Y41BT** 4x6 label printer (USB `5958:0041`, sold as KNAON / ByteCintia, vendor
app "FlashLabel Pro"). Reverse engineered 2026-10-14: it speaks plain **TSPL** over USB
(`/dev/usb/lp0`, kernel `usblp`). No driver, no CUPS, no vendor app.

```
label shipping.pdf                 # one label per PDF page, roll auto-detected from page size
label photo.png                    # image, rotated + scaled, dithered
label -t "FRAGILE\nTHIS SIDE UP"   # big centred text
label -s 60x80 file.pdf            # force the roll
label --preview file.pdf           # /tmp/label-preview-N.png, prints nothing
label --check                      # printer connected + writable?
```

Rolls (`WIDTHxHEIGHT` mm as they leave the printer, 203 dpi = 8 dots/mm):

| roll | WebStamp PDF | status |
|---|---|---|
| `100x150` | 150x100 page (EU, CN22) | verified |
| `60x80` | 80x60 page (CH A-Post) | **untested** - first print may need an X offset if the roll sits off-centre |

Auto-detect refuses a mix of sizes in one call: different rolls, print them separately.

## Files

- `.local/bin/label` - the CLI (Python + Pillow, `pdftoppm` from poppler)
- `.local/bin/label-remote` - forced command for the VPS print key (see below)

Stow with `stow --no-folding label`.

## Device access

`/dev/usb/lp0` is `root:lp 0660`. Rule in `/etc/udev/rules.d/70-y41bt.rules`:

```
SUBSYSTEM=="usbmisc", ATTRS{idVendor}=="5958", ATTRS{idProduct}=="0041", TAG+="uaccess", GROUP="users", MODE="0660"
```

`uaccess` only covers a logged-in desktop session. Remote printing after Wake-on-LAN happens
with nobody logged in, hence `GROUP="users"` (elyes is in `users`). After editing:
`sudo udevadm control --reload && sudo udevadm trigger -s usbmisc`.

## Remote printing (slideplate-ship)

The VPS prints through `~/.ssh/authorized_keys`:

```
command="/home/elyes/.local/bin/label-remote",restrict ssh-ed25519 ... slideplate-ship-print
```

That key can only run `check` or `print <auto|100x150|60x80>` with a PDF on stdin - no shell,
no forwarding. The pipeline around it lives on the VPS: `~/agents/slideplate-tools/slideplate-ship/README.md` (Forgejo `elyes/slideplate-tools`).

## Protocol notes

- Status queries (`ESC !?`, `~!T`, ESC/POS `DLE EOT`) get no reply over USB - don't rely on them.
- `BITMAP x,y,width_bytes,height,0,<data>`: bit 1 = white, 0 = black (= PIL mode "1" bytes as-is).
- BLE: advertises `Y41BT-1B7B_LE`, service `0x18F0`. Probably the same TSPL on char `0x2AF1`, untested
  (from the bedroom the signal is ~-98 dBm and connections drop).
- Public, server-free copy of this tool: `~/projects/tspl-label`.
