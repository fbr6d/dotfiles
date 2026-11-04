-- Completion: Tab / Shift+Tab are left to LazyVim (jump between snippet fields,
-- otherwise a normal tab); pick items with Ctrl+n / Ctrl+p or the arrow keys.
-- Kept simple: only code (LSP), file paths and snippets are suggested (no words
-- from the buffer), no gray ghost text. The selected item's documentation
-- opens beside the menu.
-- Each item shows its kind (Function, Struct, Variable, ...) and type details.

-- Basic snippets kept per filetype (friendly-snippets prefixes); other
-- filetypes keep all of theirs
local basic_snippets = {
  rust = {
    "fn", "main", "if", "if-let", "for", "while", "match",
    "struct", "enum", "trait", "test", "println", "vec",
  },
  lua = { "if", "elseif", "for", "fori", "forp", "fu", "lf", "l", "req", "p", "while" },
}

return {
  {
    "saghen/blink.cmp",
    opts = function(_, opts)
      opts.completion = opts.completion or {}
      opts.completion.documentation = { auto_show = true, auto_show_delay_ms = 200 }
      opts.completion.ghost_text = { enabled = false }
      opts.completion.menu = vim.tbl_deep_extend("force", opts.completion.menu or {}, {
        draw = {
          columns = { { "kind_icon" }, { "label", "label_description", gap = 1 }, { "kind" } },
        },
      })

      -- sources.default is a list LazyVim extends, so drop "buffer" here
      opts.sources.default = vim.tbl_filter(function(s)
        return s ~= "buffer"
      end, opts.sources.default)

      opts.sources.providers = opts.sources.providers or {}
      opts.sources.providers.snippets = vim.tbl_deep_extend("force", opts.sources.providers.snippets or {}, {
        transform_items = function(_, items)
          local keep = basic_snippets[vim.bo.filetype]
          if not keep then
            return items
          end
          return vim.tbl_filter(function(item)
            return vim.tbl_contains(keep, item.label)
          end, items)
        end,
      })
    end,
  },
}
