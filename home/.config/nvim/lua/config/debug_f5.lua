-- F5: one key to debug a Rust program
--   * no debug session: save all files, ask for the program's arguments
--     (paths relative to the Cargo project root, Tab completes file names,
--     the last arguments are filled in so Enter alone reuses them),
--     then build and start the program's binary under the debugger
--   * debug session running: continue to the next breakpoint
-- Arguments are remembered per project, also after restarting Neovim.
local M = {}

local store = vim.fn.stdpath("data") .. "/debug_f5_args.json"

local function load()
  local ok, data = pcall(function()
    return vim.json.decode(table.concat(vim.fn.readfile(store), "\n"))
  end)
  return ok and type(data) == "table" and data or {}
end

local function save(data)
  pcall(vim.fn.writefile, { vim.json.encode(data) }, store)
end

-- Cargo project root of the current file (where Cargo.toml is)
local function cargo_root()
  local file = vim.api.nvim_buf_get_name(0)
  local found = vim.fs.find("Cargo.toml", { upward = true, path = vim.fs.dirname(file) })[1]
  return found and vim.fs.dirname(found) or vim.fn.getcwd()
end

-- Ask for the arguments; nil when cancelled with Esc
local function ask_args(root)
  local saved = load()
  local prev = vim.fn.getcwd()
  vim.fn.chdir(root) -- file completion starts at the project root
  vim.g.debug_args_prompt = true -- file list pops up while typing (plugins/completion.lua)
  local ok, input = pcall(vim.fn.input, {
    prompt = "Debug args (" .. vim.fn.fnamemodify(root, ":t") .. "): ",
    default = saved[root] or "",
    completion = "file",
    cancelreturn = "\0",
  })
  vim.g.debug_args_prompt = false
  vim.fn.chdir(prev)
  if not ok or input == "\0" then
    return nil
  end
  saved[root] = input
  save(saved)
  return vim.split(vim.trim(input), "%s+", { trimempty = true })
end

-- Start the crate's binary (the "cargo run" target) with the given arguments.
-- The debugger's working directory is the project root, so relative paths work.
local function start_rust(args)
  local fallback = function()
    vim.cmd.RustLsp({ "debuggables", unpack(args) })
  end
  local client = vim.lsp.get_clients({ bufnr = 0, name = "rust-analyzer" })[1]
  if not client then
    vim.notify("rust-analyzer is not running yet", vim.log.levels.WARN)
    return
  end
  local params = { textDocument = vim.lsp.util.make_text_document_params(), position = nil }
  client:request("experimental/runnables", params, function(_, result)
    local ok = pcall(function()
      local bin
      for _, r in ipairs(result or {}) do
        if r.args and r.args.cargoArgs and r.args.cargoArgs[1] == "run" then
          bin = r
          break
        end
      end
      if not bin then
        error("no binary target")
      end
      local a = vim.deepcopy(bin.args)
      require("rustaceanvim.overrides").sanitize_command_for_debugging(a.cargoArgs) -- run -> build
      a.executableArgs = args
      require("rustaceanvim.dap").start(a, true, require("dap").run)
      require("rustaceanvim.cached_commands").set_last_debuggable(a)
    end)
    if not ok then
      fallback() -- pick the target from the list instead
    end
  end, 0)
end

function M.f5()
  local dap = require("dap")
  if dap.session() then
    dap.continue()
    return
  end
  vim.cmd("silent! wall") -- breakpoints must match the code that gets built
  if vim.bo.filetype ~= "rust" then
    dap.continue()
    return
  end
  local args = ask_args(cargo_root())
  if args then
    start_rust(args)
  end
end

vim.keymap.set("n", "<F5>", M.f5, { desc = "Debug: start / continue" })

return M
