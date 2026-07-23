FROM node:24-alpine

WORKDIR /workspace
RUN corepack enable

COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
COPY apps/web/package.json apps/web/package.json
COPY apps/admin/package.json apps/admin/package.json
COPY packages/ui/package.json packages/ui/package.json
COPY packages/iica-engine/package.json packages/iica-engine/package.json
RUN pnpm install --frozen-lockfile --ignore-scripts

COPY . .
EXPOSE 3001
CMD ["pnpm", "--filter", "@iica/admin", "dev", "--hostname", "0.0.0.0"]
