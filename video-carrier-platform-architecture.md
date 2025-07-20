# Video Carrier Platform - Technical Architecture Document

## 1. Requirements Recap

• Pull public YouTube videos via URL or channel feed
• Generate Chinese subtitles (ASR → Translation → SRT format)
• Rewrite titles & descriptions in native Chinese (≤80 chars title)
• Predict categories/hashtags aligned to Bilibili taxonomy
• Optional: Rewrite on-screen text and re-dub audio in Mandarin
• Run Chinese compliance checks (political, copyright, vulgar content)
• Auto-publish to Bilibili with auth management and rate limiting
• 100% on-premises deployment (Ubuntu/Docker/K8s)
• No outbound data except YouTube pull and Bilibili push

## 2. High-Level Architecture Diagram (ASCII Art)

```
┌─────────────────┐    ┌──────────────┐    ┌─────────────────┐
│   Web Portal    │    │  API Gateway │    │  Message Queue  │
│   (React/Vue)   │◄──►│   (Nginx)    │◄──►│   (RabbitMQ)    │
└─────────────────┘    └──────────────┘    └─────────────────┘
                              │                       │
                              ▼                       ▼
┌───────────────────────────────────────────────────────────┐
│                    Microservices Layer                    │
├─────────────┬─────────────┬─────────────┬─────────────────┤
│   Video     │    ASR      │ Translation │   Compliance    │
│  Ingestion  │   Service   │   Service   │    Service      │
└─────────────┴─────────────┴─────────────┴─────────────────┘
├─────────────┬─────────────┬─────────────┬─────────────────┤
│    TTS      │  Content    │   Bilibili  │   Workflow      │
│  Service    │  Rewriter   │ Integration │   Orchestrator  │
└─────────────┴─────────────┴─────────────┴─────────────────┘
                              │
                              ▼
┌───────────────────────────────────────────────────────────┐
│                    Data & Storage Layer                   │
├─────────────┬─────────────┬─────────────┬─────────────────┤
│   Object    │  Metadata   │    Redis    │     GPU         │
│   Storage   │  Database   │    Cache    │   Cluster       │
│  (MinIO)    │ (PostgreSQL)│             │  (CUDA Nodes)   │
└─────────────┴─────────────┴─────────────┴─────────────────┘
```

## 3. End-to-End Workflow

1. **Video Intake**: User submits YouTube URL/channel via web portal
2. **Download & Validation**: Video ingestion service downloads and validates content
3. **Audio Extraction**: Extract audio track for ASR processing
4. **Speech Recognition**: Whisper model generates English transcripts
5. **Translation**: LLM translates transcripts to Chinese with timing preservation
6. **Content Rewriting**: AI rewrites title, description, and generates tags
7. **Compliance Check**: Automated screening for prohibited content
8. **Optional Re-dubbing**: TTS generates Mandarin voiceover if requested
9. **Subtitle Generation**: Create SRT files with proper formatting
10. **Quality Review**: Optional manual review queue for flagged content
11. **Bilibili Upload**: Automated publishing with metadata and subtitles
12. **Status Tracking**: Real-time progress updates and completion notifications

## 4. Service Breakdown

### Video Ingestion Service
- **Purpose**: Download, validate, and preprocess YouTube videos
- **Tech Stack**: Python, yt-dlp, FFmpeg, Celery
- **Key Libraries**: yt-dlp, moviepy, opencv-python
- **Scaling**: Horizontal scaling with worker pools, rate limiting for YouTube API

### ASR Service
- **Purpose**: Convert audio to text transcripts
- **Tech Stack**: Python, PyTorch, CUDA
- **Key Libraries**: openai-whisper, transformers, torch-audio
- **Scaling**: GPU-based scaling, model sharding for large files

### Translation Service
- **Purpose**: Translate and localize content for Chinese audience
- **Tech Stack**: Python, Transformers, vLLM
- **Key Libraries**: transformers, torch, jieba, opencc
- **Scaling**: Model parallelism, batch processing, caching

