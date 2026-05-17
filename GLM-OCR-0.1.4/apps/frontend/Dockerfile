# 使用 Node.js 官方镜像作为基础镜像
FROM node:lts-alpine as build-stage

# 设置工作目录
WORKDIR /app

# 将 package.json 和 pnpm-lock.json 添加到工作目录
COPY package.json pnpm-lock.yaml ./

# 启用 corepack 并安装兼容的 pnpm 版本（lockfileVersion 6.0 需要 pnpm 8.x）
RUN corepack enable && corepack prepare pnpm@8 --activate
# 安装项目依赖
RUN pnpm install

# 将项目文件添加到工作目录
COPY . .

# 构建项目并清理缓存
RUN pnpm build && \
    pnpm store prune && \
    rm -rf node_modules

# 使用 Nginx 镜像作为基础镜像
FROM nginx:stable-alpine as production-stage

# 将构建产物复制到 Nginx 服务器的服务目录
COPY --from=build-stage /app/dist /usr/share/nginx/html

# 复制 Nginx 配置
COPY nginx.conf /etc/nginx/conf.d/default.conf

# 添加健康检查（检查 index.html 文件是否存在）
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD test -f /usr/share/nginx/html/index.html || exit 1

# 暴露 80 端口
EXPOSE 80

# 启动 Nginx 服务器
CMD ["nginx", "-g", "daemon off;"]
