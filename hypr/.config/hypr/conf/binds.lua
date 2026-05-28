-- https://wiki.hypr.land/Configuring/Basics/Binds/
local mod         = "SUPER"
local terminal    = "kitty"
local fileManager = "nautilus"
local menu        = "vicinae toggle"
local vicinaeClip = "vicinae deeplink vicinae://extensions/vicinae/clipboard/history"
local qsHyprview  = "/home/elyes/apps/qs-hyprview"

local function qs_cmd(mode)
    return ("quickshell ipc -p %s call expose toggle '%s'"):format(qsHyprview, mode)
end

-- laptop brightness
hl.bind("XF86MonBrightnessUp",   hl.dsp.exec_cmd("brightnessctl set 5%+"), { locked = true, repeating = true })
hl.bind("XF86MonBrightnessDown", hl.dsp.exec_cmd("brightnessctl set 5%-"), { locked = true, repeating = true })

-- apps
hl.bind(mod .. " + RETURN",  hl.dsp.exec_cmd(terminal))
hl.bind(mod .. " + E",       hl.dsp.exec_cmd(fileManager))
hl.bind(mod .. " + B",       hl.dsp.exec_cmd("zen-browser"))
hl.bind(mod .. " + V",       hl.dsp.exec_cmd(vicinaeClip))
hl.bind("ALT + SPACE",       hl.dsp.exec_cmd(menu))
hl.bind(mod .. " + ALT + W", hl.dsp.exec_cmd("swww img $(find ~/.config/ml4w/wallpapers/ -type f | shuf -n 1)"))

-- session management
hl.bind(mod .. " + Q",         hl.dsp.window.close())
hl.bind(mod .. " + C",         hl.dsp.window.close())
hl.bind(mod .. " + M",         hl.dsp.exec_cmd("hyprctl dispatch exit"))
hl.bind(mod .. " + L",         hl.dsp.exec_cmd("hyprlock"))
hl.bind(mod .. " + BACKSPACE", hl.dsp.exec_cmd("wlogout"))

-- window states
hl.bind(mod .. " + F",     hl.dsp.window.fullscreen())
hl.bind(mod .. " + space", hl.dsp.window.float({ action = "toggle" }))
hl.bind(mod .. " + P",     hl.dsp.window.pseudo())

-- focus movement
hl.bind(mod .. " + left",  hl.dsp.focus({ direction = "left"  }))
hl.bind(mod .. " + right", hl.dsp.focus({ direction = "right" }))
hl.bind(mod .. " + up",    hl.dsp.focus({ direction = "up"    }))
hl.bind(mod .. " + down",  hl.dsp.focus({ direction = "down"  }))

-- window movement
hl.bind(mod .. " + SHIFT + left",  hl.dsp.window.move({ direction = "left"  }))
hl.bind(mod .. " + SHIFT + right", hl.dsp.window.move({ direction = "right" }))
hl.bind(mod .. " + SHIFT + up",    hl.dsp.window.move({ direction = "up"    }))
hl.bind(mod .. " + SHIFT + down",  hl.dsp.window.move({ direction = "down"  }))

-- workspaces 1–10
for i = 1, 10 do
    local key = i % 10  -- 10 maps to key "0"
    hl.bind(mod .. " + " .. key,         hl.dsp.focus({ workspace = i }))
    hl.bind(mod .. " + SHIFT + " .. key, hl.dsp.window.move({ workspace = i }))
end

-- special workspace (minimized scratchpad)
hl.bind(mod .. " + H",         hl.dsp.window.move({ workspace = "special:minimized" }))
hl.bind(mod .. " + SHIFT + H", hl.dsp.workspace.toggle_special("minimized"))

-- media control
hl.bind("XF86AudioRaiseVolume", hl.dsp.exec_cmd("wpctl set-volume -l 1.4 @DEFAULT_AUDIO_SINK@ 5%+"), { locked = true, repeating = true })
hl.bind("XF86AudioLowerVolume", hl.dsp.exec_cmd("wpctl set-volume -l 1.4 @DEFAULT_AUDIO_SINK@ 5%-"), { locked = true, repeating = true })
hl.bind("XF86AudioMute",        hl.dsp.exec_cmd("wpctl set-mute @DEFAULT_AUDIO_SINK@ toggle"),       { locked = true })
hl.bind("XF86AudioPlay",        hl.dsp.exec_cmd("playerctl play-pause"),                             { locked = true })
hl.bind("XF86AudioNext",        hl.dsp.exec_cmd("playerctl next"),                                   { locked = true })
hl.bind("XF86AudioPrev",        hl.dsp.exec_cmd("playerctl previous"),                               { locked = true })
hl.bind("mouse:274",            hl.dsp.exec_cmd("wl-copy -pc"),                                      { consuming = false })

-- screenshots
hl.bind(mod .. " + SHIFT + S", hl.dsp.exec_cmd([[grim -g "$(slurp -w 0)" - | wl-copy]]))
hl.bind(mod .. " + S",         hl.dsp.exec_cmd("grim - | wl-copy"))
hl.bind(mod .. " + ALT + S",   hl.dsp.exec_cmd([[grim -g "$(slurp)" ~/Pictures/$(date +%Y%m%d_%H%M%S).png]]))

-- mouse window management
hl.bind(mod .. " + mouse:272", hl.dsp.window.drag(),   { mouse = true })
hl.bind(mod .. " + mouse:273", hl.dsp.window.resize(), { mouse = true })

-- hyprview
hl.bind(mod .. " + TAB", hl.dsp.exec_cmd(qs_cmd("smartgrid")))
hl.bind(mod .. " + Escape", hl.dsp.exec_cmd(("quickshell ipc -p %s call expose close"):format(qsHyprview)))
hl.bind(mod .. " + G",   hl.dsp.exec_cmd(qs_cmd("spiral")))
hl.bind(mod .. " + T",   hl.dsp.exec_cmd(qs_cmd("masonry")))
hl.bind(mod .. " + A",   hl.dsp.exec_cmd(qs_cmd("smartgrid")))
hl.bind(mod .. " + W",   hl.dsp.exec_cmd(qs_cmd("columnar")))
hl.bind(mod .. " + F2",  hl.dsp.exec_cmd(qs_cmd("hero")))
