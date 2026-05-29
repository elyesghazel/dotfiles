local qsHyprview = "/home/elyes/apps/qs-hyprview"

local function qs_cmd(mode)
    return ("quickshell ipc -p %s call expose toggle '%s'"):format(qsHyprview, mode)
end

hl.config({
    gestures = {
        workspace_swipe_distance                = 150,
        workspace_swipe_min_speed_to_force      = 10,
        workspace_swipe_cancel_ratio            = 0.2,
        workspace_swipe_forever                 = true,
        workspace_swipe_create_new              = false,
        workspace_swipe_direction_lock          = false,
        workspace_swipe_direction_lock_threshold = 0,
    }
})

hl.gesture({ fingers = 3, direction = "horizontal", action = "workspace" })
hl.gesture({
    fingers   = 3,
    direction = "up",
    action    = function() hl.exec_cmd(qs_cmd("smartgrid")) end,
})

hl.gesture({
    fingers   = 3,
    direction = "down",
    action    = function()
        hl.exec_cmd(("quickshell ipc -p %s call expose close"):format(qsHyprview))
    end,
})
