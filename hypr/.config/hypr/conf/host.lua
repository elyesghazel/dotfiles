-- Host-specific overrides (laptop: eDP-1)
hl.monitor({ output = "eDP-1", mode = "1920x1080", position = "0x0", scale = 1.0 })

hl.config({
    input = {
        kb_layout     = "ch",
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
