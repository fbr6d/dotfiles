// KSAT 계획서 전체 진행도 (2026-11-19, 마스터 요청: 카드 장수 말고 계획서 전체 진행도) — 오른쪽 위, 미쿠 도트 그림 아래.
// 2026-11-23 마스터: 말풍선 위젯을 빼고 이 칸을 더 상세하게(과목별 지금 단계, 칸반 현황, 실행 카드 3줄, 최근 끝난 카드 2줄). 이전판 ~/.local/share/backups/tui-widgets-detail-20261123/
// scripts/ksat_plan_progress.py(읽기 전용)를 REFRESH_MS마다 불러 JSON을 받는다.
// 기준: plan/20261118_전과목_위키정식판_PDF 최신 판(스크립트가 자동 선택) 4절 작업 순서 17단계(자세한 채점은 스크립트 머리말).
// 켜기/끄기: /miku-ksat   다시 읽기: /widgets-reload
import { execFile } from 'node:child_process'
import { join } from 'node:path'

const SCRIPT = join(process.env.HOME || '', '.hermes/profiles/miku/scripts/ksat_plan_progress.py')
const REFRESH_MS = 10 * 1000 // 2026-11-19 마스터 요청: 1분 → 10초 (스크립트 한 번 약 0.6초)
const WIDTH = 54 // miku-art 칸 폭과 맞춘다
// 2026-11-23 마스터 '색이 디자인 가이드랑 안 맞아': 스킨 색(ok/warn/error, 미쿠 청록) 대신 ~/Documents/design-guide.md 토큰을 직접 쓴다.
// 무채색 우선 · 색은 상태에만(완료 green, 지금 진행 mauve, 주의 peach, 위험 red) · 단계 색 green→blue→peach→red. 이전판 .bak-before-guide
const G = {
  text: '#faf9f5', muted: '#c2c0b6', dim: '#9c9a92', raised: '#4a4a47', surface: '#30302e',
  green: '#a6e3a1', blue: '#89b4fa', peach: '#fab387', red: '#f38ba8', mauve: '#cba6f7',
}
const level = pct => (pct < 30 ? G.green : pct < 60 ? G.blue : pct < 85 ? G.peach : G.red) // 가이드 2.4

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

    const muted = G.dim
    let k = 0
    const T = (color, text, extra) => h(Text, { color, key: k++, ...(extra || {}) }, text)
    // 2026-11-23: 줄을 Box 안 Text 여러 개로 그리면 Ink가 조각 끝 빈칸을 지워 칸이 어긋났다('진행 중수학', '검수 4/4PDF').
    // 한 줄을 Text 하나 안의 중첩 Text로 묶으면 빈칸이 줄 안에 남는다.
    const Row = (...kids) => h(Text, { key: k++, wrap: 'truncate' }, ...kids)
    const rows = []

    if (!p) rows.push(T(muted, '계획서 진행도 계산 중…'))
    else if (p.error) rows.push(T(G.red, p.error))
    else {
      // 2026-11-23 마스터 '더 상세하게' (말풍선 위젯을 빼서 생긴 자리로 12줄 → 18줄).
      // 줄 수는 항상 고정(본문 15줄): 막대 · 무게/Codex · 진행 중 · 과목 5 · 칸반 현황 · 실행 카드 3 · 최근 완료 2 · 기준 시각
      const fit = (s, w) => padTo(width(s) <= w ? s : clip(s, w), w)
      const barW = WIDTH - 14
      const fill = Math.round((p.percent / 100) * barW)
      // 가이드 9.6: 홈 raised, 채움 text(흰색)
      rows.push(Row(T(G.text, '█'.repeat(fill)), T(G.raised, '░'.repeat(barW - fill)), T(G.text, ` ${p.percent}%`, { bold: true })))
      // 2026-11-20 마스터 요청: Codex 주간 사용량(KSAT 봇 공용)을 같은 줄에 (98%면 새 카드 멈춤 기준)
      const cx = p.codex
      const cxCol = !cx ? muted : level(cx.pct)
      rows.push(Row(
        // 2026-11-21 마스터: 단계 수 대신 전체 가중치(대략 걸리는 시간) 기준
        T(muted, `전체 무게 ${p.weight_done}/${p.weight_total} · `),
        T(muted, 'Codex 주간 '),
        T(cxCol, cx ? `${cx.pct}%` : '?', { bold: true })
      ))
      const act = p.active || []
      const short = n => n.replace(' 위키 정식판', ' 위키').replace(' 1~2일차 PDF', ' PDF').replace(' 자료 확장', ' 확장').replace('통합사회', '사회').replace('통합과학', '과학')
      if (act.length) rows.push(Row(T(G.mauve, '▶ 진행 중\u00a0'), T(G.text, clip(act.map(a => `${short(a.name)} ${a.pct}%`).join(' · '), WIDTH - 14))))
      else if (p.current) rows.push(Row(T(G.mauve, '▶ 다음\u00a0'), T(G.text, clip(short(p.current.name), WIDTH - 12))))
      else rows.push(T(G.green, '✓ 계획서 단계를 모두 마쳤어요!'))
      // 과목 5줄: 위키는 '% + 지금 단계(공식 범위/개념 목록/집필/검수 완료/전체/인수 대기)'
      for (const s of p.subjects) {
        // 완료 green · 진행 중 글자는 흰색(표시 ◐만 mauve) · 대기 dim
        const wikiColor = s.final ? G.green : s.wiki === '대기' ? muted : G.text
        const markColor = s.final ? G.green : s.wiki === '대기' ? muted : G.mauve
        const mark = s.final && s.pdf === 2 ? '●' : s.wiki === '대기' && !s.pdf ? '○' : '◐'
        const wikiText = s.final || s.wiki === '대기' ? s.wiki : `${s.wiki_pct ?? 0}% ${s.stage || s.wiki}`
        rows.push(
          Row(
            T(markColor, `${mark} `),
            T(G.text, padTo(s.name, 9)),
            T(muted, '위키 '),
            T(wikiColor, fit(wikiText, 12)),
            T(muted, ' PDF '),
            // v12(2026-11-22): 0이면 미쿠판 진행 상태(제작중/보류/대기)를 대신 보여 준다
            T(s.pdf === 2 ? G.green : s.pdf ? G.text : s.pdf_note === '보류' ? G.peach : s.pdf_note ? G.mauve : muted,
              padTo(!s.pdf ? (s.pdf_note || '미제작') : s.pdf >= 2 ? '확정' : s.pdf_note === '수정중' ? '수정중' : '제작됨', 7)),  // 2026-11-22 마스터: 숫자(0/2) 대신 글자
            // v13 3-4절: raw 전체 자료 확장 진행
            T(muted, '확장 '),
            T(s.ext_pct >= 100 ? G.green : s.ext_pct ? G.text : muted, `${s.ext_pct || 0}%`)
          )
        )
      }
      // 칸반 현황 한 줄 (마스터 결정이 필요한 건이 있으면 그 자리에 빨갛게 — 2026-11-19 '결정 필요는 한 줄로')
      const att = p.attention || []
      const b = p.board || {}
      if (att.length) {
        const head = `! 결정 필요 ${att.length}건 · `
        rows.push(Row(T(G.red, head, { bold: true }), T(G.red, clip(att.map(a => a.task).join(', '), WIDTH - 6 - width(head)))))
      } else {
        rows.push(Row(
          T(G.text, '칸반 ', { bold: true }),
          T(muted, '실행 '), T(b.running ? G.mauve : G.text, `${b.running ?? '?'}`, { bold: true }),
          T(muted, ' · 대기 '), T(G.text, `${b.waiting ?? '?'}`),
          T(muted, ' · 멈춤 '), T(b.stopped ? G.peach : G.text, `${b.stopped ?? '?'}`),
          T(muted, ' · 오늘 완료 '), T(G.green, `${b.done_today ?? '?'}`, { bold: true })
        ))
      }
      // 실행 중 카드 3줄: 시간 진행 막대(시작 후 경과 / 최대 실행 시간) — 실제 작업 %가 아님. 신호 5분 넘게 끊기면 빨강
      const run = p.running || []
      const RUN_ROWS = 3
      const cardRow = c => {
        const stale = c.beat_ago_min >= 5
        const col = stale ? G.red : G.mauve
        const bw = 8
        const f = Math.max(0, Math.min(bw, Math.round((c.elapsed_min / Math.max(1, c.max_min)) * bw)))
        const tail = ` ${c.elapsed_min}/${c.max_min}분` + (stale ? ` · 신호 ${c.beat_ago_min}분 끊김` : '')
        const head = `▸ ${c.who}·${c.model} `
        const titleW = WIDTH - 6 - width(head) - bw - width(tail) - 2
        return Row(T(col, head), T(G.text, padTo(clip(c.title, titleW), titleW) + ' '), T(col, '▓'.repeat(f)), T(G.raised, '░'.repeat(bw - f)), T(stale ? G.red : muted, tail))
      }
      const slot = []
      if (!run.length) slot.push(T(muted, '▸ 실행 중인 카드 없음'))
      else {
        const n = run.length > RUN_ROWS ? RUN_ROWS - 1 : run.length
        for (const c of run.slice(0, n)) slot.push(cardRow(c))
        if (run.length > n) slot.push(T(muted, `▸ 그 밖에 ${run.length - n}개 더 실행 중`))
      }
      while (slot.length < RUN_ROWS) slot.push(T(muted, ' '))
      rows.push(...slot)
      // 최근 끝난 카드 2줄
      const rec = p.recent || []
      for (let i = 0; i < 2; i++) {
        const r = rec[i]
        if (!r) { rows.push(T(muted, i ? ' ' : '✓ 최근 끝난 카드 없음')); continue }
        const head = `✓ ${r.at} ${r.who} ${r.min}분 `
        rows.push(Row(T(G.green, head), T(G.muted, clip(r.title, WIDTH - 6 - width(head)))))
      }
      const at = new Date(p.at * 1000)
      rows.push(T(muted, `${pad(at.getHours())}:${pad(at.getMinutes())}:${pad(at.getSeconds())} 기준 · 10초마다 갱신`))
    }

    // 2026-11-20: 칸과 줄마다 flexShrink 0. 오른쪽 레일 높이가 모자라면 Yoga가 줄을 눌러 줄이며
    // 반올림 때문에 줄끼리 겹쳐 그려졌다(말풍선과 같은 문제). Text는 flexShrink를 못 받아 Box로 감싼다.
    const fixRow = (r, i) => h(Box, { key: `fix${i}`, flexShrink: 0, height: 1 }, r)
    return h(
      Box,
      { flexDirection: 'column', borderStyle: 'round', borderColor: G.surface, /* 가이드 5.2: 테두리는 surface로 녹여 거의 안 보이게(칸 크기 그대로) */ paddingX: 1, width: WIDTH - 2, flexShrink: 0 },
      ...[Row(T(G.text, `KSAT 계획서 ${(p && p.version) || ''}`, { bold: true }), T(muted, ' · 위키 정식판 + 첫 2일 PDF')), ...rows].map(fixRow)
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
