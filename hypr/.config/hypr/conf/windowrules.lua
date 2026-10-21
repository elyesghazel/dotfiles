-- https://wiki.hypr.land/Configuring/Basics/Window-Rules/
-- hl.window_rule({
--     name  = "example",
--     match = { class = "^myapp$" },
--     float = true,
-- })

hl.window_rule({
    name   = "zunder-settings",
    match  = { title = "^zunder settings$" },
    float  = true,
    size   = "980 660",
    center = true,
})

-- zunder fades in and out quickly instead of sliding (speed: fadeLayersIn/Out in animations.lua)
hl.layer_rule({
    name      = "zunder-fade",
    match     = { namespace = "^zunder$" },
    animation = "fade",
})
