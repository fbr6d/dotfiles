-- Completion menu: Tab selects the next item, Shift+Tab the previous one
-- (Enter still accepts). With the menu closed, Tab jumps through snippet
-- fields or inserts a normal tab.
return {
  {
    "saghen/blink.cmp",
    opts = {
      keymap = {
        ["<Tab>"] = { "select_next", "snippet_forward", "fallback" },
        ["<S-Tab>"] = { "select_prev", "snippet_backward", "fallback" },
      },
    },
  },
}
