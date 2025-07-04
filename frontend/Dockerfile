# Node.js 20 Alpine 이미지 사용
FROM node:20-alpine AS base

# 의존성 설치 단계
FROM base AS deps
RUN apk add --no-cache libc6-compat
WORKDIR /app

# 패키지 파일들 복사
COPY package.json pnpm-lock.yaml* ./
RUN npm install -g pnpm
RUN pnpm install --no-frozen-lockfile

# 빌드 단계
FROM base AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .

# Next.js 빌드
RUN npm install -g pnpm
RUN pnpm build

# 실행 단계
FROM base AS runner
WORKDIR /app

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

# 빌드된 앱 복사
COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs

EXPOSE 3000

ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

CMD ["node", "server.js"] 