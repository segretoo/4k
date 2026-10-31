import type { EntityType, Level, RegionType } from '../api/types'
import type { PixelName } from '../components/pixels'

export const LEVELS: Level[] = ['safe', 'caution', 'high', 'very_high']

export const LEVEL_LABEL: Record<Level, string> = {
  safe: '안전',
  caution: '주의',
  high: '위험',
  very_high: '매우 위험',
}

export const TYPE_LABEL: Record<RegionType, string> = {
  name: '이름',
  age: '나이',
  school: '유치원',
  area: '장소',
  time: '등원 시간',
  contact: '연락처',
  unreadable: '읽을 수 없는 글자',
}

export const TYPE_ORDER: EntityType[] = ['name', 'age', 'school', 'area', 'time', 'contact']

export function formatDate(iso: string | null): string {
  if (!iso) return ''
  const d = new Date(iso)
  return `${d.getMonth() + 1}월 ${d.getDate()}일`
}

/** 단서 종류별 픽셀 아이콘 (와이어프레임 결과 카드와 같음) */
export const CLUE_ICON: Record<EntityType, PixelName> = { name: 'nameTag', age: 'cake', school: 'school', area: 'house', time: 'clock', contact: 'nameTag' }
