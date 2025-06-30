# 기술적 의사결정 문서

## FastAPI 기반 Python을 선택한 이유

본 프로젝트에서는 AI 추론과 벡터 검색 중심의 RAG 파이프라인을 빠르게 구축하고, 유연한 확장성과 생산성을 확보하기 위해 Python 기반 FastAPI 프레임워크를 채택하였습니다.

### AI 라이브러리 연동 용이성
Python은 OpenAI, KoSimCSE, HuggingFace Transformers 등 다양한 AI 라이브러리와의 호환성이 뛰어나 RAG 파이프라인 구성에 최적화되어 있습니다.

### 빠른 프로토타이핑 및 테스트
FastAPI의 간결한 문법과 자동 문서화(Swagger/OpenAPI)를 활용해, 짧은 시간 안에 API를 설계하고 배포할 수 있어 초기 개발 및 반복 테스트에 유리합니다.

### 비동기 기반 성능 최적화
OpenAI API 호출처럼 응답 시간이 긴 AI 작업을 async/await 기반으로 처리하여, 서버 전체의 응답성 및 동시 처리 성능을 개선했습니다.

### 라우터 모듈화를 통한 구조적 개발
FastAPI의 APIRouter 기반 모듈화를 통해 기능 단위로 API를 나누고, 트랜잭션이 무거운 서비스는 다른 언어(Java 등)로 확장 가능한 마이크로서비스 구조로 설계했습니다.

## 기타 기술 선택 배경

### 벡터 데이터베이스: Qdrant
- 한국어 의미론적 검색에 최적화
- Docker 기반 쉬운 배포
- REST API를 통한 간편한 연동

### 임베딩 모델: KoSimCSE-bert
- 한국어 문장 임베딩에 특화
- 레시피 도메인에서 높은 유사도 정확성
- HuggingFace 모델 허브를 통한 쉬운 사용

### 프론트엔드: Next.js 14
- SSR/SSG를 통한 SEO 최적화
- TypeScript 지원으로 타입 안전성 확보
- React 생태계의 풍부한 라이브러리 활용 