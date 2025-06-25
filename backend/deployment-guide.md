# 레시피 추천 백엔드 애플리케이션 배포 가이드

## 개요
FastAPI 기반의 레시피 추천 백엔드 애플리케이션을 Docker를 사용하여 배포하는 방법을 설명합니다.

## 시스템 아키텍처
- **FastAPI**: 백엔드 API 서버 (포트: 8000)
- **MySQL**: 관계형 데이터베이스 (포트: 3307)
- **QDRANT**: 벡터 데이터베이스 (포트: 6201)
- **Docker & Docker Compose**: 컨테이너 오케스트레이션

## 프로젝트 구조
```
backend/
├── app/                    # FastAPI 애플리케이션
│   ├── main.py            # 메인 애플리케이션
│   ├── db.py              # 데이터베이스 설정
│   ├── models.py          # 데이터 모델
│   ├── schemas.py         # Pydantic 스키마
│   └── routers/           # API 라우터들
├── migrations/            # 데이터베이스 마이그레이션
├── Dockerfile            # 도커 이미지 빌드 설정
├── docker-compose.yml    # 서비스 오케스트레이션
├── init_data.py          # 초기 데이터 설정 스크립트
├── seed_data.py          # 시드 데이터 스크립트
├── recipe_rag_pipeline.py # RAG 파이프라인 스크립트
└── delete_and_recreate.py # 데이터베이스 초기화 스크립트
```

## 배포 절차

### 1. 사전 준비

#### 1.1 시스템 요구사항
- Docker 20.10+
- Docker Compose 2.0+
- 최소 4GB RAM
- 최소 10GB 디스크 공간

#### 1.2 환경 변수 설정
`.env` 파일을 프로젝트 루트에 생성:
```bash
# API 키 설정
FOOD_SAFETY_API_KEY=your_food_safety_api_key_here
FOOD_SAFETY_SERVICE_ID=COOKRCP01
OPENAI_API_KEY=your_openai_api_key_here
```

### 2. 도커 이미지 빌드 및 서비스 시작

#### 2.1 전체 서비스 시작
```bash
# 모든 서비스를 백그라운드에서 시작
docker-compose up -d

# 서비스 상태 확인
docker-compose ps
```

#### 2.2 로그 확인
```bash
# 전체 서비스 로그 확인
docker-compose logs -f

# 특정 서비스 로그 확인
docker-compose logs -f backend
docker-compose logs -f mysql
docker-compose logs -f qdrant
```

### 3. 초기 데이터 설정

#### 3.1 데이터베이스 초기화 및 시드 데이터 삽입
```bash
# 초기 데이터 설정 실행 (한 번만)
docker-compose --profile init up init-data

# 초기화 로그 확인
docker-compose logs init-data
```

#### 3.2 초기화 과정 설명
1. **delete_and_recreate.py**: 기존 테이블 삭제 및 재생성
2. **seed_data.py**: 기본 레시피 데이터 삽입
3. **recipe_rag_pipeline.py**: RAG 벡터 데이터 생성

### 4. 서비스 접속 확인

#### 4.1 API 서비스 확인
- **API 문서**: http://localhost:8000/docs
- **Redoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

#### 4.2 데이터베이스 접속
- **MySQL**: localhost:3307
  - 사용자: root
  - 비밀번호: 1234
  - 데이터베이스: cookwise

- **QDRANT**: http://localhost:6201

### 5. 서비스 관리

#### 5.1 서비스 중지
```bash
# 모든 서비스 중지
docker-compose down

# 볼륨까지 삭제 (데이터 완전 삭제)
docker-compose down -v
```

#### 5.2 서비스 재시작
```bash
# 특정 서비스 재시작
docker-compose restart backend

# 전체 서비스 재시작
docker-compose restart
```

#### 5.3 이미지 재빌드
```bash
# 이미지 재빌드 후 시작
docker-compose up -d --build

# 캐시 없이 재빌드
docker-compose build --no-cache
```

## 🔧 운영 환경 배포

### 1. 프로덕션 환경 설정

