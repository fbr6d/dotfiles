-- Status line: no clock at the right end (LazyVim puts the time in lualine_z)
return {
  {
    "nvim-lualine/lualine.nvim",
    opts = function(_, opts)
      opts.sections.lualine_z = {}
    end,
  },
}
