# BBoyApp 设计文档

**日期：** 2026-03-05  
**状态：** 已确认

## 项目概述

构建一个街舞社区网站，功能类似 [and8.dance](https://and8.dance/)，数据通过定时爬虫从 and8.dance 同步，展示赛事日历、艺术家档案、团队信息、留言板和赛果报告。

---

## 技术栈

| 层次 | 技术 |
|------|------|
| 后端框架 | FastAPI |
| 数据库 | PostgreSQL |
| ORM | SQLAlchemy (async) |
| 数据库迁移 | Alembic |
| 模板引擎 | Jinja2 |
| CSS 框架 | Tailwind CSS（CDN） |
| PWA | manifest.json + sw.js |
| 爬虫 | httpx + BeautifulSoup4 |
| 调度器 | APScheduler（内嵌） |
| 邮件 | smtplib（SMTP） |
| 容器化 | Docker（单容器） |
| CI/CD | GitHub Actions（tag 触发） |

---

## 架构：单体 FastAPI

```
bboyapp/
├── app/
│   ├── main.py                 # FastAPI 入口 + 生命周期（APScheduler）
│   ├── config.py               # 配置（环境变量，Pydantic Settings）
│   ├── database.py             # SQLAlchemy async engine / session
│   ├── models/
│   │   ├── event.py
│   │   ├── artist.py
│   │   ├── group.py
│   │   ├── guestbook.py
│   │   └── battle_report.py
│   ├── routers/                # Jinja2 HTML 路由
│   │   ├── events.py
│   │   ├── artists.py
│   │   ├── groups.py
│   │   ├── guestbook.py
│   │   └── stats.py
│   ├── api/v1/                 # REST API（供管理/爬虫写入用）
│   ├── scraper/
│   │   ├── and8_client.py      # httpx 客户端，请求 and8.dance
│   │   └── tasks.py            # APScheduler 任务定义
│   ├── services/
│   │   ├── email.py            # SMTP 发送 PIN 码
│   │   └── ical.py             # iCal 导出生成
│   ├── templates/              # Jinja2 HTML 模板
│   └── static/                 # CSS / JS / 图片 / PWA 资源
├── alembic/
├── Dockerfile
├── docker-compose.yml
├── .github/workflows/docker-build.yml
└── pyproject.toml
```

---

## 数据库模型

### events
| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID PK | |
| source_id | VARCHAR UNIQUE | and8.dance 原始 ID，防重复 |
| title | VARCHAR | 赛事名称 |
| date | DATE | 开始日期 |
| end_date | DATE | 结束日期（可空） |
| location | VARCHAR | 地点 |
| country | VARCHAR | 国家 |
| region | VARCHAR | 地区 |
| level | ENUM | international / national / local |
| dance_styles | ARRAY[VARCHAR] | Breaking / Popping / Locking 等 |
| poster_url | VARCHAR | 海报图片 URL |
| source_url | VARCHAR | 原始链接 |
| created_at | TIMESTAMP | |

### artists
| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID PK | |
| source_id | VARCHAR UNIQUE | |
| name | VARCHAR | |
| nickname | VARCHAR | 艺名 |
| avatar_url | VARCHAR | |
| country | VARCHAR | |
| dance_styles | ARRAY[VARCHAR] | |
| bio | TEXT | |

### groups
| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID PK | |
| source_id | VARCHAR UNIQUE | |
| name | VARCHAR | |
| logo_url | VARCHAR | |
| country | VARCHAR | |
| dance_styles | ARRAY[VARCHAR] | |
| founded_year | INTEGER | |
| description | TEXT | |

### guestbook_messages
| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID PK | |
| nickname | VARCHAR | 留言者昵称 |
| email | VARCHAR | |
| pin_code | VARCHAR(6) | 验证码 |
| pin_expires_at | TIMESTAMP | 有效期 10 分钟 |
| email_verified | BOOLEAN | 是否已验证 |
| content | TEXT | 留言内容 |
| is_visible | BOOLEAN | 是否公开展示 |
| created_at | TIMESTAMP | |

### battle_reports
| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID PK | |
| source_id | VARCHAR UNIQUE | |
| event_id | UUID FK → events | |
| title | VARCHAR | |
| report_data | JSONB | 完整对战树结构 |
| created_at | TIMESTAMP | |

---

## 页面路由

| 路由 | 说明 |
|------|------|
| `GET /` | 首页：近期赛事 + 热门艺术家卡片 |
| `GET /events` | 时间轴 + 过滤器（地区/级别/舞种） |
| `GET /events/{id}` | 赛事详情 + iCal 下载 |
| `GET /events/calendar.ics` | iCal 订阅（动态生成） |
| `GET /artists` | 艺术家卡片网格 + 搜索 |
| `GET /artists/{id}` | 艺术家详情 |
| `GET /groups` | 团队卡片网格 |
| `GET /groups/{id}` | 团队详情 |
| `GET /guestboard` | 留言板列表 + 发帖表单 |
| `POST /guestboard/submit` | 提交留言（触发 PIN 邮件） |
| `POST /guestboard/verify` | 验证 PIN 码 |
| `GET /stats` | 赛果报告列表 |
| `GET /stats/{report_id}` | 单场赛事统计详情 |
| `GET /stats/{report_id}/{round_id}/review` | Battle 对战回顾 |

---

## UI 设计规范

- **主题**：浅色主题，无暗色模式
- **CSS 框架**：Tailwind CSS（CDN 引入）
- **卡片设计**：圆角（rounded-xl）、阴影（shadow-md）、hover 放大（transition）
- **时间轴**：CSS 竖向时间线，赛事按月分组
- **导航栏**：顶部固定，移动端汉堡菜单
- **响应式**：Mobile-first，Tailwind 断点适配
- **字体**：系统字体栈（无需引入外部字体）

---

## PWA

- `/static/manifest.json`：应用名、图标、主题色、display: standalone
- `/static/sw.js`：Cache-First 策略缓存静态资源，离线时展示首页缓存
- 在 base 模板 `<head>` 中引用 manifest 和注册 Service Worker

---

## 爬虫与数据同步

- **工具**：`httpx`（异步 HTTP） + `BeautifulSoup4`（HTML 解析）
- **调度**：APScheduler `AsyncIOScheduler`，随 FastAPI 应用启动，每 6 小时全量同步
- **去重**：通过 `source_id` 做 `INSERT ... ON CONFLICT DO UPDATE`（upsert）
- **爬取范围**：赛事、艺术家、团队、赛果报告

---

## 留言板邮件 PIN 验证流程

1. 用户填写昵称 + 邮箱 + 留言内容，点击"发送验证码"
2. 后端生成 6 位随机 PIN，写入数据库（`email_verified=False`，有效期 10 分钟）
3. 通过 SMTP 发送 PIN 邮件到用户邮箱
4. 用户在页面输入 PIN，提交验证
5. 后端校验 PIN 正确且未过期 → `email_verified=True`，留言公开显示

---

## CI/CD（GitHub Actions）

```yaml
on:
  push:
    tags:
      - 'v*'   # 仅 v1.0.0 格式的 tag 触发构建
```

- 构建多平台镜像：`linux/amd64` + `linux/arm64`
- 推送到：`ghcr.io/{owner}/bboyapp:{tag}` 和 `ghcr.io/{owner}/bboyapp:latest`

---

## 环境变量（config.py）

```
DATABASE_URL          # postgresql+asyncpg://...
SMTP_HOST
SMTP_PORT
SMTP_USER
SMTP_PASSWORD
SMTP_FROM
SCRAPER_INTERVAL_HOURS   # 默认 6
ADMIN_API_KEY             # 管理接口鉴权
```
