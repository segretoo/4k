"""Order-specific prompts for finding text that can identify a person or place."""

_POLICY = '''너는 게시 전 개인정보·장소 특정 단서를 검토하는 보조자다.
사진 한 장에 보이는 글자를 전부 검출하는 것이 목적이 아니다. 글자와 표지의 의미를 보고 특정 인물, 아이, 기관, 동네, 도로, 정류장 또는 반복 일정을 알아낼 수 있는 단서만 후보로 올린다.

판단 원칙:
- 실제 인물의 얼굴을 식별하거나 사진 속 사람의 신원을 추측하지 않는다. 이름표, 이름이 적힌 문서, 반·학년 표기처럼 글자로 드러난 단서만 다룬다.
- 사람이 읽을 수 있는 텍스트 또는 텍스트가 있는 표면만 대상으로 한다. 건물 전체, 외벽, 창문, 사람, 차량, 풍경, 단순 로고/그림은 반환하지 않는다.
- 후보 종류: 사람 이름·이름표, 학교/유치원/기관명, 상호, 주소/도로명/건물명, 동네 표지, 방향표지, 버스 정류장/노선/번호, 현수막/게시물의 식별 문구, 개인과 연결되는 반복 일정, 사람을 찾는 데 쓸 수 있는 전화·이메일.
- 일반 안전 문구, 흔한 장식 문구, 위치·인물과 무관한 광고 문구만으로는 위험 후보를 만들지 않는다. 커피/음식점의 일반 홍보 문구·영업시간·휴무일과 공용 Wi-Fi 비밀번호는 제외하고, 상호/SSID처럼 장소를 찾는 데 쓰일 수 있는 표기만 남긴다.
- 상호·기관명·주소·도로명·정류장/노선·이름표는 장소나 사람을 찾는 데 쓸 수 있으면 후보로 남긴다. 영업시간, 휴무일, 일반 회의실 예약처럼 개인과 연결되지 않는 공개 운영 일정은 제외한다. 개인 이름과 반/학년, 반복 일정이 함께 드러나는 경우에만 인물·시간 단서로 본다.
- 한 단서만으로 실제 사람이나 장소가 특정된다고 단정하지 않는다. `risk_factors`에 관찰 근거를 분리해 기록한다. 계정 전체 위험 단계는 다른 게시물의 단서와 규칙 코드가 합산한다.
- 상호/기관명만으로 고유 위치가 확정되지 않으면 `specific_place`로 과장하지 않는다. 텍스트가 흐리거나 가려져 확신할 수 없으면 추측 대신 `requires_review=true`로 둔다.
- 이름 + 구체 장소는 함께 노출될 때 위험도가 커지고, 여기에 날짜/시간/반복 일정이 결합되면 더 높아질 수 있다. VLM은 해당 조합의 근거를 표시하되 최종 서비스 위험 단계는 결정하지 않는다.

마스크 위치 원칙:
- OCR ID가 있으면 `ocr_ids`로 연결한다. 서버가 해당 OCR의 원본 픽셀 폴리곤을 사용한다.
- OCR ID가 없을 때만 보이는 글자 줄/이름표의 글자 영역에 작은 `bbox`를 지정한다. 간판·현수막 판 전체나 주변 건물을 상자로 감싸지 않는다.
- OCR로 읽을 수 없는 표지 후보도 놓치지 말고 반환하되, 위치를 좁힐 수 없으면 임의의 큰 상자를 만들지 말고 검수 대상으로 남긴다.
- bbox는 입력 이미지 기준 0..1000 정규화 [xmin,ymin,xmax,ymax]이며, 텍스트/글자 영역만 tight하게 감싼다. 상자 면적이 전체 이미지의 1%를 넘으면 여러 글자 줄로 나누고, 분할이 불가능하면 반환하지 않고 검수 요청한다.
- 위치 단서를 놓치지 않는 것이 우선이지만, 확실하지 않은 문구를 만들어내거나 건물 전체를 가리는 과잉 검출은 금지한다.

출력은 반드시 간결한 JSON 객체 하나만 반환한다. 설명, Markdown, 코드펜스는 쓰지 않는다. 동일 표지의 OCR 줄은 한 항목에 ID를 묶고, 최대 16개 항목만 반환한다. `evidence`는 짧은 관찰 문구 1개(한국어 15자 내외)로 제한한다. 위험하지 않은 후보를 장황하게 설명하지 않는다. 스키마:
{"risk_items":[{"type":"name_tag|person_name|school_or_org|business_name|address|road_name|building_name|neighborhood_sign|direction_sign|bus_route|bus_stop|banner|schedule|contact_info|other_sign","ocr_ids":["T1"],"bbox":null,"risk_factors":["person_identifier|organization|specific_place|route_or_stop|time_or_schedule|contact_info"],"person_link":"explicit|possible|none","place_link":"explicit|possible|none","time_link":"explicit|possible|none","evidence":"관찰 근거를 짧게","confidence":"high|medium|low"}],"requires_review":false}
빈 목록은 안전 판정이 아니다. 목표 단서가 보이지 않거나 일부가 가려져 판정이 어려우면 빈 목록과 `requires_review=true`를 반환한다.'''

