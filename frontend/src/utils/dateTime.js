const ISO_LIKE_DATE_RE = /^\d{4}-\d{2}-\d{2}$/
const NAIVE_ISO_DATETIME_RE = /^\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}(?::\d{2}(?:\.\d{1,6})?)?$/
const HAS_TIMEZONE_SUFFIX_RE = /([zZ]|[+-]\d{2}:?\d{2})$/

function asDate(value) {
  if (value instanceof Date) {
    return Number.isNaN(value.getTime()) ? null : new Date(value.getTime())
  }

  const raw = String(value || '').trim()
  if (!raw) {
    return null
  }

  const direct = new Date(raw)
  if (!Number.isNaN(direct.getTime())) {
    return direct
  }

  const noComma = new Date(raw.replace(',', ''))
  if (!Number.isNaN(noComma.getTime())) {
    return noComma
  }

  return null
}

export function parseServerDate(value) {
  const raw = String(value || '').trim()
  if (!raw) {
    return value instanceof Date ? asDate(value) : null
  }

  const normalizedIso = raw.includes('T') ? raw : raw.replace(' ', 'T')
  const hasTimezone = HAS_TIMEZONE_SUFFIX_RE.test(normalizedIso)
  const looksNaiveIso = ISO_LIKE_DATE_RE.test(raw) || NAIVE_ISO_DATETIME_RE.test(raw)

  if (looksNaiveIso && !hasTimezone) {
    const utcCandidate = new Date(`${normalizedIso}Z`)
    if (!Number.isNaN(utcCandidate.getTime())) {
      return utcCandidate
    }
  }

  return asDate(raw)
}

export function parseBooleanFlag(value) {
  if (typeof value === 'boolean') return value
  if (typeof value === 'number') return value !== 0

  const normalized = String(value || '').trim().toLowerCase()
  if (!normalized) return false

  if (['true', '1', 'yes', 'y'].includes(normalized)) return true
  if (['false', '0', 'no', 'n'].includes(normalized)) return false

  return Boolean(value)
}
