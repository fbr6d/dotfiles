-- Keymaps are automatically loaded on the VeryLazy event
-- Default keymaps that are always set: https://github.com/LazyVim/LazyVim/blob/main/lua/lazyvim/config/keymaps.lua
-- Add any additional keymaps here

-- Key descriptions in Korean (which-key popup, F1 list); see config/keymap_ko.lua
require("config.keymap_ko_apply").setup()

-- F1: searchable list of every key mapping (LazyVim's built-in keymaps picker),
-- the same key that shows kitty's and yazi's shortcut lists
vim.keymap.set({ "n", "i", "v" }, "<F1>", function()
  -- list across the full width (descriptions fit), source preview below it
  Snacks.picker.keymaps({ layout = { preset = "vertical" } })
end, { desc = "Shortcut list" })

-- F2: show / hide inferred types next to the code (LSP inlay hints, same as <leader>uh)
Snacks.toggle.inlay_hints():map("<F2>", { mode = { "n", "i" } })

-- x / X delete characters without copying them (black-hole register), so they
-- don't overwrite the clipboard
vim.keymap.set({ "n", "x" }, "x", '"_x', { desc = "Delete char (no copy)" })
vim.keymap.set({ "n", "x" }, "X", '"_X', { desc = "Delete char before (no copy)" })

-- Recent commands with what they do, bottom right (<leader>uk toggles); see config/key_history.lua
require("config.key_history")