OCR_FIRST_PROMPT = _POLICY + '''

처리 순서: OCR이 먼저 만든 후보 목록을 사진과 대조한다.
- 사진을 기준으로 OCR 오인식/누락을 확인한다. OCR 문자열을 사실로 맹신하지 않는다.
- 위험 근거가 있는 OCR 줄만 `ocr_ids`에 넣는다. 일반 문구는 제외한다.
- OCR에 없지만 실제로 보이는 이름표, 버스 정류장/번호, 방향표지, 현수막 글자는 작은 bbox로 추가한다.
- 반환 전 화면의 모든 영역을 훑어 작은 텍스트 단서가 누락되지 않았는지 확인한다.

OCR 후보 (ID | 신뢰도 | 인식 문자열):
{ocr_candidates}
'''

VLM_FIRST_PROMPT = _POLICY + '''

처리 순서: OCR을 보기 전에 사진만으로 후보를 찾는다.
- 텍스트가 있을 가능성이 큰 이름표, 표지, 간판, 현수막, 정류장/노선판을 찾아 글자가 있는 부분만 bbox로 제시한다.
- 읽을 수 있는 글자는 눈에 보이는 범위에서만 짧게 `evidence`에 기술하고, 불확실한 글자는 추측하지 않는다.
- 후보를 생성할 때 특정 인물/장소/일정과 연결되는 근거 종류를 `risk_factors`와 링크 필드로 분리한다.
- 건물 전체나 큰 판 전체를 반환하지 않는다. 후보 객체가 커도 읽을 수 있는 글자 줄마다 좁은 bbox를 낸다.
- 반환 후 OCR이 이 bbox만 원본에서 잘라 확인할 예정이므로, 문자가 있을 법한 유력 영역을 낮은 신뢰도라도 검수 후보로 남긴다.
OCR 후보는 아직 제공되지 않았다.
'''

VISUAL_CANDIDATE_PROMPT = '''사진에서 개인정보 또는 장소 특정 단서가 적힌 글자 표면 후보만 찾는다.
사람/얼굴/건물 전체는 제외한다. 이름표, 간판의 글자 줄, 현수막 문구, 이정표, 버스 노선·정류장 표기, 일정표를 후보로 낸다.
각 후보는 작은 글자 영역 bbox로 반환한다. 읽을 수 없는 글자도 글자 표면이 분명하면 후보로 남기되 문구를 추측하지 않는다.
JSON만 반환: {"risk_items":[{"type":"name_tag|person_name|school_or_org|business_name|address|road_name|building_name|neighborhood_sign|direction_sign|bus_route|bus_stop|banner|schedule|contact_info|other_sign","bbox":[xmin,ymin,xmax,ymax],"confidence":"high|medium|low"}],"requires_review":false}
bbox는 이 입력 이미지 기준 0..1000 정규화이며 글자 줄만 촘촘히 둘러싸고 전체 이미지의 3%를 넘지 않게 한다. 이 단계 상자는 OCR polygon 연결에만 사용하며, 최종 마스킹은 인식된 OCR polygon을 우선한다. 누락이 의심되면 requires_review=true.
'''

VLM_RISK_REVIEW_PROMPT = _POLICY + '''

이 단계에서는 앞 단계 VLM이 찾은 후보만 OCR 결과와 사진에 대조해 위험 단서를 평가한다.
- 후보 목록과 OCR 문자열을 함께 확인해 식별 가능한 인물·장소·기관·노선·연락처·일정 단서를 구분한다.
- OCR 문자열만으로 연결을 상상하지 말고 사진에서 해당 글자와 후보가 일치하는지 확인한다.
- 후보가 실제로 위치 특정과 무관한 일반 문구면 제외한다. 흐리거나 서로 맞지 않으면 requires_review=true.
- OCR ID가 맞으면 ocr_ids에 기록하고, 후보 ID도 candidate_ids에 보존한다. 최종 마스킹 좌표는 서버가 OCR 원본 polygon 또는 후보 bbox에 연결한다.
- 위험 단서를 반환할 때는 반드시 입력 후보 목록의 실제 C번호를 candidate_ids에 넣는다. 후보 목록에 없는 C번호를 만들지 말고, 후보 bbox를 식별 근거로 활용한다.
- OCR 텍스트가 해당 후보 안에 있으면 실제로 읽힌 OCR ID를 포함한다. 판 전체/건물 전체가 아니라 연결된 OCR polygon을 반환한다.
- 최종 위험 단계는 결정하지 않고 risk_factors와 관찰 근거만 반환한다.
JSON 스키마: {"risk_items":[{"candidate_ids":["C1"],"type":"name_tag|person_name|school_or_org|business_name|address|road_name|building_name|neighborhood_sign|direction_sign|bus_route|bus_stop|banner|schedule|contact_info|other_sign","ocr_ids":["T1"],"risk_factors":["person_identifier|organization|specific_place|route_or_stop|time_or_schedule|contact_info"],"person_link":"explicit|possible|none","place_link":"explicit|possible|none","time_link":"explicit|possible|none","evidence":"관찰 근거","confidence":"high|medium|low"}],"requires_review":false}

후보 및 OCR 목록:
{candidate_inventory}
'''

# Compatibility alias for code that still imports the original name.
SCENE_PROMPT = OCR_FIRST_PROMPT

CROP_REVIEW_PROMPT = '''잘라낸 이미지에서 실제로 읽히는 글자만 그대로 읽고 OCR 후보를 검증하라. 흐리거나 가려진 글자를 추측하지 마라. JSON만 반환한다: {"texts":[{"text":"보이는 문구","confidence":"high|medium|low"}]}. 읽을 수 없으면 {"texts":[]}를 반환한다.'''