#### 1.1 docker-compose.prod.yml 생성
```yaml
version: '3.8'

services:
  mysql:
    image: mysql:8.0
    container_name: recipe-mysql-prod
    environment:
      MYSQL_ROOT_PASSWORD: ${MYSQL_ROOT_PASSWORD}
      MYSQL_DATABASE: cookwise
    ports:
      - "3306:3306"
    volumes:
      - mysql_prod_data:/var/lib/mysql
    command: --default-authentication-plugin=mysql_native_password
    restart: unless-stopped

  qdrant:
    image: qdrant/qdrant:latest
    container_name: recipe-qdrant-prod
    ports:
      - "6333:6333"
    volumes:
      - qdrant_prod_data:/qdrant/storage
    restart: unless-stopped

  backend:
    build: .
    container_name: recipe-backend-prod
    ports:
      - "80:8000"
    environment:
      - DATABASE_URL=mysql+pymysql://root:${MYSQL_ROOT_PASSWORD}@mysql:3306/cookwise
      - QDRANT_URL=http://qdrant:6333
      - ENV=production
      - FOOD_SAFETY_API_KEY=${FOOD_SAFETY_API_KEY}
      - FOOD_SAFETY_SERVICE_ID=${FOOD_SAFETY_SERVICE_ID}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    depends_on:
      - mysql
      - qdrant
    volumes:
      - ./hf_cache:/app/hf_cache
    restart: unless-stopped

volumes:
  mysql_prod_data:
  qdrant_prod_data:
```

#### 1.2 프로덕션 환경 변수 설정
```bash
# .env.prod 파일 생성
MYSQL_ROOT_PASSWORD=secure_password_here
FOOD_SAFETY_API_KEY=your_production_api_key
FOOD_SAFETY_SERVICE_ID=COOKRCP01
OPENAI_API_KEY=your_production_openai_key
```

#### 1.3 프로덕션 배포
```bash
# 프로덕션 환경으로 배포
docker-compose -f docker-compose.prod.yml --env-file .env.prod up -d

# 초기 데이터 설정 (최초 배포시에만)
docker-compose -f docker-compose.prod.yml --env-file .env.prod --profile init up init-data
```

### 2. 보안 설정

#### 2.1 방화벽 설정
```bash
# UFW 방화벽 설정 (Ubuntu)
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 22/tcp
sudo ufw enable
```

#### 2.2 SSL 인증서 설정 (선택사항)
Nginx 리버스 프록시와 Let's Encrypt를 사용한 HTTPS 설정

## 🔍 모니터링 및 로깅

### 1. 로그 관리
```bash
# 로그 파일 크기 제한 설정
docker-compose.yml에 logging 옵션 추가:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

### 2. 헬스체크
```bash
# 서비스 상태 확인
curl http://localhost:8000/health

# 데이터베이스 연결 확인
docker-compose exec mysql mysqladmin ping -h localhost -u root -p1234
```

## 문제 해결

### 1. 일반적인 문제

#### 1.1 포트 충돌
```bash
# 포트 사용 중인 프로세스 확인
netstat -tulpn | grep :8000
lsof -i :8000

# 프로세스 종료
kill -9 <PID>
```

#### 1.2 MySQL 연결 실패
```bash
# MySQL 컨테이너 로그 확인
docker-compose logs mysql

# MySQL 컨테이너 직접 접속
docker-compose exec mysql mysql -u root -p1234 cookwise
```

#### 1.3 QDRANT 연결 실패
```bash
# QDRANT 상태 확인
curl http://localhost:6201/collections

# QDRANT 컨테이너 재시작
docker-compose restart qdrant
```

### 2. 데이터 백업 및 복구

#### 2.1 MySQL 백업
```bash
# 데이터베이스 백업
docker-compose exec mysql mysqldump -u root -p1234 cookwise > backup.sql

# 데이터베이스 복구
docker-compose exec -T mysql mysql -u root -p1234 cookwise < backup.sql
```

#### 2.2 QDRANT 백업
```bash
# QDRANT 데이터 백업
docker-compose exec qdrant tar -czf /tmp/qdrant_backup.tar.gz /qdrant/storage
docker cp recipe-qdrant:/tmp/qdrant_backup.tar.gz ./qdrant_backup.tar.gz
```

## 📊 성능 최적화

### 1. 리소스 제한 설정
```yaml
# docker-compose.yml에 리소스 제한 추가
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 1G
```

### 2. 캐싱 설정
- Redis 캐시 서버 추가 고려
- 애플리케이션 레벨 캐싱 구현

## 📝 배포 체크리스트

### 배포 전 확인사항
- [ ] 환경 변수 설정 완료
- [ ] API 키 유효성 확인
- [ ] Docker 및 Docker Compose 설치 확인
- [ ] 필요한 포트 사용 가능 확인
- [ ] 충분한 디스크 공간 확인

### 배포 후 확인사항
- [ ] 모든 서비스 정상 실행 확인
- [ ] API 엔드포인트 접속 확인
- [ ] 데이터베이스 연결 확인
- [ ] 초기 데이터 로드 완료 확인
- [ ] 로그 에러 없음 확인

## 🆘 지원 및 문의

배포 과정에서 문제가 발생하면 다음을 확인해주세요:
1. 로그 파일 확인: `docker-compose logs -f`
2. 서비스 상태 확인: `docker-compose ps`
3. 시스템 리소스 확인: `docker stats`

---

**마지막 업데이트**: 2024년 12월
**버전**: 1.0.0 