-- Korean Rust standard library docs in the hover popup (K) and in the
-- completion menu's documentation window (Ctrl+Space).
-- Translations live in ~/.local/share/rust-doc-ko/dict.json (built by
-- tools/build.py: normalized English paragraph -> Korean). Hover replies from
-- rust-analyzer are rewritten paragraph by paragraph before any UI sees them;
-- code blocks and paragraphs without a translation stay as they are.
-- <leader>uk toggles it (vim.g.rust_doc_ko).
local M = {}

local DICT = vim.fn.expand("~/.local/share/rust-doc-ko/dict.json")
local dict

local function load()
  if dict == nil then
    local ok, data = pcall(function()
      return vim.json.decode(table.concat(vim.fn.readfile(DICT), "\n"))
    end)
    dict = ok and data or false
  end
  return dict
end

-- Same normalization as tools/extract.py (drop link targets) plus build.py's
-- match_key (drop emphasis, bracket and backslash marks), then collapse spaces
local function norm(s)
  s = s:gsub("%[([^%]]*)%]%([^)]*%)", "%1")
  s = s:gsub("%[(`[^`]*`)%]%[[^%]]*%]", "%1")
  s = s:gsub("%[(`[^`]*`)%]", "%1")
  s = s:gsub("[%*_%[%]\\]", "")
  s = s:gsub("%s+", " ")
  return vim.trim(s)
end

-- "~" in Korean ranges ('A'~'Z') would pair up as markdown strikethrough;
-- outside `code` it becomes a full-width tilde
local function fix(ko)
  local parts = vim.split(ko, "`", { plain = true })
  for i = 1, #parts, 2 do
    parts[i] = parts[i]:gsub("~", "～")
  end
  return table.concat(parts, "`")
end

function M.translate(text)
  local d = load()
  if not d then
    return text
  end
  local out, para, fence = {}, {}, false
  local function flush()
    if #para > 0 then
      local ko = d[norm(table.concat(para, " "))]
      if ko then
        table.insert(out, fix(ko))
      else
        vim.list_extend(out, para)
      end
      para = {}
    end
  end
  for _, line in ipairs(vim.split(text, "\n", { plain = true })) do
    local s = vim.trim(line)
    if s:sub(1, 3) == "```" then
      flush()
      fence = not fence
      table.insert(out, line)
    elseif fence then
      table.insert(out, line)
    elseif s == "" or s == "---" then
      flush()
      table.insert(out, line)
    elseif s:sub(1, 1) == "#" then
      flush()
      local hashes, title = s:match("^(#+)%s*(.*)$")
      local ko = d[norm(title)]
      table.insert(out, ko and (hashes .. " " .. fix(ko)) or line)
    else
      table.insert(para, line)
    end
  end
  flush()
  return table.concat(out, "\n")
end

-- Rewrite the doc text of a reply in place: hover (K) and the completion
-- menu's documentation window (completionItem/resolve)
local function rewrite(method, result)
  if vim.g.rust_doc_ko == false or type(result) ~= "table" then
    return
  end
  local translate = require("config.rust_doc_ko").translate -- latest version after a reload
  local doc = method == "textDocument/hover" and result.contents or result.documentation
  if type(doc) == "table" and doc.value then
    doc.value = translate(doc.value)
  elseif method == "completionItem/resolve" and type(doc) == "string" then
    result.documentation = translate(doc)
  end
end

local function wrap(client)
  if client.name ~= "rust-analyzer" or client._rust_doc_ko then
    return
  end
  client._rust_doc_ko = true
  local request = client.request
  client.request = function(self, method, params, handler, bufnr)
    if handler and (method == "textDocument/hover" or method == "completionItem/resolve") then
      local orig = handler
      handler = function(err, result, ctx, config)
        rewrite(method, result)
        return orig(err, result, ctx, config)
      end
    end
    return request(self, method, params, handler, bufnr)
  end
end

function M.setup()
  vim.api.nvim_create_autocmd("LspAttach", {
    group = vim.api.nvim_create_augroup("rust_doc_ko", { clear = true }),
    callback = function(ev)
      local client = vim.lsp.get_client_by_id(ev.data.client_id)
      if client then
        wrap(client)
      end
    end,
  })
  for _, client in ipairs(vim.lsp.get_clients({ name = "rust-analyzer" })) do
    wrap(client)
  end
  Snacks.toggle({
    name = "Korean Rust Docs",
    get = function()
      return vim.g.rust_doc_ko ~= false
    end,
    set = function(on)
      vim.g.rust_doc_ko = on
    end,
  }):map("<leader>uk")
end

return M
