// 미쿠 말풍선 (2026-11-19, 마스터 요청: 저장된 대사 말고 그때그때 AI가 아무 말이나)
// 오른쪽 위 도트 미쿠 그림(miku-art.mjs) 바로 아래에 붙는 말풍선.
// 파일 이름 순서(miku-art → miku-bubble → miku-ksat)대로 같은 모서리에 위에서부터 쌓인다.
// CHANGE_MS마다 scripts/miku_bubble_line.py(Claude Haiku 한 번 호출, 대화 기록 안 남김)로 새 대사를 받는다.
// 실패하면 이전 대사를 그대로 둔다. 켜기/끄기: /miku-bubble   다시 읽기: /widgets-reload
import { execFile } from 'node:child_process'
import { join } from 'node:path'

const CHANGE_MS = 10 * 60 * 1000 // 2026-11-20 마스터 요청: 2분 → 10분
const WIDTH = 54 // miku-art 칸 폭(그림 52 + 2)과 맞춘다
const MIKU = '#39C5BB'
const HOME = process.env.HOME || ''
const PY = join(HOME, '.hermes/tools/python-3.14.9+20261021-linux-x64/bin/python3')
const SCRIPT = join(HOME, '.hermes/profiles/miku/scripts/miku_bubble_line.py')

// 2026-11-19 마스터 요청: 말풍선 크기 고정(4줄). 줄바꿈을 화면에 맡기지 않고 직접 한다.
const LINES = 4
const INNER = WIDTH - 2 - 2 - 2 // 바깥 폭 52 - 테두리 2 - 여백 2 = 48칸
const cellW = ch => (/[\u1100-\u115F\u2E80-\uA4CF\uAC00-\uD7A3\uF900-\uFAFF\uFE30-\uFE4F\uFF00-\uFF60\uFFE0-\uFFE6]/.test(ch) ? 2 : 1)
const width = s => [...s].reduce((n, ch) => n + cellW(ch), 0)

// 띄어쓰기 단위로 INNER칸에 맞춰 줄을 나누고, 정확히 LINES줄로 맞춘다(모자라면 빈 줄, 넘치면 마지막 줄 끝 '…').
function layout(text) {
  const out = []
  let cur = ''
  const push = () => { out.push(cur); cur = '' }
  for (const word of text.split(' ').filter(Boolean)) {
    const sep = cur ? ' ' : ''
    if (width(cur + sep + word) <= INNER) { cur += sep + word; continue }
    if (cur) push()
    let w = word
    while (width(w) > INNER) { // 한 단어가 한 줄보다 길면 글자 단위로 끊는다
      let piece = ''
      for (const ch of w) { if (width(piece + ch) > INNER) break; piece += ch }
      out.push(piece)
      w = w.slice(piece.length)
    }
    cur = w
  }
  if (cur) push()
  if (out.length > LINES) {
    let last = out[LINES - 1]
    while (last && width(last + '…') > INNER) last = [...last].slice(0, -1).join('')
    out.length = LINES
    out[LINES - 1] = last + '…'
  }
  while (out.length < LINES) out.push('')
  return out
}

function askMiku(prev) {
  return new Promise(resolve => {
    execFile(PY, ['-I', SCRIPT, prev || ''], { timeout: 60000, env: process.env }, (err, out) => {
      const line = String(out || '').trim().split('\n').pop()
      resolve(err || !line ? null : line)
    })
  })
}

export default function register(sdk) {
  const { Box, Text, React, defineWidgetApp, h, openWidget } = sdk

  function Bubble({ t }) {
    const [line, setLine] = React.useState(null)
    const lastRef = React.useRef('')
    React.useEffect(() => {
      let alive = true
      let busy = false
      const load = () => {
        if (busy) return
        busy = true
        askMiku(lastRef.current).then(l => {
          busy = false
          if (alive && l) {
            lastRef.current = l
            setLine(l)
          }
        })
      }
      load()
      const id = setInterval(load, CHANGE_MS)
      return () => {
        alive = false
        clearInterval(id)
      }
    }, [])
    return h(
      Box,
      { flexDirection: 'column', width: WIDTH - 2 },
      h(Text, { color: MIKU }, ' '.repeat(24) + '▲'),
      h(
        Box,
        { borderStyle: 'round', borderColor: MIKU, paddingX: 1, width: WIDTH - 2, flexDirection: 'column', height: LINES + 2 },
        ...layout(line || '음… 무슨 말 할지 생각 중이에요…').map((s, i) =>
          h(Text, { key: i, wrap: 'truncate', color: line ? undefined : t.color.muted }, s || ' ')
        )
      )
    )
  }

  const app = defineWidgetApp({
    id: 'miku-bubble',
    help: '미쿠 말풍선: AI 미쿠가 10분마다 재밌는 사실을 말해요 (켜기/끄기)',
    mode: 'ambient',
    zone: 'top-right',
    width: WIDTH,
    init: () => ({}),
    reduce: state => state,
    render: ({ t }) => h(Bubble, { t }),
  })

  openWidget(app, app.init(''))
}
