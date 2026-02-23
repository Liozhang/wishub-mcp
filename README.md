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

## 开发

### 运行测试

```bash
pytest tests/
```

### 代码格式化

```bash
black wishub_mcp/ tests/
ruff check wishub_mcp/ tests/
```

## 许可证

MIT License - see [LICENSE](LICENSE) file for details.

## 贡献

欢迎贡献！请查看 [CONTRIBUTING.md](CONTRIBUTING.md)

## 联系我们

- GitHub: https://github.com/Liozhang/wishub-mcp
- Issues: https://github.com/Liozhang/wishub-mcp/issues
