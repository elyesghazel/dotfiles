local qsHyprview = "/home/elyes/apps/qs-hyprview"

local function qs_cmd(mode)
    return ("quickshell ipc -p %s call expose toggle '%s'"):format(qsHyprview, mode)
end

hl.gesture({ fingers = 3, direction = "horizontal", action = "workspace" })
hl.gesture({
    fingers   = 3,
    direction = "up",
    action    = function() hl.exec_cmd(qs_cmd("smartgrid")) end,
})
