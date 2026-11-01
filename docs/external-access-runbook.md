# 외부 접속 연결 작업안

## 이번 시범 공개에 권장하는 구성

NCP VPC의 **Public Application Load Balancer**에 HTTPS 443 리스너를 만들고, CPU 서버의 기존 웹/API 포트 `8000`으로 전달한다. 프론트와 `/api`가 같은 origin을 사용하므로 경로 재작성이나 프론트 별도 공개 서버는 필요하지 않다. GPU 서버는 계속 사설망에만 둔다.

이 방식은 외부 접속을 빠르게 여는 reverse proxy 구조다. ZIP·사진·분석 요청은 ALB를 통과한다. 기존에 요청한 “중계 서버는 연결 설정만 하고 데이터는 브라우저와 서버가 직접 송수신”하는 구조는 WebRTC DataChannel, 별도 신호 교환 서비스, ICE/STUN 및 NAT 예외용 TURN 구성이 필요하므로 별도 2단계로 둔다. 현재 HTTP API를 WebRTC 전송으로 바꾸는 코드는 아직 구현되지 않았다.

## NCP 콘솔 설정

1. Networking > Load Balancer에서 VPC **Public Application Load Balancer**를 생성한다. 같은 VPC의 전용 Load Balancer 서브넷을 사용한다.
2. 리스너 `HTTPS:443`, 서버 프로토콜 `HTTP`, 대상 `CPU 서버 사설 IP:8000`인 Target Group을 만든다. 헬스 체크는 `GET /health`로 둔다.
3. 도메인이 있으면 DNS에서 소유권을 확인하고 NCP Certificate Manager의 도메인 검증 인증서를 등록한 뒤 ALB 443에 연결한다. DNS 업체에 ALB가 제공한 주소를 연결한다.
4. ALB의 ACG에는 인터넷에서 `TCP 443`만 허용한다. HTTP 리다이렉트가 필요하면 `TCP 80`도 추가한다.
5. CPU ACG에는 ALB의 Access Control Group을 소스로 `TCP 8000`만 허용한다. `0.0.0.0/0`에서 CPU 8000으로 직접 들어오는 규칙은 만들지 않는다.
6. GPU ACG는 CPU ACG에서 `TCP 8080`만 허용한다. GPU API 포트는 인터넷에 열지 않는다.
7. 작은 비공개 테스트면 ALB Listener ACL에 테스트 담당자의 공인 IP를 제한한다. 외부 테스트 계정이 늘어나면 인증과 요청 제한을 먼저 추가한다.

NCP 문서상 VPC Public ALB는 인터넷에서 요청을 받을 수 있고 고객 도메인 또는 ALB가 제공하는 도메인으로 사용할 수 있다. HTTPS 리스너는 Certificate Manager 인증서가 필요하다. ALB 대상 포트는 Target Group에서 설정하고, CPU ACG는 Load Balancer의 접근 소스를 허용해야 한다.

## CPU 서버 환경

CPU 서버의 `.env`에 아래 값을 설정한다. 비밀값은 서버에서 직접 생성·입력하며 채팅이나 Git에 올리지 않는다.

```dotenv
GPU_MOCK=false
GPU_URL=http://10.1.2.30:8080
SESSION_SECRET=<서버에서 생성한 32자 이상의 임의 비밀값>
SESSION_COOKIE_SECURE=true
API_HOST=0.0.0.0
API_PORT=8000
```

GPU 서버 `.env`의 `GPU_API_KEY`는 CPU 서버 값과 일치시킨다. 모델 API는 GPU 서버 내부에만 바인딩/방화벽 허용한다. 배포 전 `/api/status`가 `gpu_mock=false`, `gpu_ok=true`인지 확인한다.

## 적용 전 확인할 조건

- 현재 작업 환경에서 `10.1.1.30:8000`과 `10.1.2.30:8080`에 연결할 수 없어 서버 설정/상태를 원격 확인하거나 바꾸지 못했다.
- NCP 콘솔에서는 같은 VPC에 Public Load Balancer 전용 서브넷이 이미 있는지 확인해야 한다. 없다면 생성이 필요하다.
- 도메인을 쓰려면 도메인 관리 권한으로 DNS 레코드를 추가하고 인증서 DNS 검증을 완료해야 한다.
- 현재 앱에는 사용자 계정 인증이 없고 브라우저 세션 쿠키로 작업 소유권을 구분한다. 일반 공개 전에는 로그인/접근 통제, 업로드 속도 제한, 사용량 제한을 넣는다. 소수 인원 시범 테스트는 Listener ACL로 IP를 제한한다.

## 사용자 작업

1. 사용할 도메인/서브도메인과 시범 공개 대상(IP 제한 또는 인증 사용자)을 정한다.
2. NCP 콘솔에서 위 ALB와 Listener ACL을 준비한다. 도메인을 사용하면 DNS에 접근할 수 있어야 한다.
3. ALB가 만들어지면 ALB 이름, 대상 그룹 이름, 제공 주소와 도메인 준비 여부를 알려준다. 비밀번호·API 키·인증서 개인 키는 전달하지 않는다.
4. VPN이 켜져 있고 CPU/GPU SSH 터미널이 로그인되어 있는 상태에서 알려주면, 서버 앱 설정·헬스체크와 외부 브라우저 연결을 확인한다.

## 공식 문서

- [NCP Application Load Balancer 생성 및 관리](https://guide.ncloud-docs.com/docs/loadbalancer-application-vpc)
- [NCP Load Balancer Target Group](https://guide.ncloud-docs.com/docs/loadbalancer-targetgroup-vpc)
- [NCP ACG 설정](https://guide.ncloud-docs.com/docs/server-acg-vpc)
- [NCP Certificate Manager 인증서 정보](https://guide.ncloud-docs.com/docs/certificatemanager-cmissuedcertificate-feature)
