-- https://wiki.hypr.land/Configuring/Basics/Variables/
hl.config({
    general = {
        gaps_in  = 5,
        gaps_out = 15,
        col = {
            active_border   = { colors = { "rgba(cba6f7ff)", "rgba(89b4faff)" }, angle = 45 },
            inactive_border = "rgba(45475aaa)",
        },
        border_size      = 2,
        layout           = "dwindle",
        resize_on_border = true,
    },
    xwayland = {
        force_zero_scaling = true,
    },
})
