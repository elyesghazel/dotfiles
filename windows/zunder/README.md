# zunder plugins on Windows

zunder on Windows runs the same plugins as Arch (`zunder/.config/zunder/plugins`) inside WSL.
Each plugin gets a `.cmd` wrapper in `%APPDATA%\zunder\plugins` that calls `zunder-wsl`,
which runs the plugin and rewrites its `run`/`term` actions back into WSL. `bin/` has
`notify-send`, `wl-copy` and `wl-paste` stand-ins that talk to Windows.

Setup, once, inside WSL (Ubuntu):

```sh
ln -sfn ~/dotfiles/windows/zunder/zunder-wsl ~/.local/bin/zunder-wsl
zunder-wsl --sync
```

After adding or renaming a plugin, run `zunder-wsl --sync` again (then `zunder reload`, or
reopen zunder). Edits to a plugin's code need nothing.
