#!/usr/bin/env python3
"""Vim 수련장: 진짜 vim으로 하는 터미널 연습 앱.

  python3 vimdojo.py              메뉴 실행
  python3 vimdojo.py --date 2026-11-01   지난 날짜의 챌린지 보기
  python3 vimdojo.py --selftest 30       레슨과 30일치 챌린지의 모범 답안을 vim으로 검증
"""
import datetime
import difflib
import json
import os
import random
import re
import shutil
import subprocess
import sys
import tempfile
import unicodedata

VIM = shutil.which('vim') or shutil.which('nvim')
DATA_DIR = os.path.join(os.environ.get('XDG_DATA_HOME', os.path.expanduser('~/.local/share')), 'vimdojo')
PROGRESS = os.path.join(DATA_DIR, 'progress.json')

VIMRC = r'''
set nocompatible
set encoding=utf-8
set number relativenumber
set showcmd showmode ruler laststatus=2
set hlsearch incsearch
set backspace=indent,eol,start
set nrformats=bin,hex
set noswapfile nobackup nowritebackup noundofile
set shortmess+=IF
set mouse=
set t_fe= t_fd=
set scrolloff=2
set shiftwidth=4 expandtab tabstop=4
set belloff=all
set ttimeoutlen=50
syntax off
'''

# ---------------------------------------------------------------- terminal ui
USE_COLOR = sys.stdout.isatty() and not os.environ.get('NO_COLOR')


def c(code, s):
    return f'\033[{code}m{s}\033[0m' if USE_COLOR else s


def bold(s): return c('1', s)
def dim(s): return c('2', s)
def green(s): return c('32', s)
def yellow(s): return c('33', s)
def red(s): return c('31', s)
def cyan(s): return c('36', s)
def magenta(s): return c('35', s)
def keycap(s): return c('30;47', f' {s} ') if USE_COLOR else f'[{s}]'


ANSI = re.compile(r'\033\[[0-9;]*m')


def wlen(s):
    s = ANSI.sub('', s)
    return sum(2 if unicodedata.east_asian_width(ch) in 'WF' else 1 for ch in s)


def pad(s, w):
    return s + ' ' * max(0, w - wlen(s))


def clear():
    if sys.stdout.isatty():
        print('\033[2J\033[H', end='')


def ask(prompt='> '):
    try:
        return input(cyan(prompt)).strip()
    except EOFError:
        print()
        sys.exit(0)


def header(title, sub=''):
    clear()
    print(bold(green(' vim 수련장 ')) + dim(' │ ') + bold(title) + (dim('  ' + sub) if sub else ''))
    print(dim('─' * min(78, shutil.get_terminal_size((80, 24)).columns)))


def show_text(lines, width=None, title='', marks=None):
    """줄 번호와 함께 텍스트 블록을 그린다. marks[i]가 True면 초록, False면 빨강 표시."""
    out = []
    if title:
        out.append(dim(title))
    for i, ln in enumerate(lines):
        vis = ln.replace(' ', dim('·')) if ln.strip() != ln or not ln else ln
        if ln and ln.strip() == ln:
            vis = ln
        mark = ''
        if marks is not None:
            mark = green('✓ ') if marks[i] else red('✗ ')
        out.append(f'{dim(f"{i + 1:>3}")} {mark}{vis if ln else dim("(빈 줄)")}')
    return out


def side_by_side(left, right):
    w = max([wlen(x) for x in left] + [30]) + 3
    rows = max(len(left), len(right))
    for i in range(rows):
        a = left[i] if i < len(left) else ''
        b = right[i] if i < len(right) else ''
        print(pad(a, w) + b)


# ---------------------------------------------------------------- key notation
SPECIAL = {'<Esc>': '\x1b', '<CR>': '\r', '<BS>': '\x08', '<Tab>': '\t',
           '<C-a>': '\x01', '<C-x>': '\x18', '<C-r>': '\x12', '<C-v>': '\x16', '<C-o>': '\x0f'}
TOKEN_RE = re.compile(r'<(Esc|CR|BS|Tab|C-[a-z])>')


def tokenize(s):
    out, i = [], 0
    while i < len(s):
        m = TOKEN_RE.match(s, i)
        if m:
            out.append(m.group(0)); i = m.end()
        else:
            out.append(s[i]); i += 1
    return out


def ntok(s):
    return len(tokenize(s))


def to_bytes(s):
    return ''.join(SPECIAL.get(t, t) for t in tokenize(s)).encode()


def pretty_keys(s, limit=None):
    toks = tokenize(s) if isinstance(s, str) else s
    if limit and len(toks) > limit:
        toks = toks[:limit] + ['…']
    out = []
    for t in toks:
        if len(t) > 1 and t != '…':
            out.append(yellow(t))
        elif t == ' ':
            out.append(dim('␣'))
        else:
            out.append(bold(t))
    return ''.join(out)


def parse_keylog(data):
    """vim -W 로그를 키 목록으로 바꾼다."""
    keys, i = [], 0
    names = {0x1b: '<Esc>', 0x0d: '<CR>', 0x08: '<BS>', 0x7f: '<BS>', 0x09: '<Tab>'}
    while i < len(data):
        b = data[i]
        if b == 0x80 and i + 2 < len(data):
            kind = data[i + 1]
            i += 3
            if kind in (0xFD, 0xFB):  # 포커스·마우스 같은 키 아닌 이벤트
                continue
            pair = bytes(data[i - 2:i]).decode('latin1')
            keys.append({'ku': '<Up>', 'kd': '<Down>', 'kl': '<Left>', 'kr': '<Right>', 'kb': '<BS>', 'kD': '<Del>'}.get(pair, '<특수>'))
            continue
        if b >= 0xC0:
            n = 2 if b < 0xE0 else 3 if b < 0xF0 else 4
            keys.append(bytes(data[i:i + n]).decode('utf-8', 'replace')); i += n
            continue
        if b in names:
            keys.append(names[b])
        elif b < 0x20:
            keys.append(f'<C-{chr(b + 96)}>')
        else:
            keys.append(chr(b))
        i += 1
    return keys


def strip_submit(keys):
    """마지막 제출 명령(:w, :wq, :x, ZZ)은 키 수에서 뺀다."""
    if len(keys) >= 2 and keys[-2:] == ['Z', 'Z']:
        return keys[:-2]
    if keys and keys[-1] == '<CR>':
        j = len(keys) - 2
        while j >= 0 and keys[j] != ':':
            j -= 1
        if j >= 0 and ''.join(keys[j + 1:-1]).strip() in ('w', 'wq', 'x', 'wa', 'wqa', 'xa', 'w!', 'wq!', 'x!', 'up', 'update'):
            return keys[:j]
    return keys


# ---------------------------------------------------------------- navigation helper
def fnb(line):
    n = len(line) - len(line.lstrip())
    return min(n, max(0, len(line) - 1))


def hnav(line, a, b):
    if a == b:
        return ''
    opts = []
    if b == 0:
        opts.append('0')
    if b == len(line) - 1:
        opts.append('$')
    if b == fnb(line):
        opts.append('^')
    ch = line[b]
    if b > a:
        n = line[a + 1:b + 1].count(ch)
        opts.append(('' if n == 1 else str(n)) + 'f' + ch)
        d = b - a
        opts.append(('' if d == 1 else str(d)) + 'l')
    else:
        n = line[b:a].count(ch)
        opts.append(('' if n == 1 else str(n)) + 'F' + ch)
        d = a - b
        opts.append(('' if d == 1 else str(d)) + 'h')
    return min(opts, key=ntok)


class Nav:
    """모범 답안을 만들 때 커서 위치를 추적한다."""
    def __init__(self, lines):
        self.lines = list(lines)
        self.l = 0
        self.c = self.want = fnb(self.lines[0])
        self.keys = []

    def k(self, s):
        self.keys.append(s)

    def set(self, l, c):
        self.l, self.c, self.want = l, c, c

    def vgo(self, l):
        """세로로만 이동하고 도착 열을 돌려준다."""
        if l == self.l:
            return self.c
        opts = self._vopts(l)
        best = min(opts, key=lambda o: ntok(o[0]))
        self._apply(l, best)
        return self.c

    def _vopts(self, l):
        d = l - self.l
        gk = 'gg' if l == 0 else f'{l + 1}G'
        jk = 'j' if d > 0 else 'k'
        ad = abs(d)
        vk = jk * ad if ad <= 2 else f'{ad}{jk}'
        return [(gk, fnb(self.lines[l]), True), (vk, min(self.want, max(0, len(self.lines[l]) - 1)), False)]

    def _apply(self, l, o):
        self.k(o[0]); self.l = l; self.c = o[1]
        if o[2]:
            self.want = self.c

    def go(self, l, c):
        if l != self.l:
            opts = self._vopts(l)
            best = min(opts, key=lambda o: ntok(o[0]) + ntok(hnav(self.lines[l], o[1], c)))
            self._apply(l, best)
        h = hnav(self.lines[self.l], self.c, c)
        if h:
            self.k(h); self.c = c
            self.want = 10 ** 9 if h == '$' else c

    def sol(self):
        return ''.join(self.keys)


