# 🐳 Recipe App Docker 배포 가이드

> Frontend + Backend 통합 Docker 배포 설정

## 📋 변경사항 요약

### 🆕 새로 추가된 파일
- `docker-compose.yml` - 전체 앱 통합 compose 파일
- `frontend/Dockerfile` - Next.js 프론트엔드용 Docker 설정
- `nginx.conf` - 리버스 프록시 설정 (선택사항)

### 🔄 수정된 파일
- `frontend/next.config.mjs` - standalone 출력 모드 및 API 프록시 설정 추가

## 🏗️ 아키텍처 구조

```
┌─────────────────────────────────────────────────────────────┐
│                     Docker Network                         │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────────────┐ │
│  │   Nginx     │  │   Frontend   │  │      Backend        │ │
│  │ (Port: 80)  │  │ (Port: 3000) │  │   (Port: 8000)     │ │
│  └─────────────┘  └──────────────┘  └─────────────────────┘ │
│                                      │                     │
│  ┌─────────────┐  ┌──────────────┐  │                     │
│  │   MySQL     │  │   Qdrant     │  │                     │
│  │ (Port: 3307)│  │ (Port: 6201) │  │                     │
│  └─────────────┘  └──────────────┘  │                     │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 배포 방법

### 1. 기본 실행 (추천)
전체 스택을 독립적으로 실행:

```bash
# 모든 서비스 실행
docker-compose up -d

# 로그 확인
docker-compose logs -f

# 서비스 상태 확인
docker-compose ps
```

**접속:**
- 프론트엔드: http://localhost:3000
- 백엔드 API: http://localhost:8000
- MySQL: localhost:3307
- Qdrant: http://localhost:6201

### 2. Nginx 통합 실행 (선택사항)
하나의 도메인에서 모든 서비스 접근:

```bash
# Nginx 포함 실행
docker-compose --profile nginx up -d
```

**접속:**
- 통합 앱: http://localhost (프론트엔드 + API 모두)

### 3. 데이터 초기화
처음 실행 시 또는 데이터 리셋이 필요할 때:

```bash
# 데이터 초기화 실행
docker-compose --profile init up init-data

# 초기화 로그 확인
docker-compose --profile init logs init-data
```

## 🔧 개발 vs 운영 환경

### 개발 환경
```bash
# Backend만 실행 (기존 방식)
cd backend
docker-compose up -d

# Frontend 로컬 실행
cd frontend
pnpm dev
```

### 운영 환경
```bash
# 루트에서 전체 앱 실행
docker-compose up -d
```

## 📁 파일별 상세 설명

### 1. `docker-compose.yml` (루트)
- **목적**: 전체 애플리케이션 통합 배포
- **서비스**: frontend, backend, mysql, qdrant, nginx, init-data
- **네트워크**: recipe-network로 서비스 간 통신
- **볼륨**: 데이터 영속성 보장

### 2. `frontend/Dockerfile`
- **베이스 이미지**: node:20-alpine
- **빌드 방식**: Multi-stage build (deps → builder → runner)
- **최적화**: 
  - pnpm 사용으로 빠른 의존성 설치
  - standalone 출력으로 최소 런타임
  - 비root 사용자 (nextjs) 실행

### 3. `frontend/next.config.mjs`
- **추가 설정**:
  - `output: 'standalone'` - Docker 최적화
  - API 프록시 설정 (개발/운영 환경 자동 감지)

### 4. `nginx.conf`
- **역할**: 리버스 프록시 및 로드밸런서
- **라우팅**:
  - `/` → Frontend (Next.js)
  - `/api/` → Backend (FastAPI)
  - `/ws` → WebSocket 지원

## 🛠️ 환경 변수 설정

환경 변수가 필요한 경우 `.env` 파일 생성:

```env
# API Keys
FOOD_SAFETY_API_KEY=your_api_key_here
OPENAI_API_KEY=your_openai_key_here

# Database
MYSQL_ROOT_PASSWORD=1234
MYSQL_DATABASE=cookwise

# Environment
ENV=production
NODE_ENV=production
```

## 🐛 트러블슈팅

### 1. 포트 충돌
```bash
# 사용 중인 포트 확인
netstat -an | findstr "3000\|8000\|3307\|6201"

# 다른 포트로 변경하거나 기존 프로세스 종료
```

### 2. 컨테이너 빌드 실패
```bash
# 캐시 없이 다시 빌드
docker-compose build --no-cache

# 개별 서비스 빌드
docker-compose build frontend
docker-compose build backend
```

### 3. 데이터베이스 연결 오류
```bash
# MySQL 컨테이너 상태 확인
docker-compose logs mysql

# 헬스체크 상태 확인
docker-compose ps
```

### 4. 네트워크 문제
```bash
# 네트워크 정리
docker network prune

# 컨테이너 재시작
docker-compose down && docker-compose up -d
```

## 🔄 유지보수 명령어

### 시작/중지
```bash
# 전체 서비스 시작
docker-compose up -d

# 전체 서비스 중지
docker-compose down

# 볼륨까지 삭제 (데이터 초기화)
docker-compose down -v
```

### 로그 및 모니터링
```bash
# 전체 로그
docker-compose logs -f

# 특정 서비스 로그
docker-compose logs -f frontend
docker-compose logs -f backend

# 실시간 상태 모니터링
watch docker-compose ps
```

### 업데이트
```bash
# 코드 변경 후 다시 빌드
docker-compose build
docker-compose up -d

# 특정 서비스만 재빌드
docker-compose build frontend
docker-compose up -d frontend
```

## 📊 성능 최적화 팁

1. **이미지 크기 최적화**
   - Multi-stage build 활용
   - Alpine Linux 베이스 이미지 사용
   - .dockerignore 파일로 불필요한 파일 제외

2. **메모리 사용량 제한**
   ```yaml
   deploy:
     resources:
       limits:
         memory: 512M
   ```

3. **헬스체크 활용**
   - 서비스 상태 자동 모니터링
   - 의존성 관리로 안정적인 시작 순서

## 🔐 보안 고려사항

1. **환경 변수 보안**
   - `.env` 파일을 git에 커밋하지 않기
   - 민감한 정보는 Docker secrets 사용 고려

2. **네트워크 보안**
   - 내부 네트워크 사용으로 서비스 간 통신 격리
   - 필요한 포트만 외부 노출

3. **컨테이너 보안**
   - 비root 사용자로 실행
   - 최소 권한 원칙 적용

---

**작성일**: 2024년 12월
**버전**: v1.0
**작성자**: jyr 