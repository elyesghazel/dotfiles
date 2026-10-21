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

-- zunder opens and closes instantly instead of sliding and fading in
hl.layer_rule({
    name    = "zunder-no-anim",
    match   = { namespace = "^zunder$" },
    no_anim = true,
})