# ---------------------------------------------------------------- content pools
WORDS = ['apple', 'banana', 'cherry', 'grape', 'lemon', 'mango', 'melon', 'peach', 'plum', 'kiwi',
         'orange', 'papaya', 'lime', 'fig', 'pear', 'guava', 'apricot', 'coconut']
NAMES = [('Kim', 'Minji'), ('Lee', 'Jisoo'), ('Park', 'Hana'), ('Choi', 'Yuna'), ('Jung', 'Dami'),
         ('Kang', 'Sora'), ('Yoon', 'Hyun'), ('Han', 'Bora'), ('Seo', 'Jiho'), ('Oh', 'Narae'),
         ('Lim', 'Taeyang'), ('Shin', 'Haneul')]
VARS = ['count', 'total', 'index', 'value', 'result', 'buffer', 'offset', 'limit', 'score', 'width', 'speed', 'cache']
NEW_VARS = ['amount', 'cursor', 'payload', 'output', 'stock', 'margin', 'budget', 'weight', 'ratio', 'tally']
SENTENCES = ['the quick brown fox jumps over the lazy dog', 'practice makes the hands remember',
             'every journey begins with a single step', 'simple is better than complex',
             'readable code is kind to future you', 'measure twice and cut once',
             'a rolling stone gathers no moss', 'the early bird catches the worm',
             'small habits build strong skills', 'fortune favors the patient learner',
             'quiet keyboards make happy neighbors', 'good tools reward careful hands']
PARAS = ['Vim starts in normal mode.', 'Keys are commands there.', 'Press i to type text.',
         'Escape brings you back.', 'Motions move the cursor.', 'Operators change text.',
         'Counts repeat an action.', 'The dot repeats a change.', 'Macros record many keys.',
         'Search jumps to a pattern.', 'Registers hold yanked text.', 'Undo is always one key away.']
FAMILY_LABEL = {
    'textobj': '텍스트 객체', 'find': 'f/t 찾기', 'macro': '매크로', 'incr': '숫자 증감', 'typo': '오타 교정',
    'indent': '들여쓰기', 'join': '줄 합치기', 'case': '대소문자', 'subst': '치환', 'global': ':g 명령',
    'gen': '줄 생성', 'dot': '점 반복', 'grid': '격자 편집', 'para': '문단', 'sort': '정렬',
    'visual': '비주얼 모드', 'wrap': '감싸기', 'swap': '단어 교환', 'search': '검색 + 반복',
}


def ch(fam, title, desc, start, target, sol, hint, level):
    return {'fam': fam, 'title': title, 'desc': desc, 'start': start, 'target': target,
            'sol': sol, 'hint': hint, 'level': level}


# ---------------------------------------------------------------- daily generators
def g_textobj(r):
    keys = r.sample(['title', 'label', 'author', 'motto', 'status', 'theme', 'owner'], 3)
    olds = r.sample(['hello world', 'work in progress', 'to be decided', 'old value', 'temporary text', 'lorem ipsum'], 3)
    news = r.sample(['Vim rocks', 'ready', 'done', 'shipped', 'final', 'approved'], 1)
    fns = r.sample(['print', 'send', 'render', 'notify', 'save', 'load', 'emit'], 3)
    args = r.sample(VARS, 6)
    q = [f'{k} = "{o}"' for k, o in zip(keys, olds)]
    p = [f'{f}({args[2 * i]}, {args[2 * i + 1]})' for i, f in enumerate(fns)]
    kinds = ['q'] * 3 + ['p'] * 3
    r.shuffle(kinds)
    qi = pi = 0
    lines = []
    for kd in kinds:
        if kd == 'q':
            lines.append(q[qi]); qi += 1
        else:
            lines.append(p[pi]); pi += 1
    qlines = [i for i, k in enumerate(kinds) if k == 'q']
    plines = [i for i, k in enumerate(kinds) if k == 'p']
    eq = r.choice(qlines)
    ep_empty, ep_new = r.sample(plines, 2)
    new_arg = r.choice(NEW_VARS)
    nav = Nav(lines)
    target = list(lines)
    for l in sorted([eq, ep_empty, ep_new]):
        s = target[l]
        if l == eq:
            qpos = s.index('"')
            nav.go(l, qpos)
            nav.k(f'ci"{news[0]}<Esc>')
            target[l] = s[:qpos + 1] + news[0] + '"'
            nav.lines[l] = target[l]; nav.set(l, qpos + len(news[0]))
        else:
            ppos = s.index('(')
            nav.go(l, ppos)
            if l == ep_empty:
                nav.k('di(')
                target[l] = s[:ppos + 1] + ')'
                nav.lines[l] = target[l]; nav.set(l, ppos + 1)
            else:
                nav.k(f'ci({new_arg}<Esc>')
                target[l] = s[:ppos + 1] + new_arg + ')'
                nav.lines[l] = target[l]; nav.set(l, ppos + len(new_arg))
    return ch('textobj', '따옴표와 괄호 속만 갈아끼우기',
              '세 줄의 따옴표 안, 괄호 안 내용만 바꿔요. 바깥 글자는 한 글자도 지우지 마세요.',
              lines, target, nav.sol(),
              'ci" 는 따옴표 안을, di( 는 괄호 안을 지워요. 커서가 괄호 위나 안에 있어야 해요.', 2)


def g_find(r):
    v = r.choice(VARS)
    f1, f2, f3, f4 = r.sample(['wrap', 'clean', 'parse', 'trim', 'check', 'cast', 'fetch', 'scale'], 4)
    x = r.choice(['data', 'items', 'rows', 'input'])
    depth = r.choice([2, 3])
    inner = [f2, f3, f4][:depth]
    line0 = f'{v} = {f1}(' + ''.join(f + '(' for f in inner) + x + ')' * (depth + 1)
    t0 = f'{v} = {f1}({x})'
    g = r.choice(['plot', 'move', 'blend', 'draw'])
    a, b, cc = r.sample(['x', 'y', 'z', 'alpha', 'beta', 'gamma', 'size'], 3)
    line1 = f'{g}({a}, {b}, {cc})'
    t1 = f'{g}({a}, {cc})'
    tag = r.choice(['DEBUG', 'TEMP', 'OLD', 'TODO'])
    msg = r.choice(['saving file', 'user signed in', 'cache cleared', 'retry later'])
    line2 = f'log("[{tag}] {msg}")'
    t2 = f'log("{msg}")'
    lines = [line0, '', line1, '', line2]
    nav = Nav(lines)
    col = line0.index('(') + 1
    nav.go(0, col)
    nav.k(f'd{depth}f(')
    s = f'{v} = {f1}(' + x + ')' * (depth + 1)
    nav.lines[0] = s; nav.set(0, col)
    nav.go(0, s.index(')'))
    nav.k(f'{depth}x' if depth > 1 else 'x')
    nav.lines[0] = t0; nav.set(0, t0.index(')'))
    nav.go(2, line1.index(','))
    nav.k('dt,')
    nav.lines[2] = t1; nav.set(2, line1.index(','))
    nav.go(4, line2.index('['))
    nav.k('df ')
    return ch('find', '괄호 벗기기',
              '겹겹이 감싼 함수 호출을 벗기고, 가운데 인자를 빼고, 로그의 [태그]를 지우세요.',
              lines, [t0, '', t1, '', t2], nav.sol(),
              'd2f( 처럼 개수를 붙인 f, dt, 처럼 "어디까지"를 정하는 t 를 써 보세요.', 3)


def g_macro(r):
    words = r.sample(WORDS, r.randint(6, 8))
    n = len(words)
    target = ['['] + [f'  "{w}",' for w in words[:-1]] + [f'  "{words[-1]}"', ']']
    sol = f'qaI  "<Esc>A",<Esc>jq{n - 1}@aggO[<Esc>Go]<Esc>k$x'
    return ch('macro', 'JSON 배열 만들기',
              '단어 목록을 JSON 배열로 바꾸세요. 마지막 항목 뒤에는 쉼표가 없어야 해요.',
              words, target, sol,
              'qa 로 한 줄 작업을 녹화하고 q 로 끝낸 뒤 숫자@a 로 나머지 줄에 반복해요.', 4)


