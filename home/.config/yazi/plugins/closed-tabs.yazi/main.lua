--- closed-tabs: remember tabs as they are closed (Ctrl+C, q, Q) and bring them
--- back with Ctrl+Shift+T, most recently closed first — like a browser.
--- The list is kept in ~/.local/state/yazi/closed-tabs, so it survives quitting
--- yazi: reopening yazi and pressing Ctrl+Shift+T restores the last folder.
---   plugin closed-tabs close     -- remember the current tab, then close it
---   plugin closed-tabs quit      -- remember every open tab, then quit
---   plugin closed-tabs quit-no-cwd
---   plugin closed-tabs restore   -- reopen the most recently closed tab
local STATE = os.getenv("HOME") .. "/.local/state/yazi/closed-tabs"
local MAX = 50

local snapshot = ya.sync(function(_, all)
	local function one(tab)
		local h = tab.current.hovered
		return tostring(tab.current.cwd) .. "\t" .. (h and tostring(h.url) or "")
	end
	local out = {}
	if all then
		for i = 1, #cx.tabs do
			out[#out + 1] = one(cx.tabs[i])
		end
	else
		out[1] = one(cx.active)
	end
	return out
end)

local function load()
	local lines, f = {}, io.open(STATE, "r")
	if f then
		for line in f:lines() do
			if line ~= "" then lines[#lines + 1] = line end
		end
		f:close()
	end
	return lines
end

local function save(lines)
	while #lines > MAX do table.remove(lines, 1) end
	local f = io.open(STATE, "w")
	if f then
		f:write(table.concat(lines, "\n"), #lines > 0 and "\n" or "")
		f:close()
	end
end

local function remember(all)
	local lines = load()
	for _, l in ipairs(snapshot(all)) do lines[#lines + 1] = l end
	save(lines)
end

return {
	entry = function(_, job)
		local action = job.args[1]
		if action == "close" then
			remember(false)
			ya.emit("close", {})
		elseif action == "quit" or action == "quit-no-cwd" then
			remember(true)
			ya.emit("quit", { no_cwd_file = action == "quit-no-cwd" })
		elseif action == "restore" then
			local lines = load()
			local last = table.remove(lines)
			if not last then
				return ya.notify { title = "탭 복구", content = "다시 열 탭이 없습니다", timeout = 2 }
			end
			save(lines)
			local cwd, hovered = last:match("^(.-)\t(.*)$")
			ya.emit("tab_create", { cwd })
			if hovered and hovered ~= "" then
				ya.emit("reveal", { hovered })
			end
		end
	end,
}
