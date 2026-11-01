// backend/app/schemas/contracts.py 와 같은 이름을 쓴다. 계약을 바꾸면 양쪽을 같이 고친다.
export type EntityType = 'name' | 'age' | 'school' | 'area' | 'time' | 'contact'
export type Level = 'safe' | 'caution' | 'high' | 'very_high'
export type Box = [number, number, number, number]
export type Polygon = [number, number][]

export interface Clue {
  type: EntityType
  value: string
}

export interface PhotoSummary {
  photo_id: string
  thumb_url: string
}

export interface CaptionCandidate {
  id: string
  type: EntityType
  value: string
  source: 'caption' | 'hashtag'
  why: string
  selected_by_default: boolean
}

export interface ManualCaptionClue {
  type: EntityType
  value: string
}

export interface PostSummary {
  post_id: string
  posted_at: string | null
  caption: string
  photos: PhotoSummary[]
  hashtags: string[]
  candidates: CaptionCandidate[]
  recommended: boolean
  hints: string[]
  score: number
}

export interface UploadResponse {
  upload_id: string
  total_posts: number
  total_photos: number
  max_select: number
  recommended_photo_ids: string[]
  posts: PostSummary[]
}

export interface JobCreated {
  job_id: string
  total: number
}

export interface CleanupItem {
  post_id: string
  posted_at: string | null
  caption: string
  photo_ids: string[]
  clues: Clue[]
  cuts: string[]
}

export interface EngineResult {
  level: Level
  reason: EntityType[]
  card: Partial<Record<EntityType, string>>
  sources: Partial<Record<EntityType, string[]>>
  explanation: string
  cleanup: string[]
  cleanup_items: CleanupItem[]
  level_after_cleanup: Level | null
  remaining_after_cleanup: EntityType[]
  clues: Clue[]
  analyzed_posts: number
  failed_photo_ids: string[]
  post_results: PostAnalysisResult[]
}

export interface DetectedEntity {
  type: EntityType
  value: string
  evidence: 'image' | 'caption'
  box?: Box | null
  polygon?: Polygon | null
  path?: string | null
  why: string
  time_source?: 'analog_clock' | 'digital_clock' | 'text_timestamp' | 'schedule' | 'none' | null
}

export interface PhotoAnalysisResult {
  photo_id: string
  source: string
  size: number[]
  entities: DetectedEntity[]
  risk_level: Level
  analysis_failed: boolean
}

export interface PostAnalysisResult {
  post_id: string
  posted_at: string | null
  caption: string
  hashtags: string[]
  selected_candidate_ids: string[]
  risk_level: Level
  photos: PhotoAnalysisResult[]
}

export interface JobStatus {
  status: 'queued' | 'running' | 'done' | 'failed'
  done: number
  total: number
  result: EngineResult | null
  error: string | null
}

export type RegionType = EntityType | 'unreadable'

export interface Region {
  id: string
  type: RegionType
  text: string
  box: Box
  polygon?: Polygon | null
  path?: string | null
  time_source?: 'analog_clock' | 'digital_clock' | 'text_timestamp' | 'schedule' | 'none' | null
}

export interface Warning {
  type: RegionType
  severity: 'high' | 'medium' | 'check'
  why: string
  action: string
  region_ids: string[]
  in_caption: boolean
}

export interface CaptionEdit {
  id: string
  type: EntityType
  text: string
}

export interface CheckResponse {
  level_now: Level | null
  level_if_posted: Level
  added: EntityType[]
  warnings: Warning[]
  regions: Region[]
  caption_suggestion: string
  caption_edits: CaptionEdit[]
  image_size: [number, number]
  requires_review: boolean
  review_reasons: string[]
  ocr_texts?: { text: string; box?: Box | null; polygon?: Polygon | null; path?: string | null; source: 'ocr' | 'vlm' | 'caption'; conf?: number | null }[]
  pipeline_metrics?: Record<string, unknown>
}

export interface MaskFragment {
  region_id: string
  crop_box_original_pixels: Box
  patch_base64: string
  alpha_base64: string
  media_type: 'image/png'
}

export interface MaskResponse {
  fragments: MaskFragment[]
  rescan_passed: boolean
  leaked: string[]
  meta_clean: boolean
  requires_review: boolean
}

export interface ServerStatus {
  gpu_mock: boolean
  gpu_ok: boolean
  max_photos: number
  max_zip_mb: number
}