def g_incr(r):
    keys = r.sample(['port', 'timeout', 'workers', 'retries', 'max_conn', 'cache_mb', 'threads', 'log_level'], 6)
    base = {'port': 8080, 'timeout': 30, 'workers': 4, 'retries': 3, 'max_conn': 100,
            'cache_mb': 256, 'threads': 8, 'log_level': 2}
    lines = ['[server]'] + [f'{k} = {base[k] + r.randint(0, 9)}' for k in keys]
    target = list(lines)
    idx = sorted(r.sample(range(1, 7), 3))
    nav = Nav(lines)
    for l in idx:
        cur = int(lines[l].split('= ')[1])
        d = r.choice([1, 1, 2, 5, 10, 15, 37, 100, -1, -2, -3, -20])
        if cur + d < 0:
            d = -d
        new = cur + d
        target[l] = lines[l].split('= ')[0] + f'= {new}'
        nav.vgo(l)
        nav.k(('' if abs(d) == 1 else str(abs(d))) + ('<C-a>' if d > 0 else '<C-x>'))
        nav.lines[l] = target[l]; nav.set(l, len(target[l]) - 1)
    return ch('incr', '설정값 계산하기',
              '목표 창과 비교해 숫자 세 개를 바꾸세요. 숫자를 지우고 다시 쓰지 말고 더하고 빼 보세요.',
              lines, target, nav.sol(),
              'Ctrl-a 는 커서 뒤 첫 숫자를 1 올리고 Ctrl-x 는 내려요. 15 Ctrl-a 처럼 개수를 붙일 수 있어요.', 2)


def g_typo(r):
    sents = r.sample(SENTENCES, 3)
    start = list(sents)
    edits = []  # (l, c, kind, orig)
    used = set()
    kinds = ['swap', 'rep', 'case', r.choice(['swap', 'rep', 'case'])]
    r.shuffle(kinds)
    for kind in kinds:
        for _ in range(100):
            l = r.randrange(3)
            words = [(m.start(), m.group()) for m in re.finditer(r'[a-z]+', sents[l])]
            ws, w = r.choice(words)
            if (l, ws) in used or len(w) < 3:
                continue
            if kind == 'swap':
                i = r.randrange(len(w) - 1)
                if w[i] == w[i + 1]:
                    continue
                pos = ws + i
            else:
                pos = ws + r.randrange(len(w))
            used.add((l, ws))
            edits.append((l, pos, kind))
            break
    for l, pos, kind in edits:
        s = start[l]
        if kind == 'swap':
            start[l] = s[:pos] + s[pos + 1] + s[pos] + s[pos + 2:]
        elif kind == 'rep':
            alt = r.choice([x for x in 'aeioustr' if x != s[pos]])
            start[l] = s[:pos] + alt + s[pos + 1:]
        else:
            start[l] = s[:pos] + s[pos].upper() + s[pos + 1:]
    nav = Nav(start)
    for l, pos, kind in sorted(edits):
        nav.go(l, pos)
        orig = sents[l][pos]
        if kind == 'swap':
            nav.k('xp'); nav.set(l, pos + 1)
        elif kind == 'rep':
            nav.k('r' + orig); nav.set(l, pos)
        else:
            nav.k('~'); nav.set(l, min(pos + 1, len(sents[l]) - 1))
        nav.lines[l] = (nav.lines[l][:pos] + sents[l][pos:pos + 2] + nav.lines[l][pos + 2:]) if kind == 'swap' \
            else nav.lines[l][:pos] + orig + nav.lines[l][pos + 1:]
    return ch('typo', '오타 사냥',
              '문장 속 오타 네 개를 고치세요. 순서가 뒤바뀐 글자, 틀린 글자, 엉뚱한 대문자가 섞여 있어요.',
              start, sents, nav.sol(),
              'xp 는 두 글자를 맞바꾸고, r 은 한 글자를 교체하고, ~ 는 대소문자를 뒤집어요. f 로 빠르게 찾아가세요.', 2)


def g_indent(r):
    name = r.choice(['update', 'render', 'process', 'sync', 'refresh'])
    v = r.choice(VARS)
    cond = r.choice(['ready', 'dirty', 'visible', 'enabled'])
    calls = r.sample(['save', 'draw', 'notify', 'flush', 'reset', 'log'], r.randint(2, 3))
    body = [f'let {v} = {r.randint(1, 9)};', f'if ({cond}) {{'] + [f'{c_}();' for c_ in calls] + ['}', f'return {v};']
    lines = [f'function {name}() {{'] + body + ['}']
    target = [lines[0], '    ' + body[0], '    ' + body[1]] + ['        ' + x for x in body[2:2 + len(calls)]] + \
             ['    }', '    ' + body[-1], '}']
    inner = len(lines) - 2
    m = len(calls)
    sol = f'j>{inner - 1}jjj' + ('>>' if m == 1 else f'>{m - 1}j')
    return ch('indent', '들여쓰기 복원',
              '들여쓰기가 다 날아간 함수예요. 함수 안은 4칸, if 블록 안은 8칸으로 맞추세요.',
              lines, target, sol,
              '>j 는 두 줄을 한 단계 들여요. >5j 처럼 범위를 넓힐 수 있고, V로 고른 뒤 > 해도 돼요.', 1)


def g_join(r):
    s1, s2 = r.sample(SENTENCES, 2)

    def chop(s):
        w = s.split()
        cuts = sorted(r.sample(range(1, len(w)), min(len(w) - 1, r.randint(2, 4))))
        parts, prev = [], 0
        for c_ in cuts + [len(w)]:
            parts.append(' '.join(w[prev:c_])); prev = c_
        return parts
    p1, p2 = chop(s1), chop(s2)
    lines = p1 + [''] + p2
    j1 = 'J' if len(p1) == 2 else f'{len(p1)}J'
    j2 = 'J' if len(p2) == 2 else f'{len(p2)}J'
    return ch('join', '찢어진 문장 붙이기',
              '줄바꿈으로 조각난 두 문장을 각각 한 줄로 붙이세요. 사이의 빈 줄은 남겨요.',
              lines, [s1, '', s2], f'{j1}jj{j2}',
              'J 는 아래 줄을 공백 하나로 이어 붙여요. 4J 처럼 개수를 주면 여러 줄을 한 번에 붙여요.', 1)


def g_case(r):
    n = 6
    kinds = ['const'] * 4 + ['let'] * 2
    r.shuffle(kinds)
    pairs = [('max', 'size'), ('base', 'url'), ('retry', 'limit'), ('api', 'key'), ('page', 'count'),
             ('time', 'out'), ('user', 'agent'), ('cache', 'ttl'), ('font', 'scale')]
    names = r.sample(pairs, n)
    lines, target = [], []
    nav = None
    for k, (a, b) in zip(kinds, names):
        val = r.choice(['10', '"v2"', '3', 'true', '42', '"en"'])
        lines.append(f'{k} {a}_{b} = {val};')
        target.append(f'{k} {(a + "_" + b).upper() if k == "const" else a + "_" + b} = {val};')
    nav = Nav(lines)
    first = True
    for l, k in enumerate(kinds):
        if k != 'const':
            continue
        nav.go(l, 6)
        nav.k('gUiw' if first else '.')
        first = False
        nav.lines[l] = target[l]; nav.set(l, 6)
    return ch('case', '상수 이름 대문자로',
              'const 로 선언된 이름만 전부 대문자로 바꾸세요. let 은 그대로 둬요.',
              lines, target, nav.sol(),
              'gUiw 는 단어 하나를 대문자로 바꿔요. 한 번 한 뒤엔 . 으로 같은 변경을 반복하세요.', 2)


