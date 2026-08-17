# Waking the home PC remotely

Goal: from anywhere, bring `elyes-arch` (the RTX 3060 desktop) up and connect to it.

A Wake-on-LAN magic packet is a layer-2 broadcast, so it has to originate **inside**
the home LAN. The VPS (`elyes-ghazel-server`) cannot send one — it is not on that
network. The Raspberry Pi is the only always-on device that is, which is its whole job
here. It does **not** need to be a Tailscale subnet router; it only needs to be on the
LAN and reachable over the tailnet.

```
laptop/phone ──tailnet──▶ pi-home ──broadcast──▶ elyes-arch
  (anywhere)               (home LAN)              │ boots
                                                   ▼
             ◀──────────── tailnet ───────── ssh / rustdesk
```

Day to day this is one command: `wake` (see `fish/functions/wake.fish`).

---

## 1. On `elyes-arch` — enable Wake-on-LAN

Must be done at the machine, while it is on.

**Wired ethernet is required.** WoL over WiFi needs WoWLAN and is unreliable; treat
it as unsupported.

### BIOS

Enable, names vary by board:

- `Wake on LAN` / `Power On By PCI-E` / `Resume by PCI-E Device`
- **Disable `ErP` / `EuP` / `Deep Sleep`.** This is the single most common reason WoL
  silently fails — those settings cut power to the NIC at shutdown, so nothing is
  listening for the packet.

### Linux

Find the wired interface and its MAC:

```bash
ip -br link                       # e.g. enp5s0
sudo ethtool enp5s0 | grep -i wake
#   Supports Wake-on: pumbg       <- 'g' must appear
#   Wake-on: d                    <- 'd' = currently disabled
```

Enable it for this boot:

```bash
sudo ethtool -s enp5s0 wol g
```

Persist it. The box uses NetworkManager, so set it on the connection rather than
adding a systemd unit:

```bash
nmcli -g NAME,DEVICE connection show --active
sudo nmcli connection modify "<connection-name>" 802-3-ethernet.wake-on-lan magic
```

Verify after a reboot that `ethtool` reports `Wake-on: g`.

Record the MAC into `fish/functions/wake.fish` (`set -l macs arch:<MAC>`).

---

## 2. On `elyes-arch` — RustDesk without manual launching

```bash
sudo systemctl enable --now rustdesk
systemctl status rustdesk
```

Then open RustDesk once and set a **permanent password** (Settings → Security), or
unattended access will not work.

> **Wayland caveat.** The box runs Hyprland. RustDesk drives Wayland through the
> pipewire portal, which is flaky, and it cannot show the SDDM login screen at all —
> so after a cold wake you may reach a login prompt you cannot type into. Options:
> enable SDDM autologin, or use `ssh` for anything that does not genuinely need a
> desktop. `ssh` over the tailnet is the reliable path and needs none of this.

---

## 3. On the Pi

Raspberry Pi OS Lite 64-bit is plenty — this only sends UDP broadcasts.

```bash
sudo hostnamectl set-hostname pi-home      # matches the default in wake.fish

curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up --ssh
```

`--ssh` turns on Tailscale SSH, so `wake` can reach the Pi with tailnet identity and
no key management.

Prefer wired ethernet for the Pi too — a WiFi client sending LAN broadcasts is one
more thing that can quietly not work.

No `wakeonlan` package is needed: `wake` pipes a short Python script over SSH, and
python3 ships with Raspberry Pi OS.

**SD card:** a Pi 3 running anything that logs will eventually kill its card. If this
grows past WoL, boot from a USB SSD or install `log2ram` first.

---

## 4. Verify

```bash
wake --status     # is elyes-arch up?
wake              # send the packet, wait for it to join the tailnet
```

If it times out, in order of likelihood:

1. `ErP` / `Deep Sleep` still enabled in BIOS
2. `ethtool` shows `Wake-on: d` (the NetworkManager setting did not persist)
3. Machine is on WiFi, not wired
4. Wrong MAC — must be the **wired** NIC, not a WiFi or virtual `docker0` address
