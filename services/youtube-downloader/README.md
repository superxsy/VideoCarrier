# YouTube Downloader Service

一个基于 FastAPI 和 Celery 的高性能 YouTube 视频下载服务，集成了 `yt-dlp` 工具，支持异步任务处理、进度追踪和多种下载选项。

## 🚀 特性

- **异步下载**: 使用 Celery 进行后台任务处理
- **多格式支持**: 支持视频、音频、字幕和缩略图下载
- **质量选择**: 支持多种视频质量选项（best, worst, 720p, 1080p, 1440p, 2160p）
- **进度追踪**: 实时下载进度更新
- **健康检查**: 内置服务健康监控
- **容器化**: 完整的 Docker 支持
- **URL验证**: 智能YouTube URL验证
- **视频信息**: 支持获取视频元数据而无需下载
- **灵活配置**: 丰富的环境变量配置选项

## 📋 目录

- [快速开始](#快速开始)
- [API 文档](#api-文档)
- [配置说明](#配置说明)
- [部署指南](#部署指南)
- [开发指南](#开发指南)
- [测试](#测试)
- [监控](#监控)
- [故障排除](#故障排除)

## 🚀 快速开始

### 使用 Docker

1. **克隆项目**
   ```bash
   git clone <repository-url>
   cd videocarrier/services/youtube-downloader
   ```

2. **配置环境变量**
   ```bash
   cp .env.example .env
   # 编辑 .env 文件根据需要修改配置
   ```

3. **构建并运行服务**
   ```bash
   docker build -t youtube-downloader .
   docker run -d -p 8000:8000 --name youtube-downloader youtube-downloader
   ```

4. **验证服务**
   ```bash
   curl http://localhost:8000/health
   ```

### 本地开发（Windows）

1. **安装依赖**
   ```powershell
   pip install -r requirements.txt
   ```

2. **启动 Redis**
   ```powershell
   # 使用 Docker 启动 Redis
   docker run -d -p 6379:6379 redis:alpine
   ```

3. **启动 Celery Worker**
   ```powershell
   celery -A app.celery_app worker --pool=solo --loglevel=info
   ```

4. **启动 API 服务**
   ```powershell
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

### 使用 PowerShell 测试

```powershell
# 提交下载任务
$response = Invoke-RestMethod -Uri "http://localhost:8000/download" -Method Post -ContentType "application/json" -Body '{"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ", "quality": "720p"}'

# 查询任务状态
Invoke-RestMethod -Uri "http://localhost:8000/status/$($response.task_id)" -Method Get

# 获取视频信息
Invoke-RestMethod -Uri "http://localhost:8000/info?url=https://www.youtube.com/watch?v=dQw4w9WgXcQ" -Method Get
```

## 📚 API 文档

### 基础端点

#### 健康检查
```http
GET /health
```

响应示例：
```json
{
  "status": "healthy",
  "timestamp": "2023-12-01T10:00:00Z",
  "version": "1.0.0",
  "uptime_seconds": 3600
}
```

#### 服务信息
```http
GET /
```

### 下载端点

#### 提交下载任务
```http
POST /download
Content-Type: application/json

{
  "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
  "quality": "720p",
  "audio_only": false,
  "subtitle_langs": ["en", "zh-CN"],
  "download_thumbnail": true,
  "download_description": false
}
```

响应示例：
```json
{
  "task_id": "abc123-def456-ghi789",
  "status": "pending",
  "message": "Download task submitted successfully"
}
```

#### 查询任务状态
```http
GET /status/{task_id}
```

响应示例（进行中）：
```json
{
  "task_id": "abc123-def456-ghi789",
  "status": "progress",
  "progress": 45,
  "message": "Downloading video...",
  "current": 45,
  "total": 100
}
```

响应示例（完成）：
```json
{
  "task_id": "abc123-def456-ghi789",
  "status": "success",
  "progress": 100,
  "result": {
    "video_path": "/downloads/video.mp4",
    "subtitle_paths": {
      "en": "/downloads/video.en.srt",
      "zh-CN": "/downloads/video.zh-CN.srt"
    },
    "thumbnail_path": "/downloads/video.jpg",
    "file_size": 1024000,
    "metadata": {
      "id": "dQw4w9WgXcQ",
      "title": "Rick Astley - Never Gonna Give You Up",
      "duration": 212,
      "view_count": 1000000,
      "channel": "RickAstleyVEVO"
    }
  }
}
```

#### 获取视频信息
```http
GET /info?url=https://www.youtube.com/watch?v=dQw4w9WgXcQ
```

### 支持的视频质量

- `best`: 最佳质量（默认）
- `worst`: 最低质量
- `720p`: 720p高清
- `1080p`: 1080p全高清
- `1440p`: 1440p 2K
- `2160p`: 2160p 4K

### 支持的字幕语言

- `en`: 英语
- `zh-CN`: 简体中文（默认）
- `zh-TW`: 繁体中文
- `ja`: 日语
- `ko`: 韩语
- `es`: 西班牙语
- `fr`: 法语
- `de`: 德语
- `ru`: 俄语

### 请求参数说明

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `url` | string | 是 | - | YouTube视频URL |
| `quality` | string | 否 | `best` | 视频质量选项 |
| `audio_only` | boolean | 否 | `false` | 是否仅下载音频 |
| `subtitle_langs` | array | 否 | `["zh-CN", "en"]` | 字幕语言列表 |

## ⚙️ 配置说明

### 环境变量

主要配置项（完整列表见 `.env.example`）：

#### 基础配置
| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `SERVICE_NAME` | `youtube-downloader` | 服务名称 |
| `SERVICE_VERSION` | `1.0.0` | 服务版本 |
| `ENVIRONMENT` | `development` | 运行环境 |
| `DEBUG` | `true` | 调试模式 |
| `LOG_LEVEL` | `INFO` | 日志级别 |

#### 服务器配置
| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `HOST` | `0.0.0.0` | 服务器主机 |
| `PORT` | `8000` | 服务器端口 |
| `WORKERS` | `1` | 工作进程数 |
| `RELOAD` | `true` | 是否重载代码 |

#### Redis和Celery配置
| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `REDIS_URL` | `redis://localhost:6379/0` | Redis 连接 URL |
| `CELERY_TASK_SOFT_TIME_LIMIT` | `1800` | 任务软超时（秒） |
| `CELERY_TASK_TIME_LIMIT` | `3600` | 任务硬超时（秒） |
| `CELERY_WORKER_CONCURRENCY` | `4` | Worker并发数 |

#### 下载配置
| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `DOWNLOAD_PATH` | `/app/downloads` | 下载文件存储路径 |
| `MAX_FILE_SIZE` | `0` | 最大文件大小（0=无限制） |
| `MAX_DOWNLOAD_TIME` | `3600` | 最大下载时间（秒） |
| `DEFAULT_VIDEO_QUALITY` | `best` | 默认视频质量 |
| `DEFAULT_SUBTITLE_LANGS` | `en,zh-CN` | 默认字幕语言 |

#### 文件管理配置
| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `CLEANUP_ENABLED` | `true` | 是否启用文件清理 |
| `FILE_RETENTION_HOURS` | `24` | 文件保留时间（小时） |
| `CLEANUP_INTERVAL_HOURS` | `6` | 清理任务间隔（小时） |
| `MAX_DISK_USAGE_PERCENT` | `90` | 最大磁盘使用率（%） |

### Celery 配置

```python
# 任务路由
CELERY_TASK_ROUTES = {
    'app.tasks.download_video_task': {'queue': 'download'},
    'app.tasks.cleanup_task': {'queue': 'maintenance'},
}

# 任务超时
CELERY_TASK_SOFT_TIME_LIMIT = 1800  # 30分钟
CELERY_TASK_TIME_LIMIT = 3600       # 1小时
```

## 🚢 部署指南

### Docker 部署

#### 单容器部署

```bash
# 构建镜像
docker build -t youtube-downloader .

# 启动Redis
docker run -d --name redis -p 6379:6379 redis:alpine

# 启动应用
docker run -d --name youtube-downloader \
  -p 8000:8000 \
  -e REDIS_URL=redis://host.docker.internal:6379/0 \
  -v $(pwd)/downloads:/app/downloads \
  youtube-downloader

# 启动Celery Worker
docker run -d --name celery-worker \
  -e REDIS_URL=redis://host.docker.internal:6379/0 \
  -v $(pwd)/downloads:/app/downloads \
  youtube-downloader \
  celery -A app.celery_app worker --pool=solo --loglevel=info
```

#### Windows 部署示例

```powershell
# 构建镜像
docker build -t youtube-downloader .

# 启动Redis
docker run -d --name redis -p 6379:6379 redis:alpine

# 启动应用（Windows路径）
docker run -d --name youtube-downloader `
  -p 8000:8000 `
  -e REDIS_URL=redis://host.docker.internal:6379/0 `
  -v "${PWD}/downloads:/app/downloads" `
  youtube-downloader

# 启动Celery Worker
docker run -d --name celery-worker `
  -e REDIS_URL=redis://host.docker.internal:6379/0 `
  -v "${PWD}/downloads:/app/downloads" `
  youtube-downloader `
  celery -A app.celery_app worker --pool=solo --loglevel=info
```

### 生产环境注意事项

1. **资源限制**: 设置适当的 CPU 和内存限制
2. **存储**: 使用持久化存储卷
3. **网络**: 配置适当的网络策略
4. **日志**: 集中化日志收集
5. **监控**: 配置健康检查和监控
6. **安全**: 设置环境变量和访问控制

## 🛠️ 开发指南

### 项目结构

```
youtube-downloader/
├── app/                     # 应用主目录
│   ├── __init__.py         # 服务描述和初始化
│   ├── main.py             # FastAPI 应用和API端点
│   ├── models.py           # Pydantic 数据模型
│   ├── downloader.py       # YouTube 下载器核心逻辑
│   ├── celery_app.py       # Celery 配置和初始化
│   └── tasks.py            # Celery 异步任务定义
├── tests/                  # 测试目录
│   ├── __init__.py
│   ├── conftest.py         # 测试配置和fixtures
│   ├── test_api.py         # API 端点测试
│   ├── test_downloader.py  # 下载器功能测试
│   └── test_tasks.py       # Celery 任务测试
├── downloads/              # 下载文件存储目录
├── .env                    # 环境变量配置（本地）
├── .env.example            # 环境变量配置模板
├── Dockerfile              # Docker 镜像构建文件
├── requirements.txt        # Python 依赖包列表
├── pytest.ini             # pytest 配置文件
├── pyrightconfig.json      # Python 类型检查配置
└── README.md               # 项目文档
```

### 核心组件说明

#### 1. FastAPI 应用 (`main.py`)
- 提供 RESTful API 接口
- 处理下载请求和状态查询
- 集成健康检查和错误处理

#### 2. YouTube 下载器 (`downloader.py`)
- 基于 yt-dlp 的视频下载功能
- URL 验证和视频信息提取
- 支持多种质量和格式选项

#### 3. Celery 任务系统 (`tasks.py`, `celery_app.py`)
- 异步任务处理
- 进度跟踪和状态更新
- 文件清理和维护任务

#### 4. 数据模型 (`models.py`)
- 请求和响应数据结构
- 任务状态和结果模型
- 视频信息和下载结果模型

### 添加新功能

1. **创建新的 API 端点**
   ```python
   @app.post("/new-endpoint")
   async def new_endpoint(request: NewRequest):
       # 实现逻辑
       pass
   ```

2. **添加新的 Celery 任务**
   ```python
   @celery_app.task(bind=True)
   def new_task(self, param1, param2):
       # 任务逻辑
       pass
   ```

3. **扩展下载器功能**
   ```python
   class YouTubeDownloader:
       def new_method(self, param):
           # 新功能实现
           pass
   ```

### 代码规范

- 使用 `black` 进行代码格式化
- 使用 `flake8` 进行代码检查
- 遵循 PEP 8 规范
- 编写完整的文档字符串
- 保持测试覆盖率 > 80%

## 🧪 测试

### 运行测试

```bash
# 运行所有测试
pytest

# 运行特定测试文件
pytest tests/test_api.py

# 运行带覆盖率的测试
pytest --cov=app --cov-report=html

# 运行特定标记的测试
pytest -m "not slow"
```

### 测试类型

- **单元测试**: 测试独立组件
- **集成测试**: 测试组件交互
- **API 测试**: 测试 HTTP 端点
- **任务测试**: 测试 Celery 任务

### 测试环境

#### Linux/macOS
```bash
# 设置测试环境变量
export TESTING=true
export CELERY_TASK_ALWAYS_EAGER=true
export REDIS_URL=redis://localhost:6379/1
```

#### Windows PowerShell
```powershell
# 设置测试环境变量
$env:TESTING="true"
$env:CELERY_TASK_ALWAYS_EAGER="true"
$env:REDIS_URL="redis://localhost:6379/1"
```

### 测试覆盖率

```powershell
# 生成测试覆盖率报告
pytest --cov=app --cov-report=html --cov-report=term

# 查看覆盖率报告
Start-Process .\htmlcov\index.html
```

## 📊 监控

### 健康检查

服务提供多个健康检查端点：

- `/health`: 基础健康检查
- `/health/detailed`: 详细健康信息
- `/metrics`: Prometheus 指标

### 关键指标

- **下载成功率**: 成功下载的任务比例
- **平均下载时间**: 任务完成的平均时间
- **队列长度**: 待处理任务数量
- **磁盘使用率**: 存储空间使用情况
- **内存使用率**: 服务内存消耗

### 日志

```python
# 日志配置
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'detailed': {
            'format': '{asctime} [{levelname}] {name}: {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'detailed',
        },
    },
    'root': {
        'level': 'INFO',
        'handlers': ['console'],
    },
}
```

## 🔧 故障排除

### 常见问题

#### 1. 下载失败

**症状**: 任务状态显示失败

**解决方案**:
- 检查 YouTube URL 是否有效
- 验证网络连接
- 查看 Celery worker 日志
- 检查磁盘空间

#### 2. 任务卡住

**症状**: 任务长时间处于 pending 状态

**解决方案**:
- 检查 Redis 连接
- 重启 Celery worker
- 查看任务队列状态

#### 3. 内存不足

**症状**: 服务频繁重启或响应缓慢

**解决方案**:
- 增加内存限制
- 减少并发下载数
- 启用文件清理

### 调试命令

#### Celery 调试（本地开发）
```powershell
# 查看 Celery 任务状态
celery -A app.celery_app inspect active

# 查看队列状态
celery -A app.celery_app inspect reserved

# 清空队列
celery -A app.celery_app purge

# 查看 worker 统计
celery -A app.celery_app inspect stats

# 查看注册的任务
celery -A app.celery_app inspect registered
```

#### Docker 调试
```powershell
# 查看 API 日志
docker logs youtube-downloader

# 查看 Celery worker 日志
docker logs celery-worker

# 实时查看日志
docker logs -f youtube-downloader

# 进入容器调试
docker exec -it youtube-downloader /bin/bash
```

#### 本地调试
```powershell
# 检查进程状态
Get-Process | Where-Object {$_.ProcessName -like "*python*" -or $_.ProcessName -like "*celery*"}

# 检查端口占用
netstat -an | findstr :8000
netstat -an | findstr :6379

# 检查下载目录
Get-ChildItem -Path .\downloads
```

## 🔗 平台集成

### 集成到 Video Carrier 平台

本服务设计为 Video Carrier 平台的核心组件，负责视频内容的获取和预处理。

#### 集成方式

1. **微服务架构**
   - 作为独立的微服务运行
   - 通过 REST API 与其他服务通信
   - 支持水平扩展和负载均衡

2. **API 集成**
   ```python
   # 平台调用示例
   import httpx
   
   async def download_video(video_url: str, quality: str = "720p"):
       async with httpx.AsyncClient() as client:
           # 提交下载任务
           response = await client.post(
               "http://youtube-downloader:8000/download",
               json={"url": video_url, "quality": quality}
           )
           task_data = response.json()
           
           # 轮询任务状态
           while True:
               status_response = await client.get(
                   f"http://youtube-downloader:8000/status/{task_data['task_id']}"
               )
               status = status_response.json()
               
               if status["status"] == "completed":
                   return status["result"]
               elif status["status"] == "failed":
                   raise Exception(status["message"])
               
               await asyncio.sleep(5)
   ```

3. **数据流集成**
   - 下载完成后，文件存储在共享存储中
   - 其他服务可以通过文件路径访问下载的内容
   - 支持元数据传递和处理链

#### 配置建议

```yaml
# docker-compose.yml 集成示例
version: '3.8'
services:
  youtube-downloader:
    build: ./services/youtube-downloader
    environment:
      - REDIS_URL=redis://redis:6379/0
      - DOWNLOAD_PATH=/shared/downloads
    volumes:
      - shared-storage:/shared
    networks:
      - videocarrier-network

  redis:
    image: redis:alpine
    networks:
      - videocarrier-network

volumes:
  shared-storage:

networks:
  videocarrier-network:
    driver: bridge
```

### 监控和日志

- 集成到平台的监控系统
- 统一日志收集和分析
- 健康检查和自动恢复

## 📄 许可证

MIT License

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

1. Fork 项目
2. 创建功能分支
3. 提交更改
4. 推送到分支
5. 创建 Pull Request

## 📞 支持

如有问题，请通过以下方式联系：

- 提交 GitHub Issue
- 发送邮件至 dev@videocarrier.com
- 查看项目文档

---

**VideoCarrier Team** © 2023