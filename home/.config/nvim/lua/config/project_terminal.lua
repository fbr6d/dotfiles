-- nvim starts maximized, and Ctrl+/ opens a shell in nvim's current folder as a kitty split on the right
-- (40%), replacing LazyVim's terminal inside nvim. If a split is already to the
-- right, Ctrl+/ jumps to it instead (back to nvim: Ctrl+h). Needs kitty's
-- remote-control socket (listen_on in kitty.conf); elsewhere LazyVim's own
-- terminal opens as before.
local M = {}

function M.open()
  local me = vim.env.KITTY_WINDOW_ID
  if not (vim.env.KITTY_LISTEN_ON and me) then
    Snacks.terminal(nil, { cwd = LazyVim.root() })
    return
  end
  local cwd = vim.fn.getcwd() -- read here: vim.fn can't be called in the callback
  vim.system({ "kitty", "@", "focus-window", "--match", "neighbor:right" }, { text = true }, function(r)
    if r.code ~= 0 then -- nothing to the right yet
      vim.system({ "kitty", "@", "launch", "--location=vsplit", "--bias=40",
        "--next-to", "id:" .. me, "--cwd", cwd })
    end
  end)
end

-- nvim always runs maximized: maximize this kitty's Hyprland window at start
-- (only when it is the focused window and not maximized / fullscreen yet)
local pid = tonumber(vim.env.KITTY_PID)
if pid and #vim.api.nvim_list_uis() > 0 then
  vim.system({ "hyprctl", "-j", "activewindow" }, { text = true }, function(r)
    local ok, win = pcall(vim.json.decode, r.stdout or "")
    if ok and type(win) == "table" and win.pid == pid and win.fullscreen == 0 then
      vim.system({ "hyprctl", "dispatch", 'hl.dsp.window.fullscreen({ mode = "maximized" })' })
    end
  end)
end

for _, lhs in ipairs({ "<C-/>", "<C-_>" }) do -- <C-_> is what Ctrl+/ sends in some terminals
  vim.keymap.set({ "n", "i" }, lhs, M.open, { desc = "Terminal (kitty split, right)" })
end

return M
