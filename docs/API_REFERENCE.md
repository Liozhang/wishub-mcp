# WisHub MCP API 参考文档

## 概述

WisHub MCP (Model Context Protocol) API 提供了基于知识上下文的 AI 模型调用接口。

### 基础信息

- **Base URL**: `http://localhost:8000`
- **API Version**: `v1`
- **Authentication**: API Key (Header: `X-API-Key`)
- **Content-Type**: `application/json`

### 全局响应格式

所有 API 响应遵循统一的格式：

```json
{
  "status": "success|error",
  "message": "操作结果描述",
  "data": {},
  "error": {
    "code": "错误代码",
    "details": "错误详情"
  }
}
```

---

## 认证

### API Key 认证

大多数端点需要 API Key 认证。在请求头中添加：

```http
X-API-Key: your_api_key_here
```

### 认证状态

可以通过环境变量 `AUTH_REQUIRED` 控制是否启用认证：
- `true`: 启用认证（生产环境）
- `false`: 禁用认证（开发环境）

---

## 端点列表

### 1. 健康检查

#### GET `/api/v1/health`

检查服务健康状态。

**请求示例**

```bash
curl -X GET http://localhost:8000/api/v1/health
```

**响应示例**

```json
{
  "status": "success",
  "service": "wishub-mcp",
  "version": "1.0.0",
  "timestamp": "2025-02-23T12:00:00Z"
}
```

---

### 2. MCP 调用

#### POST `/api/v1/mcp/invoke`

使用指定的 AI 模型基于知识上下文回答问题。

**请求头**

```http
Content-Type: application/json
X-API-Key: your_api_key
```

**请求参数**

| 参数 | 类型 | 必填 | 描述 | 默认值 |
|------|------|------|------|--------|
| context_id | string | 是 | 上下文 ID | - |
| context_type | string | 否 | 上下文类型 (wis_unit/default) | default |
| model_id | string | 是 | AI 模型 ID (gpt-4, gpt-3.5-turbo, glm-4) | - |
| prompt | string | 是 | 用户提示 | - |
| max_tokens | integer | 是 | 最大 Token 数量 | - |
| temperature | number | 否 | 温度参数 (0.0-2.0) | 0.7 |
| stream | boolean | 否 | 是否流式响应 | false |

**请求示例**

```bash
curl -X POST http://localhost:8000/api/v1/mcp/invoke \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your_api_key" \
  -d '{
    "context_id": "ctx_20250223_001",
    "context_type": "wis_unit",
    "model_id": "gpt-4",
    "prompt": "糖尿病的正常血糖范围是多少？",
    "max_tokens": 500,
    "temperature": 0.5
  }'
```

**成功响应示例**

```json
{
  "status": "success",
  "context": {
    "id": "ctx_20250223_001",
    "type": "wis_unit",
    "data": {
      "knowledge": "糖尿病相关知识..."
    }
  },
  "response": "根据医学标准，正常人的空腹血糖值为...",
  "tokens_used": 256
}
```

**错误响应示例**

```json
{
  "status": "error",
  "message": "不支持的模型: gpt-5",
  "error": {
    "code": "MCP_002",
    "details": "Model gpt-5 is not supported"
  }
}
```

**错误代码**

| 代码 | 描述 | HTTP 状态码 |
|------|------|-------------|
| MCP_001 | 获取上下文失败 | 500 |
| MCP_002 | 不支持的模型 | 400 |
| MCP_003 | 输入 Token 超限 | 400 |
| MCP_999 | 内部服务器错误 | 500 |

---

### 3. 列出模型

#### GET `/api/v1/mcp/models`

获取所有支持的 AI 模型列表。

**请求示例**

```bash
curl -X GET http://localhost:8000/api/v1/mcp/models
```

**响应示例**

```json
{
  "status": "success",
  "models": [
    {
      "id": "gpt-4",
      "name": "GPT-4",
      "provider": "openai",
      "max_tokens": 8192,
      "supports_streaming": true
    },
    {
      "id": "gpt-3.5-turbo",
      "name": "GPT-3.5 Turbo",
      "provider": "openai",
      "max_tokens": 4096,
      "supports_streaming": true
    },
    {
      "id": "glm-4",
      "name": "GLM-4",
      "provider": "zhipu",
      "max_tokens": 8192,
      "supports_streaming": false
    }
  ],
  "count": 3
}
```

---

### 4. 获取 Token 统计

#### GET `/api/v1/mcp/tokens/{context_id}`

获取指定上下文的 Token 使用统计。

**路径参数**

| 参数 | 类型 | 描述 |
|------|------|------|
| context_id | string | 上下文 ID |

**请求示例**

```bash
curl -X GET http://localhost:8000/api/v1/mcp/tokens/ctx_20250223_001
```

**响应示例**

```json
{
  "status": "success",
  "context_id": "ctx_20250223_001",
  "total_tokens": 15234,
  "prompt_tokens": 8432,
  "completion_tokens": 6802,
  "requests": 23
}
```

---

## 完整请求示例

### Python 示例