def g_subst(r):
    kind = r.choice(['rename', 'comment', 'capture'])
    if kind == 'rename':
        v, nv = r.choice(VARS), r.choice(NEW_VARS)
        cap = v[0].upper() + v[1:]
        lines = [f'let {v} = 0;', f'for (const item of {v}_list) {{', f'  {v} += item.size;', '}',
                 f'const my{cap} = {v} * 2;', f'console.log("{v}:", {v});']
        target = [re.sub(r'\b' + v + r'\b', nv, s) for s in lines]
        return ch('subst', f'{v} 을(를) {nv} 로',
                  f'변수 {v} 를 전부 {nv} 로 바꾸세요. {v}_list 나 my{cap} 처럼 이름 일부가 겹치는 건 건드리면 안 돼요.',
                  lines, target, f':%s/\\<{v}\\>/{nv}/g<CR>',
                  '%s 는 파일 전체 치환이에요. \\< 와 \\> 로 단어 경계를 걸 수 있어요.', 4)
    if kind == 'comment':
        pool = [('total = price * qty', 'compute total'), ('rate = 0.15', 'tax rate'),
                ('items = []', 'start empty'), ('done = False', 'not yet'), ('name = "vim"', 'editor name'),
                ('limit = 10', 'max rows')]
        rows = r.sample(pool, 4)
        lines = [f'{a}  # {b}' for a, b in rows]
        trap = r.choice(['msg = "step # 2"', 'tag = "issue # 7"', 'label = "room # 4"'])
        lines.insert(r.randint(1, 3), f'{trap}  # keep the hash in the string')
        lines.insert(2, 'print(total)')
        target = [re.sub(r'  #.*', '', s) for s in lines]
        return ch('subst', '주석만 걷어내기',
                  '줄 끝의 주석(# 부터 끝까지)과 그 앞 공백을 지우세요. 문자열 안의 # 은 살려야 해요.',
                  lines, target, ':%s/  #.*//<CR>',
                  '주석 앞에는 늘 공백이 두 칸 있어요. 패턴에 그 차이를 이용하세요.', 4)
    people = r.sample(NAMES, 5)
    lines = [f'{a}, {b}' for a, b in people]
    target = [f'{b} {a}' for a, b in people]
    return ch('subst', '이름 순서 뒤집기',
              '"성, 이름" 을 "이름 성" 으로 바꾸세요. 쉼표는 없애요.',
              lines, target, ':%s/\\(\\w\\+\\), \\(\\w\\+\\)/\\2 \\1/<CR>',
              '\\( \\) 로 묶은 부분은 바꿀 글에서 \\1, \\2 로 다시 쓸 수 있어요.', 5)


def g_global(r):
    kind = r.choice(['delete', 'reverse', 'done'])
    if kind == 'delete':
        lvl = r.choice(['DEBUG', 'INFO', 'WARN'])
        msgs = ['server started', 'user login', 'cache miss', 'disk almost full', 'request done',
                'config loaded', 'slow query', 'job queued', 'retry scheduled', 'token refreshed']
        levels = ['INFO', 'DEBUG', 'WARN', 'ERROR']
        while True:
            ls = [r.choice(levels) for _ in range(9)]
            if 3 <= ls.count(lvl) <= 5:
                break
        lines = [f'12:{10 + i:02d} {lv:<5} {m}' for i, (lv, m) in enumerate(zip(ls, r.sample(msgs, 9)))]
        target = [s for s, lv in zip(lines, ls) if lv != lvl]
        return ch('global', f'{lvl} 로그 걸러내기',
                  f'{lvl} 줄을 모두 지우세요. 나머지 줄은 순서 그대로 남겨요.',
                  lines, target, f':g/{lvl}/d<CR>',
                  ':g/패턴/명령 은 패턴이 있는 모든 줄에 명령을 실행해요.', 3)
    if kind == 'reverse':
        items = r.sample(WORDS, r.randint(6, 8))
        lines = [f'{i + 1}. {w}' for i, w in enumerate(items)]
        return ch('global', '목록 거꾸로 뒤집기',
                  '줄 순서를 통째로 뒤집으세요. 줄 내용은 그대로예요.',
                  lines, lines[::-1], ':g/^/m0<CR>',
                  '모든 줄(^)을 하나씩 맨 위(0번 줄 뒤)로 옮기면 어떻게 될까요?', 5)
    tasks = r.sample(['write tests', 'fix login bug', 'update docs', 'review PR', 'clean logs',
                      'tune queries', 'ship release', 'rename module', 'add metrics'], 7)
    while True:
        done = [r.random() < 0.45 for _ in tasks]
        if 2 <= sum(done) <= 4 and done[-1] is False:
            break
    lines = [f'- [{"x" if d else " "}] {t}' for t, d in zip(tasks, done)]
    target = [s for s, d in zip(lines, done) if not d] + [s for s, d in zip(lines, done) if d]
    return ch('global', '끝낸 일은 아래로',
              '완료된 [x] 항목을 맨 아래로 내리세요. 각 묶음 안의 순서는 원래대로 유지해요.',
              lines, target, ':g/\\[x\\]/m$<CR>',
              ':g 와 :m$ (맨 끝으로 옮기기)를 합쳐 보세요. [ 는 \\[ 로 써야 글자 그대로 찾아요.', 4)


def g_gen(r):
    stem, ext = r.choice([('backup_', '.tar'), ('photo_', '.jpg'), ('chapter', '.md'), ('test_', '.py'), ('log_', '.txt')])
    pad0 = r.choice([True, False])
    n = r.randint(6, 9)
    fmt = (lambda i: f'{i:02d}') if pad0 else (lambda i: str(i))
    target = [f'{stem}{fmt(i)}{ext}' for i in range(1, n + 1)]
    return ch('gen', '파일 이름 찍어내기',
              f'첫 줄 하나에서 시작해 번호가 1씩 늘어나는 {n}줄을 만드세요.',
              [target[0]], target, f'qayyp<C-a>q{n - 2}@a',
              'yyp 로 줄을 복사하고 Ctrl-a 로 번호를 올려요. 이 과정을 매크로로 녹화하면 빨라요.', 3)


def g_dot(r):
    v = r.choice(VARS)
    stmts = [f'let {v} = 0', f'{v} += 1', f'save({v})', f'log("{v}", {v})', f'{v} = clamp({v})',
             f'render({v})', f'notify({v})']
    picks = r.sample(stmts, 5)
    lines = []
    for i, s in enumerate(picks):
        lines.append(s)
        if i in (1, 3):
            lines.append(r.choice(['// keep going', '', '// no semicolon here']))
    already = r.choice([i for i, s in enumerate(lines) if s and not s.startswith('//')])
    lines[already] += ';'
    target = [s + ';' if s and not s.startswith('//') and not s.endswith(';') else s for s in lines]
    nav = Nav(lines)
    first = True
    for l, s in enumerate(lines):
        if target[l] == s:
            continue
        nav.vgo(l)
        nav.k('A;<Esc>' if first else '.')
        first = False
        nav.lines[l] = target[l]; nav.set(l, len(target[l]) - 1)
    return ch('dot', '세미콜론 순찰',
              '코드 줄 끝에만 ; 를 붙이세요. 주석, 빈 줄, 이미 ; 가 있는 줄은 건너뛰어요.',
              lines, target, nav.sol(),
              'A;<Esc> 로 한 번 한 다음엔 j 로 내려가 . 만 누르면 같은 일을 반복해요.', 2)


def g_grid(r):
    row = ' . | . | .'
    sep = '---+---+---'
    lines = [row, sep, row, sep, row]
    cells = [(rr, cc) for rr in range(3) for cc in range(3)]
    picks = r.sample(cells, r.randint(4, 5))
    target = list(lines)
    marks = {}
    for i, (rr, cc) in enumerate(picks):
        m = 'XO'[i % 2]
        marks[(rr, cc)] = m
        l, col = rr * 2, 1 + cc * 4
        target[l] = target[l][:col] + m + target[l][col + 1:]
    nav = Nav(lines)
    for (rr, cc) in sorted(marks):
        l, col = rr * 2, 1 + cc * 4
        nav.go(l, col)
        nav.k('r' + marks[(rr, cc)])
        nav.lines[l] = nav.lines[l][:col] + marks[(rr, cc)] + nav.lines[l][col + 1:]
        nav.set(l, col)
    return ch('grid', '틱택토 기보 옮기기',
              '목표 판과 똑같이 X 와 O 를 놓으세요. 판의 선은 건드리면 안 돼요.',
              lines, target, nav.sol(),
              'r 은 글자 하나를 바꾸고 바로 노멀 모드로 돌아와요. f. 와 ; 로 칸 사이를 건너뛰세요.', 1)


def g_para(r):
    ss = r.sample(PARAS, 7)
    a, b, c_ = ss[:2], ss[2:5], ss[5:7]
    r.shuffle(b)
    lines = a + [''] + b + [''] + c_
    target = b + [''] + a + [''] + c_
    return ch('para', '문단 자리 바꾸기',
              '첫 번째와 두 번째 문단의 순서를 바꾸세요. 문단 사이 빈 줄은 하나씩 유지해요.',
              lines, target, 'dap}p',
              'dap 는 문단 하나를 뒤따르는 빈 줄까지 지워요. } 는 다음 빈 줄로 점프해요.', 3)


