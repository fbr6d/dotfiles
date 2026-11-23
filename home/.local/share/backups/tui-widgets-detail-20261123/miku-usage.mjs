// 미쿠 TUI 상태 줄 (2026-11-19, 마스터 요청) — 원래 아래 줄(display.tui_statusbar: false)을 대신한다.
// 한 줄: 상태(준비됨/작업 중 + 경과) │ 모델 │ 추론 강도 │ 현재 제공자 사용량
// - 상태·모델·추론 강도: state.db(읽기 전용)의 현재 대화(HERMES_TUI_ACTIVE_SESSION_FILE)
//   마지막 메시지가 assistant + finish_reason 'stop'이면 준비됨, 아니면 작업 중
// - 추론 강도가 대화에 없으면 config.yaml agent.reasoning_effort
// - 사용량: `hermes usage --provider <현재 대화 제공자> --json` (1분마다, 2026-11-20 변경)
// 끄기/켜기: /miku-usage   다시 읽기: /widgets-reload   이전판: ~/.local/share/backups/tui-statusbar-20261119/
import { execFile } from 'node:child_process'
import { readFileSync } from 'node:fs'
import { join } from 'node:path'

const HOME = process.env.HERMES_HOME || join(process.env.HOME || '', '.hermes/profiles/miku')
const HERMES = join(process.env.HOME || '', '.hermes/hermes-agent/.hermes/bin/hermes')
const USAGE_MS = 60 * 1000  // 2026-11-20 마스터 요청으로 5분 → 1분
const STATE_MS = 1000
const USAGE_PROVIDERS = new Map([
  ['anthropic', { name: '클로드', five: 'Current session', week: 'Current week' }],
  ['openai-codex', { name: '코덱스', five: 'Session', week: 'Weekly' }]
])

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

const POLICY_PREFIX = 'gateway.local_policy.v1:'

function readSessionPolicy(db, sid, chatId) {
  const find = db.prepare('SELECT value FROM state_meta WHERE key = ?')
  const receipt = id => JSON.parse(find.get(POLICY_PREFIX + id)?.value || 'null')
  let saved = receipt(sid)
  if (!saved && chatId && chatId !== sid) {
    const owner = receipt(chatId)
    if (owner?.lineage?.includes(sid)) saved = owner
  }
  return saved?.policy
}

function effortLabel(value) {
  if (value === false || value?.enabled === false) return 'none'
  const effort = typeof value === 'object' ? value?.effort : value
  if (typeof effort !== 'string' || !effort.trim()) return null
  const level = effort.trim().toLowerCase()
  return ['off', 'disabled', 'false'].includes(level) ? 'none' : level
}

// 세션에서 선택한 모델과 추론은 새 응답 전에도 이 정책에 먼저 기록된다.
function applySessionPolicy(out, db, sid, chatId) {
  const policy = readSessionPolicy(db, sid, chatId)
  if (!policy) return
  const config = JSON.parse(policy.config_json || '{}')
  const request = JSON.parse(policy.request_json || '{}')
  const follows = request.follow_profile_config === true || config.follow_adopted === true
  const pinned = config.session_pins?.reasoning ?? Object.hasOwn(request, 'reasoning')
  const route = config.model
  if (!follows) {
    out.model = shortModel(policy.model || route?.default) || out.model
    if (route?.provider && route.provider !== 'auto') out.provider = route.provider
  }
  if (!follows || pinned) {
    const rawModel = policy.model || route?.default || ''
    const overrides = config.agent?.reasoning_overrides
    const override = overrides?.[rawModel] ?? overrides?.[rawModel.split('/').pop()]
    const effort = effortLabel(override ?? config.agent?.reasoning_effort)
    if (effort) out.effort = effort
  }
}

// 현재 대화 상태 한 번 읽기 (db는 열린 연결 또는 null)
function readState(db) {
  const out = { phase: 'ready', since: null, model: '', provider: null, effort: configEffort() }
  const sid = activeSid()
  if (!db || !sid) return out
  try {
    const s = db.prepare('SELECT model, model_config, chat_id FROM sessions WHERE id = ?').get(sid)
    if (s) {
      out.model = shortModel(s.model)
      try {
        const config = JSON.parse(s.model_config || '{}')
        out.provider = config.gateway_runtime?.provider || config.provider || null
        out.effort = effortLabel(config.reasoning_config) || out.effort
      } catch {}
    }
    try {
      applySessionPolicy(out, db, sid, s?.chat_id)
    } catch {}
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

function fetchUsage(provider) {
  const labels = USAGE_PROVIDERS.get(provider)
  if (!labels) return Promise.resolve({ error: '사용량 표시 미지원' })
  return new Promise(resolve => {
    execFile(HERMES, ['usage', '--provider', provider, '--json'], { timeout: 60000, env: process.env }, (err, out) => {
      if (err) return resolve({ error: '사용량 못 읽음' })
      try {
        const j = JSON.parse(out)
        if (j.unavailable_reason) return resolve({ error: '사용량 없음' })
        const win = label => (j.windows || []).find(w => w.label === label)
        const five = win(labels.five)
        const week = win(labels.week)
        resolve(five || week ? { five, week } : { error: '사용량 없음' })
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

    React.useEffect(() => {
      let alive = true
      let db = null
      try {
        if (DatabaseSync) db = new DatabaseSync(join(HOME, 'state.db'), { readOnly: true })
      } catch {}
      const tick = () => alive && setSt(readState(db))
      tick()
      const b = setInterval(tick, STATE_MS)
      return () => {
        alive = false
        clearInterval(b)
        try {
          db && db.close()
        } catch {}
      }
    }, [])

    const provider = st.provider
    const labels = USAGE_PROVIDERS.get(provider)
    const [snapshot, setSnapshot] = React.useState(null)
    React.useEffect(() => {
      setSnapshot(null)
      if (!labels) return
      let alive = true
      let pending = false
      const load = async () => {
        if (pending) return
        pending = true
        try {
          const data = await fetchUsage(provider)
          if (alive) setSnapshot({ provider, data })
        } finally {
          pending = false
        }
      }
      load()
      const timer = setInterval(load, USAGE_MS)
      return () => {
        alive = false
        clearInterval(timer)
      }
    }, [provider, labels])
    const usage = snapshot?.provider === provider ? snapshot.data : null

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
    if (!labels) parts.push(T(muted, provider ? '사용량 표시 미지원' : '사용량 대기 중…'))
    else {
      parts.push(T(muted, `${labels.name} `))
      if (!usage) parts.push(T(muted, '사용량 불러오는 중…'))
      else if (usage.error) parts.push(T(t.color.warn, usage.error))
      else {
        if (usage.five) parts.push(...win('5시간', usage.five, fmtTime))
        if (usage.five && usage.week) parts.push(sep(), T(muted, `${labels.name} `))
        if (usage.week) parts.push(...win('주간', usage.week, fmtDay))
      }
    }

    return h(Box, { flexDirection: 'row' }, ...parts)
  }

  const app = defineWidgetApp({
    id: 'miku-usage',
    help: '상태·모델·추론 강도·현재 제공자 사용량 한 줄 (켜기/끄기)',
    mode: 'ambient',
    zone: 'dock-bottom',
    init: () => ({}),
    reduce: state => state,
    render: ({ t }) => h(Line, { t })
  })

  openWidget(app, app.init(''))
}
