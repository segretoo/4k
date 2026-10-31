/** 캡션에서 고른 조각을 빼고 공백을 정리한다. backend/app/services/precheck.py 의 apply_edits 와 같은 규칙. */
export function applyEdits(caption: string, texts: string[]): string {
  let out = caption
  for (const t of [...texts].sort((a, b) => b.length - a.length)) out = out.split(t).join(' ')
  return out.replace(/\s+/g, ' ').trim()
}