def g_sort(r):
    base = r.sample([f'{a.lower()}.{b.lower()}@mail.test' for a, b in NAMES], 6)
    lines = base + r.sample(base, 3)
    r.shuffle(lines)
    return ch('sort', '주소록 정리',
              '이메일을 알파벳 순으로 정렬하고 중복은 하나만 남기세요.',
              lines, sorted(set(lines)), ':sort u<CR>',
              ':sort 에는 옵션이 있어요. u 는 중복 제거, n 은 숫자 순, ! 는 역순이에요.', 3)


def g_visual(r):
    t1 = r.choice(['Getting Started', 'Release Notes', 'Install Guide', 'Daily Practice'])
    t2 = r.choice(['Requirements', 'Next Steps', 'Known Issues', 'Shortcuts'])
    x1, x2 = r.sample(PARAS, 2)
    lines = [t1, '', x1, '', t2, '', x2]
    target = [t1, '=' * len(t1), '', x1, '', t2, '-' * len(t2), '', x2]
    sol = 'yypVr=6GyypVr-'
    return ch('visual', '마크다운 제목 밑줄',
              '첫 제목 아래에는 = 줄을, 두 번째 제목 아래에는 - 줄을 제목과 같은 길이로 그으세요.',
              lines, target, sol,
              'yyp 로 제목 줄을 복사하고 V 로 줄을 고른 뒤 r= 하면 모든 글자가 = 로 바뀌어요.', 3)


def g_wrap(r):
    words = ['init', 'start', 'stop', 'reset', 'build', 'deploy', 'test', 'lint']
    a, b, c_ = r.sample(words, 3)
    line = r.choice([f'run {a} first, then {b} and finally {c_}',
                     f'call {a} before {b} but never after {c_}',
                     f'use {a} or {b} when {c_} fails'])
    target = line
    nav = Nav([line])
    cur = line
    for w in (a, b, c_):
        pos = re.search(r'\b' + w + r'\b', cur).start()
        nav.go(0, pos)
        nav.k('i`<Esc>ea`<Esc>')
        cur = cur[:pos] + '`' + w + '`' + cur[pos + len(w):]
        nav.lines[0] = cur; nav.set(0, pos + len(w) + 1)
    target = cur
    return ch('wrap', '코드 표시 감싸기',
              f'명령 이름 {a}, {b}, {c_} 를 백틱(`)으로 감싸세요.',
              [line], [target], nav.sol(),
              'i`<Esc> 로 앞에 붙이고, e 로 단어 끝에 가서 a`<Esc> 로 뒤에 붙여요.', 2)


def g_swap(r):
    sents = r.sample(SENTENCES, 3)
    start, target = [], []
    nav = None
    swaps = []
    for s in sents:
        w = s.split()
        i = r.randrange(0, len(w) - 2)
        sw = w[:i] + [w[i + 1], w[i]] + w[i + 2:]
        start.append(' '.join(sw)); target.append(s)
        swaps.append(i)
    nav = Nav(start)
    for l, i in enumerate(swaps):
        w = start[l].split()
        pos = len(' '.join(w[:i])) + (1 if i else 0)
        nav.go(l, pos)
        nav.k('dwwP')
        nav.lines[l] = target[l]; nav.set(l, pos + len(w[i + 1]) + 1 + len(w[i]))
    return ch('swap', '뒤바뀐 단어 바로잡기',
              '각 문장에서 서로 자리가 바뀐 이웃 단어 한 쌍을 원래 순서로 돌려놓으세요.',
              start, target, nav.sol(),
              'dw 로 단어를 잘라내고 w 로 한 칸 건너뛴 뒤 P 로 앞에 붙이면 두 단어가 바뀌어요.', 2)


def g_search(r):
    w, nw = r.choice([('user', 'member'), ('item', 'entry'), ('node', 'vertex'), ('task', 'job')])
    code = [f'{w} = load()', f'if {w}.active:', f'    save({w})', f'print({w}.name)', f'cache[key] = {w}']
    comments = [f'# the {w} may be None', f'# do not rename this {w}', f'# {w} comes from the API']
    body = r.sample(code, 4)
    cm = r.sample(comments, 2)
    lines = ['def handle(key):'] + body[:2] + ['    ' + cm[0]] + body[2:] + ['    ' + cm[1]]
    lines = [lines[0]] + ['    ' + s if not s.startswith('    ') else s for s in lines[1:]]
    target = [s if s.strip().startswith('#') else re.sub(r'\b' + w + r'\b', nw, s) for s in lines]
    occ = []
    for l, s in enumerate(lines):
        for m in re.finditer(w, s):
            occ.append((l, m.start(), not s.strip().startswith('#')))
    sol = f'/{w}<CR>'
    first = True
    for i, (l, cpos, change) in enumerate(occ):
        if change:
            sol += f'cw{nw}<Esc>' if first else '.'
            first = False
        if i < len(occ) - 1:
            sol += 'n'
    return ch('search', '주석은 놔두고 이름 바꾸기',
              f'코드 속 {w} 만 {nw} 로 바꾸세요. # 주석 안의 {w} 는 그대로 둬요.',
              lines, target, sol,
              f'/{w} 로 찾고 cw 로 한 번 바꾼 다음, n 으로 다음 곳에 가서 바꿀 곳이면 . , 아니면 다시 n 이에요.', 4)


GENERATORS = {
    'textobj': g_textobj, 'find': g_find, 'macro': g_macro, 'incr': g_incr, 'typo': g_typo,
    'indent': g_indent, 'join': g_join, 'case': g_case, 'subst': g_subst, 'global': g_global,
    'gen': g_gen, 'dot': g_dot, 'grid': g_grid, 'para': g_para, 'sort': g_sort,
    'visual': g_visual, 'wrap': g_wrap, 'swap': g_swap, 'search': g_search,
}


def daily(date):
    fams = sorted(GENERATORS)
    random.Random(f'vimdojo-{date}').shuffle(fams)
    out = [GENERATORS[f](random.Random(f'vimdojo-{date}-{f}')) for f in fams[:10]]
    out.sort(key=lambda x: x['level'])
    for i, x in enumerate(out):
        x['id'] = f'{date}:{x["fam"]}'
    return out


