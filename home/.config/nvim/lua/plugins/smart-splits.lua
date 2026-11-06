-- Ctrl+h/j/k/l moves between Neovim splits and, at the edge, on into the
-- neighbouring kitty split (kitty.conf passes these keys to nvim while nvim is
-- focused, and handles them itself otherwise). Replaces LazyVim's Ctrl+h/j/k/l.
-- Talks to kitty over its remote-control socket (listen_on in kitty.conf).
return {
  {
    "smart-splits-nvim/smart-splits.nvim",
    lazy = false, -- must start with nvim so kitty knows it is focused (IS_NVIM)
    dependencies = {
      { "smart-splits-nvim/backend-kitty", module = "smart-splits-backend-kitty" },
    },
    opts = {
      -- only inside kitty with its socket; elsewhere plain window movement
      -- (without this check it warns at every start outside kitty)
      mux = vim.env.KITTY_LISTEN_ON and { backend = "smart-splits-backend-kitty" } or nil,
    },
    keys = {
      { "<C-h>", function() require("smart-splits").move_cursor_left() end, desc = "Go to Left Window" },
      { "<C-j>", function() require("smart-splits").move_cursor_down() end, desc = "Go to Lower Window" },
      { "<C-k>", function() require("smart-splits").move_cursor_up() end, desc = "Go to Upper Window" },
      { "<C-l>", function() require("smart-splits").move_cursor_right() end, desc = "Go to Right Window" },
    },
  },
}
