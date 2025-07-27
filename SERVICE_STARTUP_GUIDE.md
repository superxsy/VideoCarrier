# VideoCarrier YouTube下载服务启动指南

本文档详细记录了启动YouTube下载服务及相关组件的完整过程。

## 📋 前置条件

- Python 3.13.2 已安装
- Redis 服务器已安装（位于项目根目录的 `redis/` 文件夹）
- 项目依赖已安装

## 🚀 服务启动步骤

### 1. 环境准备

#### 1.1 切换到项目目录
```powershell
# 在任意位置执行
cd C:\Users\Administrator\Desktop\code\videocarrier
```

#### 1.2 进入YouTube下载服务目录
```powershell
# 在项目根目录执行
cd services\youtube-downloader
```
**执行位置**: `C:\Users\Administrator\Desktop\code\videocarrier`

#### 1.3 安装项目依赖
```powershell
# 在youtube-downloader目录执行
pip install -r requirements.txt
```
**执行位置**: `C:\Users\Administrator\Desktop\code\videocarrier\services\youtube-downloader`

### 2. 配置环境变量

#### 2.1 检查环境配置文件
确保 `.env` 文件存在并包含正确配置：
- `CELERY_TASK_ALWAYS_EAGER=false` (使用Redis异步模式)
- `CELERY_TASK_EAGER_PROPAGATES=false`
- `REDIS_URL=redis://localhost:6379/0`

### 3. 启动服务组件

#### 3.1 启动Redis服务器
```powershell
# 在项目根目录执行
c:\Users\Administrator\Desktop\code\videocarrier\redis\redis-server.exe
```
**执行位置**: `C:\Users\Administrator\Desktop\code\videocarrier`
**端口**: 6379
**状态检查**: 看到 "Ready to accept connections" 表示启动成功

#### 3.2 启动Celery Worker
```powershell
# 在youtube-downloader目录执行
celery -A app.celery_app worker --loglevel=info
```
**执行位置**: `C:\Users\Administrator\Desktop\code\videocarrier\services\youtube-downloader`
**状态检查**: 看到任务接收日志表示启动成功

#### 3.3 启动FastAPI服务器
```powershell
# 在youtube-downloader目录执行
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
**执行位置**: `C:\Users\Administrator\Desktop\code\videocarrier\services\youtube-downloader`
**访问地址**: http://localhost:8000
**API文档**: http://localhost:8000/docs

#### 3.4 启动Celery Flower监控（可选）
```powershell
# 在youtube-downloader目录执行
celery -A app.celery_app flower --port=5555
```
**执行位置**: `C:\Users\Administrator\Desktop\code\videocarrier\services\youtube-downloader`
**访问地址**: http://localhost:5555

## 🔧 服务架构

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   FastAPI       │    │   Celery        │    │   Redis         │
│   (Port 8000)   │◄──►│   Worker        │◄──►│   (Port 6379)   │
│                 │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         ▲                                              ▲
         │                                              │
         ▼                                              ▼
┌─────────────────┐                          ┌─────────────────┐
│   Web Browser   │                          │   Flower        │
│   Frontend      │                          │   (Port 5555)   │
└─────────────────┘                          └─────────────────┘
```

## 📁 目录结构

```
videocarrier/
├── redis/                          # Redis服务器文件
│   └── redis-server.exe
├── services/
│   └── youtube-downloader/          # YouTube下载服务
│       ├── app/                     # 应用代码
│       ├── downloads/                # 下载文件存储
│       ├── .env                     # 环境配置
│       ├── requirements.txt         # Python依赖
│       └── ...
└── ...
```

## 🧪 功能测试

### API端点测试

1. **健康检查**
   ```bash
   GET http://localhost:8000/health
   ```

2. **获取视频信息**
   ```bash
   POST http://localhost:8000/video/info
   Content-Type: application/json
   
   {
     "url": "https://www.youtube.com/watch?v=VIDEO_ID"
   }
   ```

3. **下载视频**
   ```bash
   POST http://localhost:8000/video/download
   Content-Type: application/json
   
   {
     "url": "https://www.youtube.com/watch?v=VIDEO_ID",
     "quality": "720p"
   }
   ```

4. **查询任务状态**
   ```bash
   GET http://localhost:8000/task/{task_id}
   ```

### 监控界面

- **API文档**: http://localhost:8000/docs
- **Celery监控**: http://localhost:5555

## 🔍 故障排除

### 常见问题

1. **Redis连接失败**
   - 确保Redis服务器已启动
   - 检查端口6379是否被占用

2. **Celery Worker无法启动**
   - 确保在正确目录执行命令
   - 检查Python模块路径

3. **FastAPI服务器启动失败**
   - 检查端口8000是否被占用
   - 确认所有依赖已安装

### 日志查看

- **Redis日志**: 在Redis启动终端查看
- **Celery日志**: 在Celery Worker终端查看
- **FastAPI日志**: 在Uvicorn终端查看
- **Flower日志**: 在Flower终端查看

## 📝 注意事项

1. **终端管理**: 每个服务需要独立的终端窗口
2. **启动顺序**: 建议按照Redis → Celery Worker → FastAPI → Flower的顺序启动
3. **环境变量**: 确保 `.env` 文件配置正确
4. **网络访问**: 确保防火墙允许相应端口访问
5. **资源监控**: 通过Flower界面监控任务执行状态

## 🛑 服务停止

按 `Ctrl+C` 停止各个服务，建议按照启动的逆序停止：
1. Flower (Ctrl+C)
2. FastAPI (Ctrl+C)
3. Celery Worker (Ctrl+C)
4. Redis (Ctrl+C)

---

**文档创建时间**: 2025-01-25  
**服务版本**: YouTube Downloader v1.0.0  
**Redis版本**: 5.0.14.1  
**Python版本**: 3.13.2