# ---------------------------------------------------------------- lessons
LESSONS = [
    dict(title='hjkl 로 걷기', keys=[('h j k l', '왼쪽 · 아래 · 위 · 오른쪽'), ('x', '커서 위 글자 지우기'), ('5l', '숫자를 붙이면 그만큼 반복')],
         intro=['vim은 처음에 "노멀 모드"예요. 여기선 글자를 치면 입력이 아니라 명령이 돼요.',
                '손을 홈 키 위에 둔 채로 h j k l 로 움직여요. j 는 아래로 늘어진 모양이라 외우기 쉬워요.'],
         start=['Move with h j k l.', 'Then delete each X with x.', 'The qXuick brown fox', 'jumps over the lazXy dog.'],
         target=['Move with h j k l.', 'Then delete each X with x.', 'The quick brown fox', 'jumps over the lazy dog.'],
         sol='jj5lxj13lx', hint='jj 로 세 번째 줄에 가서 l 로 X 위에 선 다음 x.'),
    dict(title='입력 모드 드나들기', keys=[('i', '커서 앞에 입력 시작'), ('a', '커서 뒤에 입력 시작'), ('Esc', '노멀 모드로 돌아오기')],
         intro=['i 나 a 를 누르면 "입력 모드"가 되어 평범하게 글을 쓸 수 있어요.',
                '다 쓰면 반드시 Esc 로 노멀 모드로 돌아와요. 헷갈리면 일단 Esc 를 누르세요.'],
         start=['Vim is a editor.', 'Typing tet is easy.'],
         target=['Vim is a modal editor.', 'Typing text is easy.'],
         sol='9limodal <Esc>j6hax<Esc>', hint='editor 의 e 위에서 i, tet 의 e 위에서 a.'),
    dict(title='줄 단위로 쓰기', keys=[('A', '줄 끝에 입력'), ('I', '줄 맨 앞(첫 글자)에 입력'), ('o', '아래에 새 줄'), ('O', '위에 새 줄')],
         intro=['커서가 어디 있든 A 는 줄 끝으로, I 는 줄 처음으로 가서 입력 모드가 돼요.',
                'o 와 O 는 새 줄을 열어요. 코드를 쓸 때 가장 많이 쓰는 키예요.'],
         start=['let a = 1', 'let b = 2', 'log(a + b)'],
         target=['// add two numbers', 'let a = 1;', 'let b = 2;', 'console.log(a + b);', '// done'],
         sol='O// add two numbers<Esc>jA;<Esc>jA;<Esc>jIconsole.<Esc>A;<Esc>o// done<Esc>',
         hint='맨 위 주석은 O, 세미콜론은 A, console. 은 I 로.'),
    dict(title='단어 단위로 뛰기', keys=[('w', '다음 단어 처음'), ('b', '이전 단어 처음'), ('e', '단어 끝'), ('dw', '단어 하나 지우기')],
         intro=['한 글자씩 움직이면 느려요. w b e 로 단어 단위로 뛰어요.',
                'd 는 "지우기" 연산자예요. 뒤에 이동 키를 붙이면 그만큼 지워요. dw = 다음 단어까지 지우기.'],
         start=['the the quick brown fox', 'jumps over over the dog'],
         target=['the quick brown fox', 'jumps over the dog'],
         sol='dwjwdw', hint='반복된 단어 위에서 dw.'),
    dict(title='줄의 처음과 끝', keys=[('0', '줄 맨 앞'), ('^', '첫 글자'), ('$', '줄 끝'), ('D', '커서부터 줄 끝까지 지우기'), ('C', '줄 끝까지 지우고 입력')],
         intro=['0 은 줄의 맨 앞, ^ 는 공백 다음 첫 글자, $ 는 줄 끝이에요.',
                'D 는 d$, C 는 c$ 와 같아요. "여기서부터 끝까지"를 한 키로 처리해요.'],
         start=['    return value; // TODO remove', 'x = 10', 'Done'],
         target=['    return value;', 'x = 42', 'Done!'],
         sol='2wlDj04lC42<Esc>j$a!<Esc>', hint='; 다음 공백에서 D, 10 위에서 C.'),
    dict(title='줄 지우고 붙이기', keys=[('dd', '줄 잘라내기'), ('yy', '줄 복사'), ('p', '아래에 붙이기'), ('P', '위에 붙이기')],
         intro=['dd 로 지운 줄은 사라지지 않고 레지스터에 들어가요. p 로 다른 곳에 붙일 수 있어요.',
                '그래서 dd 와 p 를 합치면 "줄 옮기기"가 돼요.'],
         start=['3. bake', '1. mix', '2. pour', '4. eat', '4. eat'],
         target=['1. mix', '2. pour', '3. bake', '4. eat'],
         sol='ddjpjdd', hint='3번 줄을 dd 로 잘라서 2번 아래에 p, 중복된 4번은 dd.'),
    dict(title='고치고 되돌리기', keys=[('r', '글자 하나 바꾸기'), ('~', '대소문자 뒤집기'), ('cw', '단어 바꿔 쓰기'), ('u', '되돌리기'), ('Ctrl-r', '다시 하기')],
         intro=['r 다음에 글자를 치면 그 글자로 바뀌고 바로 노멀 모드로 돌아와요.',
                '실수했다면 u. 몇 번이든 되돌릴 수 있어요. 이 키 하나만 기억해도 vim이 덜 무서워요.'],
         start=['Vim iz fun', 'make it Faster', 'the best editor'],
         target=['Vim is fun', 'make it faster', 'the greatest editor'],
         sol='wlrsj3l~jbcwgreatest<Esc>', hint='z 위에서 rs, F 위에서 ~, best 위에서 cw.'),
    dict(title='글자 찾아 점프', keys=[('fx', '오른쪽의 x 로 점프'), ('tx', 'x 바로 앞까지'), (';', '같은 찾기 반복'), ('dt,', ', 앞까지 지우기')],
         intro=['f 다음에 글자를 치면 그 줄에서 그 글자로 바로 뛰어요. F 는 왼쪽 방향.',
                't 는 그 글자 바로 앞에 멈춰요. 그래서 dt) 는 ")" 앞까지 지우는 명령이 돼요.'],
         start=['print("debug: value=", x)  # TODO', 'name = first,last,middle'],
         target=['print(x)', 'name = first'],
         sol='f(ldtxf)lDjf,D', hint='" 위에서 dtx, ) 다음 칸에서 D, 쉼표 위에서 D.'),
    dict(title='텍스트 객체', keys=[('ciw', '단어 안 바꾸기'), ('ci"', '따옴표 안 바꾸기'), ('di(', '괄호 안 지우기'), ('da"', '따옴표까지 지우기')],
         intro=['i 는 "안쪽", a 는 "바깥까지"라는 뜻이에요. 연산자 뒤에 붙여요.',
                'ci" 는 커서가 따옴표 앞에만 있어도 알아서 따옴표를 찾아가요.'],
         start=['greeting = "Hello there"', 'total = sum(1, 2, 3)', 'color = blue'],
         target=['greeting = "Hi"', 'total = sum()', 'color = green'],
         sol='ci"Hi<Esc>jdi(jciwgreen<Esc>', hint='각 줄에서 ci" , di( , ciw.'),
    dict(title='점 하나로 반복', keys=[('.', '마지막 변경 반복')],
         intro=['. 은 방금 한 "변경"을 그대로 다시 해요. 입력 모드에서 친 글자까지 포함해요.',
                '한 번 잘 만들어 두고 . 으로 반복하는 게 vim다운 편집이에요.'],
         start=['apple', 'banana', 'cherry', 'grape'],
         target=['apple;', 'banana;', 'cherry;', 'grape;'],
         sol='A;<Esc>j.j.j.', hint='A;<Esc> 다음엔 j. 만 반복.'),
    dict(title='숫자 붙이기', keys=[('3dd', '세 줄 지우기'), ('5x', '다섯 글자 지우기'), ('d3w', '세 단어 지우기'), ('4j', '네 줄 아래로')],
         intro=['대부분의 명령 앞에 숫자를 붙이면 그만큼 반복돼요.',
                'd3w 처럼 이동 키 쪽에 붙여도 돼요. 왼쪽 줄 번호(상대 번호)를 보면 몇 줄인지 바로 보여요.'],
         start=['keep 1', 'drop', 'drop', 'drop', 'keep 2', 'xxxxxkeep 3', 'keep remove these words 4'],
         target=['keep 1', 'keep 2', 'keep 3', 'keep 4'],
         sol='j3ddj5xjwd3w', hint='drop 세 줄은 3dd, xxxxx 는 5x, 가운데 세 단어는 d3w.'),
    dict(title='비주얼 모드', keys=[('v', '글자 단위 선택'), ('V', '줄 단위 선택'), ('>', '선택 들여쓰기'), ('U', '선택 대문자로')],
         intro=['v 나 V 로 범위를 먼저 고르고, 그다음 무엇을 할지 키를 눌러요.',
                '선택한 상태에서 d y c > < U u 같은 키가 그 범위에 적용돼요.'],
         start=['function hello() {', "console.log('hi');", 'return true;', '}', '// make this loud'],
         target=['function hello() {', "    console.log('hi');", '    return true;', '}', '// make this LOUD'],
         sol='jVj>G3wveU', hint='가운데 두 줄을 V 로 골라 >, loud 를 v 로 골라 U.'),
    dict(title='검색과 치환', keys=[('/word', '아래로 검색'), ('n N', '다음 · 이전 결과'), (':%s/a/b/g', '파일 전체에서 a 를 b 로')],
         intro=['/ 를 누르고 단어를 친 뒤 Enter. n 으로 다음 결과로 뛰어요.',
                ':%s/찾을것/바꿀것/g 는 파일 전체(%)에서 모든 곳(g)을 바꿔요.'],
         start=['color: red;', 'background: white;', 'border: 1px solid red;', 'outline: red;'],
         target=['color: blue;', 'background: white;', 'border: 1px solid blue;', 'outline: blue;'],
         sol=':%s/red/blue/g<CR>', hint=':%s/red/blue/g 그리고 Enter.'),
    dict(title='매크로 녹화', keys=[('qa', 'a 에 녹화 시작'), ('q', '녹화 끝'), ('@a', '녹화 재생'), ('4@a', '네 번 재생')],
         intro=['qa 를 누르면 그때부터 누르는 키가 전부 a 에 녹화돼요. q 로 멈춰요.',
                '@a 로 재생해요. 녹화 마지막에 j 로 다음 줄로 가 두면 숫자@a 로 여러 줄에 쓸 수 있어요.'],
         start=['alice', 'bob', 'carol', 'dave', 'erin'],
         target=['- [ ] alice', '- [ ] bob', '- [ ] carol', '- [ ] dave', '- [ ] erin'],
         sol='qaI- [ ] <Esc>jq4@a', hint='qa I- [ ] <Esc> j q 다음 4@a.'),
    dict(title='숫자와 줄 합치기', keys=[('Ctrl-a', '숫자 +1'), ('Ctrl-x', '숫자 -1'), ('J', '아래 줄 붙이기'), ('3J', '세 줄 합치기')],
         intro=['Ctrl-a 는 커서 뒤의 첫 숫자를 올려요. 22 Ctrl-a 처럼 한 번에 크게 올릴 수도 있어요.',
                'J 는 아래 줄을 공백 하나 두고 이어 붙여요.'],
         start=['version = 2', 'max_users = 98', 'This sentence', 'is broken', 'into pieces.'],
         target=['version = 3', 'max_users = 120', 'This sentence is broken into pieces.'],
         sol='<C-a>j22<C-a>j3J', hint='Ctrl-a, 22 Ctrl-a, 3J.'),
]
for i, ls in enumerate(LESSONS):
    ls['id'] = f'lesson{i + 1:02d}'

