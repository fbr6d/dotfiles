-- Catppuccin Mocha for text and highlights, but with the desktop's monochrome
-- dark grays (Claude dark mode) as backgrounds instead of Mocha's blue-tinted ones.
return {
  {
    "catppuccin/nvim",
    name = "catppuccin",
    opts = {
      flavour = "mocha",
      color_overrides = {
        mocha = {
          base = "#262624",     -- editor background
          mantle = "#1f1e1d",   -- side panels, status line
          crust = "#141413",    -- deepest background, window borders
          surface0 = "#30302e", -- cursor line, popups
          surface1 = "#4a4a47", -- selection
          surface2 = "#5a5a56",
        },
      },
    },
  },
  {
    "LazyVim/LazyVim",
    opts = { colorscheme = "catppuccin-mocha" },   -- not "catppuccin": Neovim 0.12 ships its own with that name
  },
}
