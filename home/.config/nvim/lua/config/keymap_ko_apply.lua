-- Show key mapping descriptions in Korean (table: config/keymap_ko.lua).
-- Nothing in the plugins is edited:
--   * which-key popup: a function added to which-key's own `replace.desc` list
--   * real mappings (F1 shortcut list, :map): desc swapped in place with mapset(),
--     again whenever plugins load or an LSP attaches and adds new mappings
local ko = require("config.keymap_ko")
ko["noice"] = ko["+noice"]

local M = {}
local modes = { "n", "i", "v", "x", "s", "o", "t", "c" }

local function swap(map, mode, buf)
  local new = map.desc and ko[map.desc]
  if not new then
    return
  end
  local full = vim.fn.maparg(map.lhs, mode, false, true)
  if vim.tbl_isempty(full) or full.desc ~= map.desc then
    return
  end
  if buf and full.buffer == 0 then
    return
  end
  full.desc = new
  pcall(vim.fn.mapset, mode, false, full)
end

function M.keymaps(buf)
  for _, mode in ipairs(modes) do
    for _, map in ipairs(vim.api.nvim_get_keymap(mode)) do
      swap(map, mode)
    end
    if buf and vim.api.nvim_buf_is_valid(buf) then
      vim.api.nvim_buf_call(buf, function()
        for _, map in ipairs(vim.api.nvim_buf_get_keymap(buf, mode)) do
          swap(map, mode, buf)
        end
      end)
    end
  end
end

function M.which_key()
  local ok, config = pcall(require, "which-key.config")
  if not ok or not config.replace or M.wk_done then
    return
  end
  M.wk_done = true
  table.insert(config.replace.desc, function(desc)
    return ko[desc]
  end)
end

function M.setup()
  local group = vim.api.nvim_create_augroup("keymap_ko", { clear = true })
  local function later(buf)
    vim.defer_fn(function()
      M.which_key()
      M.keymaps(buf)
    end, 200)
  end
  vim.api.nvim_create_autocmd("User", { group = group, pattern = { "VeryLazy", "LazyLoad" }, callback = function() later() end })
  vim.api.nvim_create_autocmd({ "LspAttach", "BufEnter" }, { group = group, callback = function(ev) later(ev.buf) end })
  later(vim.api.nvim_get_current_buf())
end

return M
