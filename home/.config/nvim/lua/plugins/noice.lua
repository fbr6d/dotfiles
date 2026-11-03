-- Command line (:, /, ?) at the bottom like plain Vim instead of a popup in the
-- middle of the screen; completion menus still pop up above it.
return {
  {
    "folke/noice.nvim",
    opts = {
      cmdline = { view = "cmdline" },
    },
  },
}
