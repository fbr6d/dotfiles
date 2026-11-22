// KSAT 계획서 전체 진행도 (2026-11-19, 마스터 요청: 카드 장수 말고 계획서 전체 진행도) — 오른쪽 위, 미쿠 말풍선 아래.
// scripts/ksat_plan_progress.py(읽기 전용)를 REFRESH_MS마다 불러 JSON을 받는다.
// 기준: plan/20261118_전과목_위키정식판_PDF 최신 판(스크립트가 자동 선택) 4절 작업 순서 17단계(자세한 채점은 스크립트 머리말).
// 켜기/끄기: /miku-ksat   다시 읽기: /widgets-reload
import { execFile } from 'node:child_process'
import { join } from 'node:path'

const SCRIPT = join(process.env.HOME || '', '.hermes/profiles/miku/scripts/ksat_plan_progress.py')
const REFRESH_MS = 10 * 1000 // 2026-11-19 마스터 요청: 1분 → 10초 (스크립트 한 번 약 0.6초)
const WIDTH = 54 // miku-art 칸 폭과 맞춘다
const MIKU = '#39C5BB'

function fetchProgress() {
  return new Promise(resolve => {
    execFile('python3', [SCRIPT], { timeout: 9000, env: process.env }, (err, out) => {
      if (err) return resolve({ error: '진행도를 못 읽었어요' })
      try {
        const j = JSON.parse(String(out).trim().split('\n').pop())
        resolve(j.error ? { error: '진행도 계산 실패' } : j)
      } catch {
        resolve({ error: '진행도를 해석 못 했어요' })
      }
    })
  })
}

const pad = v => String(v).padStart(2, '0')
// 화면 폭 기준 자르기·맞추기: 한글·전각 문자는 2칸
const cellW = ch => (/[\u1100-\u115F\u2E80-\uA4CF\uAC00-\uD7A3\uF900-\uFAFF\uFE30-\uFE4F\uFF00-\uFF60\uFFE0-\uFFE6]/.test(ch) ? 2 : 1)
const width = s => [...s].reduce((n, ch) => n + cellW(ch), 0)
const padTo = (s, w) => s + ' '.repeat(Math.max(0, w - width(s)))
const clip = (s, w) => {
  let used = 0
  let out = ''
  for (const ch of s) {
    const cw = cellW(ch)
    if (used + cw > w - 1) return out + '…'
    out += ch
    used += cw
  }
  return out
}