```python
import requests
import json

# 配置
BASE_URL = "http://localhost:8000/api/v1"
API_KEY = "your_api_key"

# 创建会话
session = requests.Session()
session.headers.update({
    "Content-Type": "application/json",
    "X-API-Key": API_KEY
})

# MCP 调用
response = session.post(
    f"{BASE_URL}/mcp/invoke",
    json={
        "context_id": "ctx_001",
        "model_id": "gpt-4",
        "prompt": "解释什么是机器学习",
        "max_tokens": 500,
        "temperature": 0.7
    }
)

if response.status_code == 200:
    result = response.json()
    if result["status"] == "success":
        print(f"回答: {result['response']}")
        print(f"使用 Token: {result['tokens_used']}")
    else:
        print(f"错误: {result['message']}")
else:
    print(f"请求失败: {response.status_code}")
```

### Go 示例

```go
package main

import (
    "bytes"
    "encoding/json"
    "fmt"
    "net/http"
)

type MCPRequest struct {
    ContextID   string  `json:"context_id"`
    ModelID     string  `json:"model_id"`
    Prompt      string  `json:"prompt"`
    MaxTokens   int     `json:"max_tokens"`
    Temperature float64 `json:"temperature"`
}

type MCPResponse struct {
    Status     string `json:"status"`
    Response   string `json:"response,omitempty"`
    TokensUsed int    `json:"tokens_used,omitempty"`
    Message    string `json:"message,omitempty"`
}

func main() {
    baseURL := "http://localhost:8000/api/v1"
    apiKey := "your_api_key"

    reqBody := MCPRequest{
        ContextID:   "ctx_001",
        ModelID:     "gpt-4",
        Prompt:      "解释什么是机器学习",
        MaxTokens:   500,
        Temperature: 0.7,
    }

    jsonData, _ := json.Marshal(reqBody)
    req, _ := http.NewRequest("POST", baseURL+"/mcp/invoke", bytes.NewBuffer(jsonData))
    req.Header.Set("Content-Type", "application/json")
    req.Header.Set("X-API-Key", apiKey)

    client := &http.Client{}
    resp, err := client.Do(req)
    if err != nil {
        fmt.Printf("请求失败: %v\n", err)
        return
    }
    defer resp.Body.Close()

    var result MCPResponse
    json.NewDecoder(resp.Body).Decode(&result)

    if result.Status == "success" {
        fmt.Printf("回答: %s\n", result.Response)
        fmt.Printf("使用 Token: %d\n", result.TokensUsed)
    } else {
        fmt.Printf("错误: %s\n", result.Message)
    }
}
```

### TypeScript 示例

```typescript
interface MCPRequest {
    context_id: string;
    model_id: string;
    prompt: string;
    max_tokens: number;
    temperature?: number;
}

interface MCPResponse {
    status: string;
    response?: string;
    tokens_used?: number;
    message?: string;
}

const BASE_URL = "http://localhost:8000/api/v1";
const API_KEY = "your_api_key";

async function invokeMCP(request: MCPRequest): Promise<MCPResponse> {
    const response = await fetch(`${BASE_URL}/mcp/invoke`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-API-Key": API_KEY,
        },
        body: JSON.stringify(request),
    });

    return await response.json();
}

// 使用示例
async function main() {
    const result = await invokeMCP({
        context_id: "ctx_001",
        model_id: "gpt-4",
        prompt: "解释什么是机器学习",
        max_tokens: 500,
        temperature: 0.7,
    });

    if (result.status === "success") {
        console.log(`回答: ${result.response}`);
        console.log(`使用 Token: ${result.tokens_used}`);
    } else {
        console.log(`错误: ${result.message}`);
    }
}

main().catch(console.error);
```

---

## 错误处理

### 标准错误格式

```json
{
  "status": "error",
  "message": "错误描述",
  "error": {
    "code": "ERROR_CODE",
    "details": "详细信息"
  }
}
```

### HTTP 状态码

| 状态码 | 描述 |
|--------|------|
| 200 | 请求成功 |
| 400 | 请求参数错误 |
| 401 | 认证失败 |
| 404 | 资源不存在 |
| 422 | 验证错误 |
| 500 | 服务器内部错误 |

### 重试策略

- **5xx 错误**: 建议使用指数退避重试
- **4xx 错误**: 不建议重试，修正请求后重试
- **429 (Too Many Requests)**: 根据 `Retry-After` 头重试

---

## 性能考虑

### Token 限制

- **GPT-4**: 最大 8192 tokens
- **GPT-3.5 Turbo**: 最大 4096 tokens
- **GLM-4**: 最大 8192 tokens

### 建议最佳实践

1. **缓存结果**: 对于相同的 prompt 和 context，缓存响应
2. **批量请求**: 合并多个小请求
3. **流式响应**: 对于长文本，使用流式响应
4. **温度参数**: 
   - 0.0-0.3: 精确答案
   - 0.4-0.7: 平衡
   - 0.8-2.0: 创造性

---

## 支持和反馈

- **文档**: https://github.com/Liozhang/wishub-mcp
- **Issues**: https://github.com/Liozhang/wishub-mcp/issues
- **API 文档 (Swagger)**: http://localhost:8000/docs
