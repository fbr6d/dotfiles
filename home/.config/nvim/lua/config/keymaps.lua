-- Keymaps are automatically loaded on the VeryLazy event
-- Default keymaps that are always set: https://github.com/LazyVim/LazyVim/blob/main/lua/lazyvim/config/keymaps.lua
-- Add any additional keymaps here

-- F1: searchable list of every key mapping (LazyVim's built-in keymaps picker),
-- the same key that shows kitty's and yazi's shortcut lists
vim.keymap.set({ "n", "i", "v" }, "<F1>", function() Snacks.picker.keymaps() end, { desc = "Shortcut list" })