### Content Rewriter Service
- **Purpose**: Generate native Chinese titles, descriptions, and tags
- **Tech Stack**: Python, LLM inference, prompt engineering
- **Key Libraries**: transformers, langchain, tiktoken
- **Scaling**: Async processing, prompt caching, model quantization

### Compliance Service
- **Purpose**: Screen content for regulatory compliance
- **Tech Stack**: Python, NLP models, rule engines
- **Key Libraries**: jieba, fasttext, regex, custom dictionaries
- **Scaling**: Parallel processing, cached rule evaluation

### TTS Service
- **Purpose**: Generate Mandarin voiceover for re-dubbing
- **Tech Stack**: Python, PyTorch, audio processing
- **Key Libraries**: TTS, espnet, librosa, soundfile
- **Scaling**: GPU acceleration, voice model caching

### Bilibili Integration Service
- **Purpose**: Handle authentication and video publishing
- **Tech Stack**: Python, Selenium/Playwright, API clients
- **Key Libraries**: requests, selenium, pillow, fake-useragent
- **Scaling**: Session pooling, retry mechanisms, rate limiting

### Workflow Orchestrator
- **Purpose**: Coordinate multi-step processing pipeline
- **Tech Stack**: Python, Celery, Redis
- **Key Libraries**: celery, redis, sqlalchemy, pydantic
- **Scaling**: Distributed task queues, priority scheduling

## 5. AI/ML Pipeline

### Speech-to-Text
- **Model**: Whisper-large-v3 with Chinese fine-tuning
- **GPU Requirements**: NVIDIA RTX 4090 or A100 (24GB+ VRAM)
- **Latency**: ~0.1x real-time (10min video → 1min processing)
- **Optimization**: Model quantization (INT8), batch processing
- **Fallback**: Whisper-medium for resource constraints

### Translation & Rewrite
- **Primary Model**: Qwen2-72B-Instruct (quantized to 4-bit)
- **Alternative**: ChatGLM3-6B for lighter workloads
- **Prompt Templates**:
  ```
  Title Rewrite: "将以下英文标题改写为吸引中国观众的中文标题(≤80字符)：{title}"
  Description: "将以下视频描述翻译并本地化为中文，保持原意但符合中国用户习惯：{description}"
  Tags: "基于视频内容生成5-8个适合B站的中文标签：{content_summary}"
  ```
- **GPU Requirements**: 2x A100 80GB or 4x RTX 4090
- **Inference**: vLLM for optimized serving

### TTS Re-dub
- **Model**: VITS-Chinese or PaddleSpeech TTS
- **Voice Options**: Multiple Mandarin speakers (male/female, regional accents)
- **Audio Alignment**: Montreal Forced Alignment (MFA) for timing
- **Quality**: 22kHz sampling rate, natural prosody
- **Processing**: Real-time factor 0.3x (faster than real-time)

## 6. Compliance Module

### Content Rules Checked
- **Political Sensitivity**: CCP leadership, Taiwan, Hong Kong, Xinjiang topics
- **Copyright**: Watermarks, branded content, music recognition
- **Vulgar Content**: Profanity, sexual content, violence
- **Regulatory**: Gambling, drugs, medical claims

### Implementation
- **Text Analysis**: Custom trained BERT model on compliance corpus
- **Image Recognition**: CLIP model for visual content screening
- **Audio Analysis**: Keyword spotting in transcripts
- **Libraries**: 
  - `chinese-sensitive-words` for text filtering
  - `opencv` + custom models for image analysis
  - `librosa` for audio feature extraction

### Fallback Process
- Flagged content enters manual review queue
- Human reviewers use web interface for approval/rejection
- Machine learning feedback loop for model improvement
- Escalation path for borderline cases

## 7. Bilibili Integration

### Authentication Strategy
- **Method**: Cookie-based session management with Selenium
- **Backup**: API integration where available (limited endpoints)
- **Session Management**: Rotating proxy pool, user-agent randomization
- **Cookie Refresh**: Automated re-authentication every 24-48 hours

