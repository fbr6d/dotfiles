// 미쿠 TUI 상태 줄 (2026-11-19, 마스터 요청) — 원래 아래 줄(display.tui_statusbar: false)을 대신한다.
// 한 줄: 상태(준비됨/작업 중 + 경과) │ 모델 │ 추론 강도 │ Claude 5시간 │ 주간
// - 상태·모델·추론 강도: state.db(읽기 전용)의 현재 대화(HERMES_TUI_ACTIVE_SESSION_FILE)
//   마지막 메시지가 assistant + finish_reason 'stop'이면 준비됨, 아니면 작업 중
// - 추론 강도가 대화에 없으면 config.yaml agent.reasoning_effort
// - 사용량: `hermes usage --provider anthropic --json` (5분마다)
// 끄기/켜기: /miku-usage   다시 읽기: /widgets-reload   이전판: ~/.local/share/backups/tui-statusbar-20261119/
import { execFile } from 'node:child_process'
import { readFileSync } from 'node:fs'
import { join } from 'node:path'

const HOME = process.env.HERMES_HOME || join(process.env.HOME || '', '.hermes/profiles/miku')
const HERMES = join(process.env.HOME || '', '.hermes/hermes-agent/.hermes/bin/hermes')
const USAGE_MS = 5 * 60 * 1000
const STATE_MS = 1000

let DatabaseSync = null
try {
  ;({ DatabaseSync } = await import('node:sqlite'))
} catch {}

function configEffort() {
  try {
    const text = readFileSync(join(HOME, 'config.yaml'), 'utf8')
    const m = text.match(/^ {2}reasoning_effort:\s*["']?([A-Za-z-]*)["']?\s*$/m)
    return m && m[1] ? m[1] : 'medium'
  } catch {
    return '?'
  }
}

const shortModel = m =>
  String(m || '')
    .split('/')
    .pop()
    .replace(/^claude[-_]/, '')
    .replace(/^anthropic[-_]/, '')
    .replace(/[-_]/g, ' ')
    .replace(/\b(\d+)\s+(\d+)\b/g, '$1.$2')
    .trim()

function activeSid() {
  try {
    const file = process.env.HERMES_TUI_ACTIVE_SESSION_FILE
    return file ? JSON.parse(readFileSync(file, 'utf8')).session_id || null : null
  } catch {
    return null
  }
}

// 현재 대화 상태 한 번 읽기 (db는 열린 연결 또는 null)
function readState(db) {
  const out = { phase: 'ready', since: null, model: '', effort: configEffort() }
  const sid = activeSid()
  if (!db || !sid) return out
  try {
    const s = db.prepare('SELECT model, model_config FROM sessions WHERE id = ?').get(sid)
    if (s) {
      out.model = shortModel(s.model)
      try {
        const rc = s.model_config ? JSON.parse(s.model_config).reasoning_config : null
        if (rc && typeof rc === 'object') out.effort = rc.enabled === false ? 'none' : String(rc.effort || 'medium')
      } catch {}
    }
    const last = db
      .prepare('SELECT role, finish_reason FROM messages WHERE session_id = ? ORDER BY id DESC LIMIT 1')
      .get(sid)
    if (last && !(last.role === 'assistant' && last.finish_reason === 'stop')) {
      out.phase = 'busy'
      const u = db
        .prepare("SELECT timestamp FROM messages WHERE session_id = ? AND role = 'user' ORDER BY id DESC LIMIT 1")
        .get(sid)
      out.since = u ? Number(u.timestamp) : null
    }
  } catch {}
  return out
}

function fetchUsage() {
  return new Promise(resolve => {
    execFile(HERMES, ['usage', '--provider', 'anthropic', '--json'], { timeout: 60000, env: process.env }, (err, out) => {
      if (err) return resolve({ error: '사용량 못 읽음' })
      try {
        const j = JSON.parse(out)
        if (j.unavailable_reason) return resolve({ error: '사용량 없음' })
        const win = label => (j.windows || []).find(w => w.label === label)
        resolve({ five: win('Current session'), week: win('Current week') })
      } catch {
        resolve({ error: '사용량 해석 실패' })
      }
    })
  })
}

const pad = n => String(n).padStart(2, '0')
const fmtTime = iso => {
  const d = new Date(iso)
  return isNaN(d) ? '' : `${pad(d.getHours())}:${pad(d.getMinutes())}`
}
const fmtDay = iso => {
  const d = new Date(iso)
  return isNaN(d) ? '' : `${d.getMonth() + 1}/${d.getDate()} ${pad(d.getHours())}:${pad(d.getMinutes())}`
}
const fmtElapsed = since => {
  if (!since) return ''
  const s = Math.max(0, Math.floor(Date.now() / 1000 - since))
  return s < 60 ? ` ${s}초` : s < 3600 ? ` ${Math.floor(s / 60)}분 ${s % 60}초` : ` ${Math.floor(s / 3600)}시간 ${Math.floor((s % 3600) / 60)}분`
}

export default function register(sdk) {
  const { Box, Text, React, defineWidgetApp, h, openWidget } = sdk

  function Line({ t }) {
    const [st, setSt] = React.useState(() => readState(null))
    const [usage, setUsage] = React.useState(null)

    React.useEffect(() => {
      let alive = true
      let db = null
      try {
        if (DatabaseSync) db = new DatabaseSync(join(HOME, 'state.db'), { readOnly: true })
      } catch {}
      const tick = () => alive && setSt(readState(db))
      const load = () => fetchUsage().then(u => alive && setUsage(u))
      tick()
      load()
      const a = setInterval(load, USAGE_MS)
      const b = setInterval(tick, STATE_MS)
      return () => {
        alive = false
        clearInterval(a)
        clearInterval(b)
        try {
          db && db.close()
        } catch {}
      }
    }, [])

    const muted = t.color.muted
    const tone = p => (p >= 90 ? t.color.error : p >= 70 ? t.color.warn : t.color.ok)
    let k = 0
    const T = (color, text) => h(Text, { color, key: k++ }, text)
    const sep = () => T(muted, ' │ ')
    const win = (name, w, fmt) =>
      w
        ? [T(muted, `${name} `), T(tone(w.used_percent), `${Math.round(w.used_percent)}%`), T(muted, w.resets_at ? ` (${fmt(w.resets_at)})` : '')]
        : [T(muted, `${name} -`)]

    const parts =
      st.phase === 'busy'
        ? [T(t.color.warn, `◐ 작업 중${fmtElapsed(st.since)}`)]
        : [T(t.color.ok, '● 준비됨')]
    if (st.model) parts.push(sep(), T(t.color.label, st.model))
    parts.push(sep(), T(muted, '추론 '), T(t.color.label, st.effort), sep())
    if (!usage) parts.push(T(muted, '사용량 불러오는 중…'))
    else if (usage.error) parts.push(T(t.color.warn, usage.error))
    else parts.push(...win('5시간', usage.five, fmtTime), sep(), ...win('주간', usage.week, fmtDay))

    return h(Box, { flexDirection: 'row' }, ...parts)
  }

  const app = defineWidgetApp({
    id: 'miku-usage',
    help: '상태·모델·추론 강도·Claude 5시간/주간 사용량 한 줄 (켜기/끄기)',
    mode: 'ambient',
    zone: 'dock-bottom',
    init: () => ({}),
    reduce: state => state,
    render: ({ t }) => h(Line, { t })
  })

  openWidget(app, app.init(''))
}
