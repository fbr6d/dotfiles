-- Debugger breakpoints as filled red circles in the sign column
-- (LazyVim's dap.core extra defines the signs from these icons)
local red = "#f38ba8" -- Catppuccin Mocha red

vim.api.nvim_create_autocmd("ColorScheme", {
  group = vim.api.nvim_create_augroup("dap_breakpoint_hl", { clear = true }),
  callback = function()
    vim.api.nvim_set_hl(0, "DapBreakpoint", { fg = red })
  end,
})
vim.api.nvim_set_hl(0, "DapBreakpoint", { fg = red })

return {
  {
    "LazyVim/LazyVim",
    opts = {
      icons = {
        dap = {
          -- U+EA71 (Codicons circle-filled): kitty.conf draws it across both
          -- sign-column cells (narrow_symbols), so it is big but stays in the column
          Breakpoint = { "\u{ea71} ", "DapBreakpoint" },
          BreakpointCondition = { "◉ ", "DapBreakpoint" }, -- with a condition (<leader>dB)
        },
      },
    },
  },
}