CHEATSHEET = [
    ('모드', [('Esc', '노멀 모드로'), ('i a', '커서 앞/뒤 입력'), ('I A', '줄 처음/끝 입력'), ('o O', '아래/위 새 줄'),
             ('v V', '글자/줄 선택'), (':', '명령줄')]),
    ('이동', [('h j k l', '← ↓ ↑ →'), ('w b e', '단어 앞/뒤/끝'), ('0 ^ $', '줄 처음/첫 글자/끝'),
             ('gg G', '파일 처음/끝'), ('5G', '5번 줄'), ('f t ; ,', '글자 찾기와 반복'), ('%', '짝 괄호'), ('{ }', '문단')]),
    ('편집', [('x r ~', '지우기/바꾸기/대소문자'), ('dd yy p P', '줄 잘라내기/복사/붙이기'), ('d c y + 이동', '범위 지우기/바꾸기/복사'),
             ('ciw ci" di(', '텍스트 객체'), ('J', '줄 합치기'), ('>> <<', '들여쓰기'), ('Ctrl-a Ctrl-x', '숫자 증감')]),
    ('반복', [('.', '마지막 변경 반복'), ('u Ctrl-r', '되돌리기/다시'), ('qa … q', '매크로 녹화'), ('@a @@', '매크로 재생')]),
    ('명령', [('/pat n N', '검색'), ('*', '커서 단어 검색'), (':%s/a/b/g', '전체 치환'), (':g/pat/d', '패턴 있는 줄 삭제'),
             (':sort u', '정렬 + 중복 제거'), (':m0', '현재 줄을 맨 위로'), (':w', '제출'), (':q!', '포기')]),
]


# ---------------------------------------------------------------- progress
def load_progress():
    try:
        with open(PROGRESS) as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def save_progress(p):
    os.makedirs(DATA_DIR, exist_ok=True)
    tmp = PROGRESS + '.tmp'
    with open(tmp, 'w') as f:
        json.dump(p, f, ensure_ascii=False, indent=1)
    os.replace(tmp, PROGRESS)


def stars_for(keys, par):
    return 3 if keys <= par else 2 if keys <= par * 1.5 else 1


def star_str(n):
    return yellow('★' * n) + dim('☆' * (3 - n))


def streak(p):
    days = {d for d, v in p.get('daily', {}).items() if v}
    d = datetime.date.today()
    if d.isoformat() not in days:
        d -= datetime.timedelta(days=1)
    n = 0
    while d.isoformat() in days:
        n += 1
        d -= datetime.timedelta(days=1)
    return n


# ---------------------------------------------------------------- running vim
def vim_escape(s):
    return s.replace('\\', '\\\\').replace(' ', '\\ ').replace('|', '\\|').replace('"', '\\"')


def run_vim(start, target, title):
    tmp = tempfile.mkdtemp(prefix='vimdojo-')
    work = os.path.join(tmp, 'work.txt')
    tgt = os.path.join(tmp, '목표.txt')
    rc = os.path.join(tmp, 'vimrc')
    log = os.path.join(tmp, 'keys.log')
    with open(work, 'w') as f:
        f.write('\n'.join(start) + '\n')
    with open(tgt, 'w') as f:
        f.write('\n'.join(target) + '\n')
    with open(rc, 'w') as f:
        f.write(VIMRC)
    cols = shutil.get_terminal_size((80, 24)).columns
    split = 'vsplit' if cols >= 90 else 'split'
    cmd = [VIM, '-u', rc, '-i', 'NONE', '-n', '-N', '-W', log, work,
           '-c', f'rightbelow {split} {vim_escape(tgt)} | setlocal readonly nomodifiable nonumber norelativenumber '
                 'statusline=\\ 목표\\ (읽기\\ 전용) | wincmd p',
           '-c', 'setlocal statusline=\\ 작업\\ \\ │\\ \\ :w\\ 제출\\ \\ :q!\\ 포기\\ \\ u\\ 되돌리기%=%l,%c\\ ',
           '-c', 'autocmd BufWritePost <buffer> qa!',
           '-c', 'autocmd QuitPre * qa!',
           '-c', f'echo "{vim_escape(title)[:60]}  —  왼쪽을 오른쪽과 똑같이 만들고 :w"']
    subprocess.call(cmd)
    with open(work) as f:
        result = f.read()
    try:
        with open(log, 'rb') as f:
            keys = parse_keylog(f.read())
    except OSError:
        keys = []
    shutil.rmtree(tmp, ignore_errors=True)
    lines = result[:-1].split('\n') if result.endswith('\n') else result.split('\n')
    submitted = bool(keys) and (keys[-2:] == ['Z', 'Z'] or strip_submit(keys) != keys)
    return lines, strip_submit(keys), submitted


def headless(start, sol):
    """모범 답안을 vim에 흘려 넣고 결과 텍스트를 돌려준다."""
    tmp = tempfile.mkdtemp(prefix='vimdojo-test-')
    work = os.path.join(tmp, 'work.txt')
    rc = os.path.join(tmp, 'vimrc')
    ks = os.path.join(tmp, 'keys')
    with open(work, 'w') as f:
        f.write('\n'.join(start) + '\n')
    with open(rc, 'w') as f:
        f.write(VIMRC)
    with open(ks, 'wb') as f:
        f.write(to_bytes(sol) + b'\x1b\x1b:w!\r:qa!\r')
    subprocess.run([VIM, '-u', rc, '-i', 'NONE', '-n', '-N', '-s', ks, work],
                   stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=20)
    with open(work) as f:
        out = f.read()
    shutil.rmtree(tmp, ignore_errors=True)
    return out[:-1].split('\n') if out.endswith('\n') else out.split('\n')


# ---------------------------------------------------------------- screens
def show_diff(got, want):
    print(bold('  어디가 다른지:'))
    for ln in difflib.unified_diff(want, got, '목표', '내 결과', lineterm='', n=1):
        if ln.startswith(('---', '+++')):
            continue
        shown = ln[1:].replace(' ', '·') if ln[:1] in '+-' else ln
        if ln.startswith('-'):
            print('   ' + green('목표 ') + shown)
        elif ln.startswith('+'):
            print('   ' + red('내것 ') + shown)
        elif ln.startswith('@@'):
            print('   ' + dim(ln))
        else:
            print('        ' + dim(ln[1:]))


def intro(item, kind, par, best):
    """과제 소개 화면. 'start' / 'back' 을 돌려준다."""
    while True:
        header(item['title'], f'기준 {par}키' if kind == 'daily' else '기초 레슨')
        if kind == 'lesson':
            for ln in item['intro']:
                print('  ' + ln)
            print()
            for k, d in item['keys']:
                print(f'  {pad(keycap(k), 16)}{d}')
        else:
            print('  ' + magenta(f'[{FAMILY_LABEL[item["fam"]]}] ') + item['desc'])
        print()
        left = show_text(item['start'], title='  지금')
        right = show_text(item['target'], title='목표')
        side_by_side(['  ' + x if i else x for i, x in enumerate(left)], right)
        print()
        if best:
            print('  ' + dim('내 최고 기록: ') + f'{best["keys"]}키 ' + star_str(best['stars']))
        print(dim('  vim이 열리면 왼쪽 창을 오른쪽과 똑같이 만들고 :w 로 제출해요. 포기는 :q!'))
        print()
        print(f'  {keycap("Enter")} 시작   {keycap("h")} 힌트   {keycap("s")} 모범 답안   {keycap("b")} 목록으로')
        cmd = ask('  > ').lower()
        if cmd == 'b':
            return 'back'
        if cmd == 'h':
            print('\n  ' + yellow('힌트 ') + item['hint'])
            ask('  Enter 로 돌아가기 ')
        elif cmd == 's':
            print('\n  ' + yellow('모범 답안 ') + f'({par}키)  ' + pretty_keys(item['sol']))
            print(dim('  <Esc> 는 Esc 키, <CR> 은 Enter, <C-a> 는 Ctrl+a 예요. 공백은 ␣ 로 보여요.'))
            ask('  Enter 로 돌아가기 ')
        elif not cmd:
            return 'start'


