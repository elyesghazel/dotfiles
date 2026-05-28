hl.config({
    decoration = {
        rounding           = 2,
        active_opacity     = 0.98,
        inactive_opacity   = 0.92,
        fullscreen_opacity = 1.0,
        blur = {
            enabled           = true,
            size              = 5,
            passes            = 2,
            new_optimizations = true,
            xray              = false,
        },
        shadow = {
            enabled      = true,
            range        = 14,
            render_power = 3,
            color        = "rgba(0, 0, 0, 0.40)",
        },
    },
})
