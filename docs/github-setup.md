# GitHub 저장소 세팅 순서 (Moon)

## 1. 저장소
- 개인 계정(Pro)에 **Private** 저장소 생성 → 이 폴더 내용을 `main`에 바로 첫 커밋 `chore: 저장소 초기 구조 세팅`
- **첫 커밋을 푸시한 뒤에** 룰셋을 켭니다. 이후로는 소유자 포함 모두 같은 규칙을 따릅니다.
- Settings → Collaborators → 팀원 3명 초대
  - 개인 저장소 협업자는 모두 쓰기 권한이 같습니다. 설정 변경은 소유자만 가능합니다.

## 2. 룰셋 (Settings → Rules → Rulesets)
**방법 A — 가져오기**: New ruleset → Import a ruleset → `.github/rulesets/main-protection.json`

**방법 B — 직접 설정**
| 항목 | 값 |
|---|---|
| Ruleset name | main-protection |
| Enforcement | Active |
| Target branches | Include default branch |
| Restrict deletions | ✅ |
| Block force pushes | ✅ |
| Require a pull request before merging | ✅ / Required approvals **1** |
| Require status checks | ❌ (해커톤 기간엔 생략) |
| Bypass list | **비워 둠** (관리자도 예외 없음) |

> 예외 없음: 소유자도 main 직접 푸시 불가, PR은 다른 1명의 승인이 있어야 병합됩니다. 마감 전 승인해 줄 사람이 깨어 있는지 미리 맞춰 두세요.

**방법 C — gh CLI**
```bash
gh api -X POST repos/segretoo/<repo>/rulesets --input .github/rulesets/main-protection.json
```

## 3. 기타 설정
- Settings → General → Pull Requests: **Allow squash merging** ✅, *Automatically delete head branches* ✅
- Labels: `.github/labels.md` 참고
- (선택) Projects 보드: Todo / In progress / Review / Done

## 4. 제출 전 공개 전환 (11/1 13:00 전)
- [ ] 커밋 기록에 `.env`, API 키, 실제 개인정보, 실제 아이 사진이 없는지 확인
  ```bash
  git log --all -p | grep -iE "api[_-]?key|secret|token|password" | head
  ```
- [ ] Settings → General → Change visibility → **Public**
- [ ] Settings → Code security → **Secret scanning / Push protection** 켜기 (공개 저장소는 무료)
- [ ] `4K_소스코드.txt` 생성, README 실행 방법 최종 확인
