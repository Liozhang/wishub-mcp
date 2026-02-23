# 贡献指南

感谢你考虑为 wishub-mcp 做出贡献！

## 如何贡献

### 报告 Bug

- 在 GitHub Issues 中搜索,确认问题未被报告
- 创建新的 Issue,详细描述问题
- 提供复现步骤、预期行为和环境信息

### 提出新功能

- 在 GitHub Issues 中讨论你的想法
- 等待维护者确认和反馈
- 如果获得批准,开始实现

### 提交代码

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

## 代码规范

### Python

- 使用 Black 格式化代码
- 使用 Ruff 进行 lint 检查
- 使用 Mypy 进行类型检查
- 编写单元测试
- 遵循 PEP 8 风格指南

```bash
# 格式化代码
black wishub_mcp/ tests/

# Lint 检查
ruff check wishub_mcp/ tests/

# 类型检查
mypy wishub_mcp/

# 运行测试
pytest tests/
```

## Pull Request 检查清单

- [ ] 代码通过所有 CI 检查
- [ ] 添加了必要的测试
- [ ] 更新了相关文档
- [ ] 提交信息清晰明确
- [ ] 没有引入破坏性变更
- [ ] 代码符合项目风格

## 行为准则

- 尊重所有贡献者
- 提供建设性反馈
- 专注于对社区最有利的事情
- 对不同的观点保持开放

## 开发设置

### 环境要求

- Python 3.11+
- pip
- Docker (可选)

### 本地开发

```bash
# 克隆仓库
git clone https://github.com/Liozhang/wishub-mcp.git
cd wishub-mcp

# 创建虚拟环境
python -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 安装开发依赖
pip install -r requirements-dev.txt

# 运行测试
pytest tests/

# 启动开发服务器
python -m wishub_mcp.main
```

### Docker 开发

```bash
# 构建Docker镜像
docker-compose -f docker/docker-compose.yml build

# 启动服务
docker-compose -f docker/docker-compose.yml up -d

# 查看日志
docker-compose -f docker/docker-compose.yml logs -f
```

## 许可证

通过贡献代码,你同意你的贡献将在 MIT 许可证下授权。
