-- Host-specific overrides (laptop: eDP-1)
hl.monitor({ output = "eDP-1", mode = "1920x1080", position = "0x0", scale = 1.0 })

-- Desktop monitors at 144Hz (HDMI-A-2 + DP-2)
hl.monitor({ output = "HDMI-A-2", mode = "1920x1080@144", position = "0x0",    scale = 1.0 })
hl.monitor({ output = "DP-2",     mode = "1920x1080@144", position = "1920x0", scale = 1.0 })

hl.config({
    input = {
        sensitivity   = 0.3,
        accel_profile = "adaptive",
        touchpad = {
            natural_scroll = true,
            scroll_factor  = 0.5,
        },
    },
    misc = {
        mouse_move_enables_dpms = true,
        key_press_enables_dpms  = true,
    },
})
