-- Command line (:, /, ?) at the bottom like plain Vim instead of a popup in the
-- middle of the screen; completion menus still pop up above it.
-- LSP loading in the bottom right: only a spinner and the server name, no
-- progress bar / percentage / message, and nothing once it finishes.
return {
  {
    "folke/noice.nvim",
    opts = {
      cmdline = { view = "cmdline" },
      lsp = {
        progress = {
          format = {
            { "{spinner} ", hl_group = "NoiceLspProgressSpinner" },
            { "{data.progress.client}", hl_group = "NoiceLspProgressClient" },
          },
          format_done = {},
        },
      },
    },
  },
}
