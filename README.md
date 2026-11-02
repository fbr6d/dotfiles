# dotfiles

이 컴퓨터(Arch Linux + Hyprland)의 설정 백업. 비공개 저장소.

## 백업 (이 컴퓨터에서)

```bash
~/dotfiles/backup.py
```

설정을 모아 커밋하고 GitHub로 push합니다. Claude Code에서 "설정 백업해줘"라고 해도 됩니다.
변경이 없으면 커밋하지 않습니다. `--no-push`는 커밋만, `--dry-run`은 무엇을 건너뛰는지만 보여줍니다.

## 복원 (새 컴퓨터에서)

```bash
git clone https://github.com/<계정>/dotfiles ~/dotfiles
~/dotfiles/restore.sh
```

단계별로만 하려면 `restore.sh packages|files|zen|home|dconf|etc|services`.
`home` 단계는 개인 파일 저장소(`home-backup`)를 받아 `~`에 풀어 놓습니다(`gh auth login` 먼저).
덮어쓴 기존 파일은 `~/.dotfiles-old/<시각>/`에 보관됩니다.

## 개인 파일 백업 (별도 저장소)

```bash
~/dotfiles/home_backup.py
```

`~`의 숨김이 아닌 폴더(문서, 사진, 다운로드, Projects 등)를 비공개 저장소 `home-backup`에 따로 올립니다.
`yay` 빌드 폴더, `node_modules`·`.git` 같은 빌드/의존성 폴더, 95MB 넘는 파일(GitHub 한도)은 건너뜁니다.

## 무엇이 들어가나

| 폴더 | 내용 |
|---|---|
| `home/` | `~`의 점파일, `~/.config/*`, `~/.local/bin`, `~/.local/share/*`(폰트 등), `~/.claude` 설정·스킬·메모리 |
| `zen/` | Zen 브라우저 프로필의 설정·확장·테마·북마크 (쿠키·비밀번호·기록 제외) |
| `etc/` | 직접 만든 systemd 유닛, greetd 등 수정한 시스템 설정 |
| `meta/` | pacman/AUR 패키지 목록, dconf 덤프, 켜져 있는 서비스 목록 |

새로 설치한 앱의 설정은 자동으로 포함됩니다(목록 방식이 아니라 제외 방식).
빼고 싶은 것은 `backup.py` 맨 위의 `*_DENY` 목록에 추가하세요.

## 항상 제외되는 것

SSH/GPG 키, 브라우저 쿠키·비밀번호·기록, 셸 기록, 토큰·자격 증명 파일, 캐시, 20MB 넘는 파일, 150MB 넘는 폴더.
커밋 전에 토큰처럼 보이는 문자열을 검사해서, 발견되면 커밋하지 않고 멈춥니다.
