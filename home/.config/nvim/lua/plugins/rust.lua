-- rust-analyzer 루트 찾기 보정
-- 기본 동작은 Cargo.toml 을 먼저 찾아서, Cargo 크레이트 밖의 단독 .rs 파일
-- (예: ~/rustquest/exercises/*) 은 "not included in any crates" 가 되어 자동완성이 안 된다.
-- rust-project.json 이 더 가까이 있으면 그 폴더를 루트로 쓴다.
return {
  {
    "mrcjkb/rustaceanvim",
    opts = {
      server = {
        root_dir = function(file_name, default_root_dir)
          local project = vim.fs.find("rust-project.json", {
            upward = true,
            path = vim.fs.dirname(file_name),
          })[1]
          if project then
            local project_dir = vim.fs.dirname(project)
            local cargo = vim.fs.find("Cargo.toml", { upward = true, path = vim.fs.dirname(file_name) })[1]
            -- Cargo.toml 이 rust-project.json 보다 더 안쪽에 있으면 Cargo 프로젝트를 따른다
            if not cargo or #vim.fs.dirname(cargo) <= #project_dir then
              return project_dir
            end
          end
          return default_root_dir(file_name)
        end,
      },
    },
  },
}
