-- Run by confirm-passkey.sh through `hs -c`, after the user clicked the
-- approval notification. Finds Chrome's "Bitwarden" passkey window and presses
-- the entry whose accessible text contains PASSKEY_MATCH, through the
-- accessibility API instead of screen coordinates, so window size and the
-- "started debugging" banner don't matter. Returns "pressed" or an error.
local match = PASSKEY_MATCH
local chrome = hs.application.get("com.google.Chrome")
if not chrome then return "chrome not running" end
local app = hs.axuielement.applicationElement(chrome)
-- Chrome builds its web-content AX tree only when an assistive client asks;
-- for the Bitwarden popout only AXEnhancedUserInterface exposed the page.
app:setAttributeValue("AXManualAccessibility", true)
app:setAttributeValue("AXEnhancedUserInterface", true)

local win
for _, w in ipairs(app:attributeValue("AXWindows") or {}) do
  if (w:attributeValue("AXTitle") or ""):find("^Bitwarden") then win = w break end
end
if not win then return "no Bitwarden window" end

local function text(e)
  return table.concat({ e:attributeValue("AXTitle") or "", e:attributeValue("AXDescription") or "",
    e:attributeValue("AXValue") or "" }, " ")
end
-- Depth-first; returns the first pressable element containing the match text.
local function find(e, depth)
  if depth > 40 then return nil end
  local role = e:attributeValue("AXRole") or ""
  if (role == "AXButton" or role == "AXLink") and text(e):find(match, 1, true) then return e end
  for _, c in ipairs(e:attributeValue("AXChildren") or {}) do
    local hit = find(c, depth + 1)
    if hit then return hit end
  end
  -- a button whose label sits in a child static text
  if role == "AXButton" then
    for _, c in ipairs(e:attributeValue("AXChildren") or {}) do
      if text(c):find(match, 1, true) then return e end
    end
  end
  return nil
end

local deadline = hs.timer.secondsSinceEpoch() + 5
local target
repeat
  target = find(win, 0)
  if not target then hs.timer.usleep(250000) end
until target or hs.timer.secondsSinceEpoch() > deadline
if not target then return "no passkey entry matching " .. match end
target:performAction("AXPress")
return "pressed"
