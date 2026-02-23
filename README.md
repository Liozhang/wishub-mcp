# wishub-mcp

WisHub MCP (Model Context Protocol) Server - AI 模型通过 MCP 协议获取 WisHub 知识上下文

[![CI](https://github.com/Liozhang/wishub-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/Liozhang/wishub-mcp/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)

## 功能特性

- ✅ MCP 调用协议实现
- ✅ 支持多种 AI 模型 (OpenAI GPT-4, 智谱 GLM-4)
- ✅ WisHub 核心集成
- ✅ API Key 认证
- ✅ OpenAPI 文档自动生成
- ✅ Redis 缓存支持

## 快速开始

### 使用 Docker

```bash
# 克隆仓库
git clone https://github.com/Liozhang/wishub-mcp.git
cd wishub-mcp

# 启动服务
docker-compose up -d

# 访问 API 文档
open http://localhost:8000/docs
```

### 使用 pip

```bash
# 安装依赖
pip install -r requirements.txt

# 设置环境变量
cp .env.example .env
# 编辑 .env 文件，配置 API Key

# 启动服务
python -m wishub_mcp.main
```

## API 使用示例

### MCP 调用

```bash
curl -X POST http://localhost:8000/api/v1/mcp/invoke \
  -H "X-API-Key: your_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "context_id": "ctx_20250223_001",
    "model_id": "gpt-4",
    "prompt": "糖尿病的正常血糖范围是多少？",
    "max_tokens": 500,
    "temperature": 0.5
  }'
```

## 本地开发

### 快速启动

使用提供的本地启动脚本，快速设置开发环境：

```bash
# 首次使用：设置开发环境
./scripts/local.sh setup

# 启动开发服务器
./scripts/local.sh start

# 访问 API 文档
open http://localhost:8000/docs
```

### 手动安装

如果需要手动设置开发环境：

```bash
# 创建虚拟环境
python3 -m venv .venv
source .venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 设置环境变量
cp .env.example .env
# 编辑 .env 文件，配置您的 API Key

# 启动开发服务器
uvicorn wishub_mcp.server.app:app --host 0.0.0.0 --port 8000 --reload
```

### 开发命令

```bash
# 运行测试
./scripts/local.sh test

# 安装依赖
./scripts/local.sh install

# 安装开发依赖
./scripts/local.sh install-dev

# 清理虚拟环境
./scripts/local.sh clean
```

### 运行测试

```bash
# 使用本地脚本
./scripts/local.sh test

# 或使用 pytest
pytest tests/ -v

# 带覆盖率
pytest tests/ --cov=wishub_mcp --cov-report=html
```

### 代码格式化

```bash
# 使用本地脚本
./scripts/local.sh format

# 或手动运行
black wishub_mcp/ tests/
ruff check --fix wishub_mcp/ tests/
```

### 环境变量配置

复制 `.env.example` 到 `.env` 并配置：

```env
# API 配置
APP_NAME=wishub-mcp
APP_ENV=development
API_HOST=0.0.0.0
API_PORT=8000
API_PREFIX=/api/v1

# 认证配置
AUTH_REQUIRED=false
AUTH_HEADER=X-API-Key

# Redis 配置
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# WisHub 核心配置
WISHUB_CORE_URL=http://localhost:9000

# AI 模型配置
OPENAI_API_KEY=your_openai_api_key
ZHIPU_API_KEY=your_zhipu_api_key

# 智谱 API 端点（可选）
# 默认使用智谱的 coding API 端点（与 clawd 配置一致）
# 如果需要使用其他端点，可以修改此配置
ZHIPU_BASE_URL=https://open.bigmodel.cn/api/coding/paas/v4

# 日志配置
LOG_LEVEL=DEBUG
```

## 许可证

MIT License - see [LICENSE](LICENSE) file for details.

## 贡献

欢迎贡献！请查看 [CONTRIBUTING.md](CONTRIBUTING.md)

## 联系我们

- GitHub: https://github.com/Liozhang/wishub-mcp
- Issues: https://github.com/Liozhang/wishub-mcp/issues
