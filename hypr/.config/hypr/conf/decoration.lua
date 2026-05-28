hl.config({
    decoration = {
        rounding           = 15,
        active_opacity     = 0.9,
        inactive_opacity   = 0.75,
        fullscreen_opacity = 1.0,
        blur = {
            enabled           = true,
            size              = 7,
            passes            = 3,
            new_optimizations = true,
            xray              = true,
        },
        shadow = {
            enabled      = true,
            range        = 20,
            render_power = 3,
            color        = "rgba(0, 0, 0, 0.5)",
        },
    },
})