### Upload Flow
- **Endpoint**: Bilibili's video upload interface (web automation)
- **Metadata Mapping**:
  ```
  Title → 标题 (≤80 chars)
  Description → 简介 (≤2000 chars)
  Tags → 标签 (max 12 tags)
  Category → 分区 (mapped to Bilibili taxonomy)
  Thumbnail → 封面 (16:9 ratio, <2MB)
  ```

### Retry & Backoff Logic
- **Rate Limiting**: Max 5 uploads per hour per account
- **Exponential Backoff**: 1s, 2s, 4s, 8s, 16s delays
- **Error Handling**: Captcha detection, network timeouts, quota limits
- **Account Pool**: Multiple Bilibili accounts for load distribution

## 8. Storage & Data Flow

### Object Storage Layout (MinIO)
```
/videos/
  /{video_id}/
    /original.mp4          # Downloaded YouTube video
    /audio.wav             # Extracted audio
    /processed.mp4         # Final processed video
    /thumbnail.jpg         # Generated thumbnail
    /subtitles.srt         # Chinese subtitles
    /dubbing.wav           # Mandarin voiceover (if applicable)

/temp/
  /{job_id}/              # Temporary processing files
    /chunks/               # Audio/video segments
    /models/               # Cached model outputs
```

### Metadata Database Schema (PostgreSQL)
```sql
-- Videos table
CREATE TABLE videos (
    id UUID PRIMARY KEY,
    youtube_url VARCHAR(255) NOT NULL,
    youtube_id VARCHAR(50) NOT NULL,
    original_title TEXT,
    chinese_title VARCHAR(80),
    original_description TEXT,
    chinese_description TEXT,
    status VARCHAR(50), -- pending, processing, completed, failed
    bilibili_url VARCHAR(255),
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

-- Processing jobs table
CREATE TABLE jobs (
    id UUID PRIMARY KEY,
    video_id UUID REFERENCES videos(id),
    job_type VARCHAR(50), -- asr, translation, compliance, upload
    status VARCHAR(50),
    progress INTEGER, -- 0-100
    error_message TEXT,
    started_at TIMESTAMP,
    completed_at TIMESTAMP
);

-- Compliance results table
CREATE TABLE compliance_checks (
    id UUID PRIMARY KEY,
    video_id UUID REFERENCES videos(id),
    check_type VARCHAR(50),
    result VARCHAR(20), -- pass, fail, review
    confidence FLOAT,
    details JSONB,
    reviewed_by VARCHAR(100),
    created_at TIMESTAMP
);
```

## 9. Security / Governance

### ICP Filing Requirements
- **Domain Registration**: Chinese domain with ICP license
- **Server Location**: All servers physically located in mainland China
- **Data Residency**: No user data or content stored outside China
- **Compliance Officer**: Designated person for regulatory communication

### Data Protection
- **Encryption**: AES-256 for data at rest, TLS 1.3 for data in transit
- **Access Control**: RBAC with principle of least privilege
- **Audit Logging**: All user actions and system events logged
- **Backup Strategy**: 3-2-1 backup rule with geographic distribution

### Sensitive Word Dictionary Maintenance
- **Sources**: Government blacklists, industry standards, community reports
- **Update Frequency**: Weekly automated updates, emergency patches
- **Version Control**: Git-based dictionary management with approval workflow
- **Testing**: Automated regression tests for false positives/negatives

## 10. Deployment Topology

### On-Premises Infrastructure
```
Rack 1: Web & API Tier
- 3x Dell R750 (64GB RAM, 2x Xeon Gold)
- Load balancer, web servers, API gateway
- 10GbE networking

Rack 2: GPU Compute Cluster
- 4x Supermicro GPU servers
- 2x RTX 4090 per server (ASR, TTS)
- 2x A100 80GB (LLM inference)
- NVLink interconnect

Rack 3: Storage & Database
- 2x Dell R750 (PostgreSQL HA)
- 1x Storage server (MinIO cluster)
- 100TB NVMe storage pool
- 10GbE storage network

Rack 4: Management & Monitoring
- Kubernetes master nodes
- Prometheus, Grafana, ELK stack
- CI/CD pipeline (GitLab)
- Network switches, firewalls
```

