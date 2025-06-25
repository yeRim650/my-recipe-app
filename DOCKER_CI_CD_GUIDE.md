# Docker Hub & GitHub Actions CI/CD 가이드

> 자동화된 Docker 이미지 빌드 및 배포 가이드

## 🚀 설정 과정

### 1. Docker Hub 계정 설정

1. **Docker Hub 계정 생성**
   - https://hub.docker.com 에서 계정 생성

2. **Access Token 생성**
   - Docker Hub → Account Settings → Security → New Access Token
   - Token Name: `github-actions`
   - Permissions: `Read, Write, Delete`
   - **토큰을 안전한 곳에 저장!**

### 2. GitHub Secrets 설정

GitHub 리포지토리에서 다음 Secrets를 설정하세요:

```
Repository → Settings → Secrets and variables → Actions → New repository secret
```

**필요한 Secrets:**
- `DOCKER_HUB_USERNAME`: Docker Hub 사용자명
- `DOCKER_HUB_ACCESS_TOKEN`: 위에서 생성한 Access Token

### 3. 워크플로우 실행

#### 자동 실행 (권장)
- `main`, `develop`, `feat/docker-deployment` 브랜치에 push
- Pull Request 생성

#### 수동 실행
- GitHub → Actions → "Build and Push Docker Images" → Run workflow

## 📦 생성되는 이미지

### Frontend
```
docker.io/[USERNAME]/my-recipe-app-frontend:latest
docker.io/[USERNAME]/my-recipe-app-frontend:[branch-name]
```

### Backend
```
docker.io/[USERNAME]/my-recipe-app-backend:latest  
docker.io/[USERNAME]/my-recipe-app-backend:[branch-name]
```

## 🌐 프로덕션 배포

### 환경변수 파일 생성 (.env.prod)
```env
# Docker Hub
DOCKER_HUB_USERNAME=your_username

# Database
MYSQL_ROOT_PASSWORD=secure_password
MYSQL_DATABASE=cookwise

# API Keys
FOOD_SAFETY_API_KEY=your_api_key
FOOD_SAFETY_SERVICE_ID=COOKRCP01
OPENAI_API_KEY=your_openai_key
```

### 프로덕션 배포 실행
```bash
# Docker Hub 이미지 사용
docker-compose -f docker-compose.prod.yml --env-file .env.prod up -d

# 로그 확인
docker-compose -f docker-compose.prod.yml logs -f

# 상태 확인
docker-compose -f docker-compose.prod.yml ps
```

## 🔄 워크플로우 동작 방식

### 변경 감지
- `frontend/` 폴더 변경 시 → Frontend 이미지만 빌드
- `backend/` 폴더 변경 시 → Backend 이미지만 빌드
- `docker-compose.yml` 변경 시 → 모든 이미지 빌드

### 태그 전략
- `main` 브랜치 → `latest` 태그
- Feature 브랜치 → `브랜치명` 태그
- Pull Request → `pr-번호` 태그
- Git 태그 → 버전 태그 (`v1.0.0`)

### 멀티플랫폼 지원
- `linux/amd64` (Intel/AMD)
- `linux/arm64` (Apple Silicon, ARM 서버)

## 🐛 트러블슈팅

### 1. Secrets 오류
```
Error: Username and password required
```
**해결:** GitHub Secrets 확인 및 재설정

### 2. 빌드 실패
```
ERROR: failed to solve: process "/bin/sh -c ..." did not complete successfully
```
**해결:** Dockerfile 문법 및 종속성 확인

### 3. 권한 오류
```
denied: requested access to the resource is denied
```
**해결:** Docker Hub 토큰 권한 확인

### 4. 캐시 문제
**해결:** Actions에서 캐시 클리어
```bash
# GitHub Actions에서 캐시 삭제 후 재실행
```

## 🔍 로그 확인

### GitHub Actions 로그
- GitHub → Actions → 해당 워크플로우 클릭

### Docker Hub 확인
- https://hub.docker.com/r/[USERNAME]/my-recipe-app-frontend
- https://hub.docker.com/r/[USERNAME]/my-recipe-app-backend

## 📈 고급 기능

### 환경별 설정
```yaml
# .env.staging
DOCKER_HUB_USERNAME=myuser
MYSQL_ROOT_PASSWORD=staging_pass

# .env.production  
DOCKER_HUB_USERNAME=myuser
MYSQL_ROOT_PASSWORD=production_pass
```

### 배포 스크립트
```bash
#!/bin/bash
# deploy.sh

ENV=${1:-production}

echo "🚀 Deploying to $ENV environment..."

docker-compose -f docker-compose.prod.yml --env-file .env.$ENV down
docker-compose -f docker-compose.prod.yml --env-file .env.$ENV pull
docker-compose -f docker-compose.prod.yml --env-file .env.$ENV up -d

echo "✅ Deployment completed!"
```

---

**작성일**: 2024년 12월  
**버전**: v1.0  
**작성자**: CI/CD 자동화 가이드 