export default function register(sdk) {
  const { Box, Text, React, defineWidgetApp, h, openWidget } = sdk

  function Board({ t }) {
    const [p, setP] = React.useState(null)
    React.useEffect(() => {
      let alive = true
      let busy = false // 앞 계산이 안 끝났으면 이번 차례는 건너뛴다(겹쳐 돌지 않게)
      const load = () => {
        if (busy) return
        busy = true
        fetchProgress().then(r => {
          busy = false
          if (alive) setP(r)
        })
      }
      load()
      const id = setInterval(load, REFRESH_MS)
      return () => {
        alive = false
        clearInterval(id)
      }
    }, [])

    const muted = t.color.muted
    let k = 0
    const T = (color, text, extra) => h(Text, { color, key: k++, ...(extra || {}) }, text)
    const Row = (...kids) => h(Box, { key: k++, flexDirection: 'row' }, ...kids)
    const rows = []

    if (!p) rows.push(T(muted, '계획서 진행도 계산 중…'))
    else if (p.error) rows.push(T(t.color.warn, p.error))
    else {
      // 2026-11-19 마스터 요청: 결정 필요는 몇 건이든 한 줄로(칸 높이 고정)
      const att = p.attention || []
      if (att.length) {
        const head = `! 결정 필요 ${att.length}건 · `
        rows.push(Row(T(t.color.error, head, { bold: true }), T(t.color.error, clip(att.map(a => a.task).join(', '), WIDTH - 6 - width(head)))))
      }
      const barW = WIDTH - 14
      const fill = Math.round((p.percent / 100) * barW)
      rows.push(Row(T(t.color.ok, '█'.repeat(fill)), T(muted, '░'.repeat(barW - fill)), T(t.color.ok, ` ${p.percent}%`)))
      // 2026-11-20 마스터 요청: Codex 주간 사용량(KSAT 봇 공용)을 같은 줄에 (98%면 새 카드 멈춤 기준)
      const cx = p.codex
      const cxCol = !cx ? muted : cx.pct >= 95 ? t.color.error : cx.pct >= 80 ? t.color.warn : t.color.ok
      rows.push(Row(
        // 2026-11-21 마스터: 단계 수 대신 전체 가중치(대략 걸리는 시간) 기준
        T(muted, `전체 무게 ${p.weight_done}/${p.weight_total} · `),
        T(muted, 'Codex 주간 '),
        T(cxCol, cx ? `${cx.pct}%` : '?', { bold: true })
      ))
      const act = p.active || []
      const short = n => n.replace(' 위키 정식판', ' 위키').replace(' 1~2일차 PDF', ' PDF').replace('통합사회', '사회').replace('통합과학', '과학')
      if (act.length) rows.push(Row(T(MIKU, '▶ 진행 중 '), T(undefined, clip(act.map(a => `${short(a.name)} ${a.pct}%`).join(' · '), WIDTH - 14))))
      else if (p.current) rows.push(Row(T(MIKU, '▶ 다음 '), T(undefined, clip(short(p.current.name), WIDTH - 12))))
      else rows.push(T(t.color.ok, '✓ 계획서 단계를 모두 마쳤어요!'))
      // 2026-11-20 마스터 B안: 아직 시작 안 한 과목(위키 대기·PDF 0)은 한 줄로 묶고,
      // 남는 줄에 실행 중 카드를 보여 준다. 과목+카드 줄 수는 항상 SLOT_ROWS(=과목 수)로 고정(칸 높이 들썩임 방지).
      const SLOT_ROWS = p.subjects.length
      const waiting = p.subjects.filter(s => s.wiki === '대기' && !s.pdf)
      const shown = waiting.length >= 2 ? p.subjects.filter(s => !waiting.includes(s)) : p.subjects
      const slot = []
      for (const s of shown) {
        const wikiColor = s.final ? t.color.ok : s.wiki === '대기' ? muted : t.color.warn
        const mark = s.final && s.pdf === 2 ? '●' : s.wiki === '대기' && !s.pdf ? '○' : '◐'
        slot.push(
          Row(
            T(wikiColor, `${mark} `),
            T(undefined, padTo(s.name, 9)),
            T(muted, '위키 '),
            T(wikiColor, padTo(!s.final && s.wiki !== '대기' && s.wiki_pct != null ? `${s.wiki} ${s.wiki_pct}%` : s.wiki, 13)),
            T(muted, 'PDF '),
            T(s.pdf === 2 ? t.color.ok : s.pdf ? t.color.warn : muted, `${s.pdf}/2`)
          )
        )
      }
      if (waiting.length >= 2) slot.push(Row(T(muted, '○ 대기 '), T(muted, clip(waiting.map(s => s.name).join('·'), WIDTH - 12))))
      // 실행 중 카드: 시간 진행 막대(시작 후 경과 / 최대 실행 시간) — 실제 작업 %가 아님. 신호 5분 넘게 끊기면 빨강
      const run = p.running || []
      let room = SLOT_ROWS - slot.length
      const cardRow = c => {
        const stale = c.beat_ago_min >= 5
        const col = stale ? t.color.error : MIKU
        const bw = 8
        const f = Math.max(0, Math.min(bw, Math.round((c.elapsed_min / Math.max(1, c.max_min)) * bw)))
        const tail = ` ${c.elapsed_min}/${c.max_min}분` + (stale ? ` · 신호 ${c.beat_ago_min}분 끊김` : '')
        const head = `▸ ${c.who}·${c.model} `
        const titleW = WIDTH - 6 - width(head) - bw - width(tail) - 2
        return Row(T(col, head), T(undefined, padTo(clip(c.title, titleW), titleW) + ' '), T(col, '▓'.repeat(f)), T(muted, '░'.repeat(bw - f)), T(stale ? t.color.error : muted, tail))
      }
      if (room > 0) {
        if (!run.length) { slot.push(T(muted, '▸ 실행 중인 카드 없음')); room-- }
        else {
          const n = run.length > room ? room - 1 : run.length
          for (const c of run.slice(0, n)) slot.push(cardRow(c))
          if (run.length > n) slot.push(T(muted, `▸ 그 밖에 ${run.length - n}개 더 실행 중`))
        }
      }
      while (slot.length < SLOT_ROWS) slot.push(T(muted, ' '))
      rows.push(...slot.slice(0, Math.max(SLOT_ROWS, slot.length)))
      const at = new Date(p.at * 1000)
      rows.push(T(muted, `${pad(at.getHours())}:${pad(at.getMinutes())}:${pad(at.getSeconds())} 기준 · 10초마다 갱신`))
    }

    // 2026-11-20: 칸과 줄마다 flexShrink 0. 오른쪽 레일 높이가 모자라면 Yoga가 줄을 눌러 줄이며
    // 반올림 때문에 줄끼리 겹쳐 그려졌다(말풍선과 같은 문제). Text는 flexShrink를 못 받아 Box로 감싼다.
    const fixRow = (r, i) => h(Box, { key: `fix${i}`, flexShrink: 0, height: 1 }, r)
    return h(
      Box,
      { flexDirection: 'column', borderStyle: 'round', borderColor: muted, paddingX: 1, width: WIDTH - 2, flexShrink: 0 },
      ...[Row(T(MIKU, `KSAT 계획서 ${(p && p.version) || ''}`, { bold: true }), T(muted, ' · 위키 정식판 + 첫 2일 PDF')), ...rows].map(fixRow)
    )
  }

  const app = defineWidgetApp({
    id: 'miku-ksat',
    help: 'KSAT 계획서 전체 진행도 (켜기/끄기)',
    mode: 'ambient',
    zone: 'top-right',
    width: WIDTH,
    init: () => ({}),
    reduce: state => state,
    render: ({ t }) => h(Board, { t }),
  })

  openWidget(app, app.init(''))
}