### Network Segmentation
- **DMZ**: Web portal, API gateway
- **Application Tier**: Microservices, message queues
- **Data Tier**: Databases, object storage
- **GPU Tier**: AI/ML workloads (isolated VLAN)
- **Management**: Monitoring, logging, CI/CD

### DevOps Toolchain
- **Container Orchestration**: Kubernetes with Helm charts
- **CI/CD**: GitLab CI with automated testing
- **Infrastructure as Code**: Terraform + Ansible
- **Monitoring**: Prometheus + Grafana + AlertManager
- **Logging**: ELK stack (Elasticsearch, Logstash, Kibana)

## 11. MVP Roadmap (6-8 Weeks)

### Week 1-2: Foundation
- Set up Kubernetes cluster and basic infrastructure
- Implement video ingestion service with YouTube download
- Basic web portal for URL submission
- PostgreSQL database setup with core schemas

### Week 3-4: Core AI Pipeline
- Deploy Whisper ASR service with GPU acceleration
- Implement translation service with Qwen model
- Basic subtitle generation (SRT format)
- Content rewriter for titles and descriptions

### Week 5-6: Integration & Compliance
- Bilibili integration service (web automation)
- Basic compliance checking (text-based rules)
- Workflow orchestrator with Celery
- End-to-end testing of core pipeline

### Week 7-8: Polish & Production
- Advanced compliance features (image/audio analysis)
- TTS service for re-dubbing (optional feature)
- Production monitoring and alerting
- Load testing and performance optimization
- Documentation and deployment guides

## 12. Potential Pitfalls & Mitigations

### 1. YouTube Rate Limiting
- **Risk**: IP blocking, download failures
- **Mitigation**: Rotating proxy pools, distributed download nodes, respect robots.txt

### 2. Bilibili Anti-Automation
- **Risk**: Captcha challenges, account suspension
- **Mitigation**: Human-like behavior simulation, account rotation, manual fallback

### 3. GPU Memory Exhaustion
- **Risk**: OOM errors during large video processing
- **Mitigation**: Dynamic batching, model quantization, graceful degradation

### 4. Compliance False Positives
- **Risk**: Legitimate content blocked incorrectly
- **Mitigation**: Human review queue, confidence thresholds, appeal process

### 5. Model Drift & Quality
- **Risk**: Translation quality degradation over time
- **Mitigation**: Regular model evaluation, A/B testing, feedback loops

### 6. Storage Scalability
- **Risk**: Rapid storage growth, backup failures
- **Mitigation**: Automated cleanup policies, tiered storage, monitoring alerts

### 7. Network Connectivity
- **Risk**: YouTube/Bilibili access issues
- **Mitigation**: Multiple ISP connections, VPN fallbacks, offline processing

## 13. Next Questions for Stakeholders

### Business Requirements
- What is the expected daily video processing volume?
- Are there specific YouTube channels or content types to prioritize?
- What is the acceptable processing time per video (SLA requirements)?
- Do we need multi-tenant support for different content creators?

### Technical Constraints
- What is the available budget for GPU hardware?
- Are there specific compliance requirements beyond general Chinese regulations?
- Do we need integration with existing content management systems?
- What level of manual review is acceptable for compliance checking?

### Operational Concerns
- Who will be responsible for daily operations and monitoring?
- What are the disaster recovery requirements (RTO/RPO)?
- Are there specific uptime requirements (99.9%, 99.99%)?
- How should we handle copyright disputes or takedown requests?

### Future Roadmap
- Plans for supporting other video platforms (TikTok, Instagram)?
- Interest in live streaming capabilities?
- Requirements for mobile app development?
- Integration with social media management tools?

---

*This architecture document provides a comprehensive foundation for building a robust, scalable video content management platform. The modular design allows for incremental development and future enhancements while maintaining compliance with Chinese regulations and technical requirements.*