def play(item, kind, prog):
    """kind: 'lesson' 또는 'daily'. 끝나면 다음 동작(None/'next')을 돌려준다."""
    par = ntok(item['sol'])
    rec_store = prog.setdefault('lessons', {}) if kind == 'lesson' else \
        prog.setdefault('daily', {}).setdefault(item['id'].split(':')[0], {})
    rec_key = item['id'] if kind == 'lesson' else item['fam']
    if intro(item, kind, par, rec_store.get(rec_key)) == 'back':
        return None
    while True:
        got, keys, submitted = run_vim(item['start'], item['target'], item['title'])
        n = len(keys)
        header(item['title'], '결과')
        if got == item['target']:
            st = stars_for(n, par)
            print('  ' + green(bold('성공!')) + f'  {n}키  ' + star_str(st) + dim(f'   (기준 {par}키)'))
            if n < par:
                print('  ' + magenta('모범 답안보다 짧아요. 대단해요!'))
            old = rec_store.get(rec_key)
            if not old or n < old['keys']:
                rec_store[rec_key] = {'keys': n, 'stars': st}
                save_progress(prog)
                if old:
                    print('  ' + yellow(f'최고 기록 갱신 ({old["keys"]} → {n})'))
            print()
            print('  ' + dim('내 입력  ') + pretty_keys(keys, 80))
            print('  ' + dim('모범답안 ') + pretty_keys(item['sol']))
            print()
            print(f'  {keycap("Enter")} 다음   {keycap("r")} 다시 도전   {keycap("b")} 목록으로')
            cmd = ask('  > ').lower()
            if cmd == 'r':
                continue
            return None if cmd == 'b' else 'next'
        if not submitted:
            print('  ' + yellow('포기하고 나왔어요.') + ' 괜찮아요, 다시 해 봐요.')
        else:
            print('  ' + red('아직 목표와 달라요.') + dim(f'  ({n}키 입력)'))
            print()
            show_diff(got, item['target'])
        print()
        print(f'  {keycap("Enter")} 다시 도전   {keycap("h")} 힌트   {keycap("s")} 모범 답안   {keycap("b")} 목록으로')
        while True:
            cmd = ask('  > ').lower()
            if cmd == 'h':
                print('  ' + yellow('힌트 ') + item['hint'])
            elif cmd == 's':
                print('  ' + yellow('모범 답안 ') + f'({par}키)  ' + pretty_keys(item['sol']))
            else:
                break
        if cmd == 'b':
            return None


def lessons_menu(prog):
    while True:
        header('기초 레슨', '처음이라면 1번부터')
        done = prog.get('lessons', {})
        for i, ls in enumerate(LESSONS):
            rec = done.get(ls['id'])
            mark = green('✓') if rec else dim('·')
            keys = dim(' '.join(k for k, _ in ls['keys']))
            print(f'  {mark} {i + 1:>2}. {pad(ls["title"], 20)} {keys}')
        print(f'\n  {dim("번호를 고르세요.")}  {keycap("b")} 처음 화면')
        cmd = ask('  > ').lower()
        if cmd == 'b' or cmd == 'q':
            return
        if cmd.isdigit() and 1 <= int(cmd) <= len(LESSONS):
            i = int(cmd) - 1
            while i < len(LESSONS):
                if play(LESSONS[i], 'lesson', prog) != 'next':
                    break
                i += 1


def daily_menu(prog, date):
    today = datetime.date.today()
    while True:
        items = daily(date.isoformat())
        rec = prog.get('daily', {}).get(date.isoformat(), {})
        label = '오늘' if date == today else date.isoformat()
        header(f'{label}의 챌린지', f'{date.isoformat()} · {len(rec)}/10 완료 · 연속 {streak(prog)}일')
        for i, it in enumerate(items):
            r_ = rec.get(it['fam'])
            st = star_str(r_['stars']) if r_ else dim('☆☆☆')
            lvl = '●' * it['level'] + dim('○' * (5 - it['level']))
            fam = magenta(pad(FAMILY_LABEL[it['fam']], 12))
            best = f'{r_["keys"]:>3}키' if r_ else dim('  — ')
            print(f'  {i + 1:>2}. {fam} {pad(it["title"], 30)} {lvl}  {dim("기준")} {ntok(it["sol"]):>3}  {best} {st}')
        print(f'\n  {dim("번호를 고르세요.")}  {keycap("p")} 전날  {keycap("n")} 다음날  {keycap("b")} 처음 화면')
        cmd = ask('  > ').lower()
        if cmd in ('b', 'q'):
            return
        if cmd == 'p':
            date -= datetime.timedelta(days=1)
        elif cmd == 'n':
            if date < today:
                date += datetime.timedelta(days=1)
        elif cmd.isdigit() and 1 <= int(cmd) <= len(items):
            i = int(cmd) - 1
            while i < len(items):
                if play(items[i], 'daily', prog) != 'next':
                    break
                i += 1


def cheatsheet():
    header('치트시트')
    for group, rows in CHEATSHEET:
        print('  ' + bold(group))
        for k, d in rows:
            print(f'    {pad(keycap(k), 18)}{d}')
        print()
    ask('  Enter 로 돌아가기 ')


def main_menu(date):
    prog = load_progress()
    while True:
        today_rec = prog.get('daily', {}).get(datetime.date.today().isoformat(), {})
        lessons_done = len(prog.get('lessons', {}))
        header('처음 화면')
        print('  진짜 vim을 열어서 연습해요. 왼쪽 창을 오른쪽 목표와 똑같이 만들고 :w 로 제출하면 채점돼요.')
        print(dim('  키를 적게 쓸수록 별이 많아요. 한글 입력 상태면 명령이 안 먹으니 영문으로 바꿔 두세요.'))
        print()
        print(f'  {keycap("1")} 기초 레슨          {dim(f"{lessons_done}/{len(LESSONS)} 완료")}')
        print(f'  {keycap("2")} 오늘의 챌린지 10   {dim(f"{len(today_rec)}/10 완료 · 연속 {streak(prog)}일")}')
        print(f'  {keycap("3")} 치트시트')
        print(f'  {keycap("q")} 끝내기')
        cmd = ask('\n  > ').lower()
        if cmd == '1':
            lessons_menu(prog)
        elif cmd == '2':
            daily_menu(prog, date)
        elif cmd == '3':
            cheatsheet()
        elif cmd in ('q', 'quit', 'exit'):
            clear()
            return


# ---------------------------------------------------------------- self test
def selftest(days):
    from concurrent.futures import ThreadPoolExecutor
    jobs = [(f'레슨 {ls["title"]}', ls) for ls in LESSONS]
    base = datetime.date.today()
    for d in range(days):
        for it in daily((base + datetime.timedelta(days=d)).isoformat()):
            jobs.append((it['id'], it))

    def check(job):
        name, it = job
        got = headless(it['start'], it['sol'])
        return name, it, got

    bad = 0
    fams = {}
    with ThreadPoolExecutor(8) as ex:
        for name, it, got in ex.map(check, jobs):
            fams[it.get('fam', 'lesson')] = fams.get(it.get('fam', 'lesson'), 0) + 1
            if got != it['target']:
                bad += 1
                if bad <= 8:
                    print(red('FAIL ') + name + '  ' + it['sol'])
                    for ln in difflib.unified_diff(it['target'], got, 'target', 'vim', lineterm='', n=0):
                        print('   ' + ln)
    print(f'{len(jobs) - bad}/{len(jobs)} 통과', dict(sorted(fams.items())))
    return bad == 0


def main():
    if not VIM:
        print('vim이 필요해요. 설치: sudo pacman -S vim  (또는 apt install vim, brew install vim)')
        sys.exit(1)
    args = sys.argv[1:]
    if args[:1] == ['--selftest']:
        sys.exit(0 if selftest(int(args[1]) if len(args) > 1 else 30) else 1)
    date = datetime.date.today()
    if args[:1] == ['--date'] and len(args) > 1:
        date = min(date, datetime.date.fromisoformat(args[1]))
    try:
        main_menu(date)
    except KeyboardInterrupt:
        print()


if __name__ == '__main__':
    main()
