-- https://wiki.hypr.land/Configuring/Basics/Variables/
hl.config({
    general = {
        gaps_in  = 6,
        gaps_out = 10,
        col = {
            active_border   = "rgba(ffffffcc)",
            inactive_border = "rgba(ffffff18)",
        },
        border_size      = 2,
        layout           = "dwindle",
        resize_on_border = true,
    },
    xwayland = {
        force_zero_scaling = true,
    },
})
