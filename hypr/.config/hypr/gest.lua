hl.gesture({
  fingers = 3,
  direction = "up",
  action = function()
    hl.notification.create({ text = "I just swiped on my trackpad!", duration = 5000, icon = "ok" })
  end
})
