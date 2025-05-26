# 專案簡介
此為專案管理系統的 Side Project。

## 目錄
- [專案簡介](#專案簡介)
   - [目錄](#目錄)
   - [功能](#功能)
   - [使用](#使用)
   - [安裝](#安裝)
      - [系統要求](#系統要求)
      - [安裝步驟](#安裝步驟)
   - [技術棧](#技術棧)
   - [其他](#其他)
   - [專案資料結構](#專案資料結構)

## 功能
使用者可透過自身帳號管理所屬的專案系統，並且可使用拖拉功能來將任務進行合適的狀態處理。

### 系統要求
- `Python 3.11`
- `FastAPI free`
- 其他相關套件可參考`requirements.txt`內容

### 安裝步驟
1. 確認有無安裝`poetry`
```
poetry --version
```
2. 進入虛擬環境
```
poetry shell
```
3. 安裝所需套件
```
poetry install
```
4. 資料庫遷移
```
alembic upgrade head
```
5. 啟動
```
uvicorn main:app --reload
```

## 技術棧
本專案使用以下技術和工具：
- 前端：`HTMX`、`Alpine.js`、`Sortable.js`
- 後端：`Python3`、`FastAPI`
- 版本控制：`Git`
- 資料庫：`PostgreSQL`
- 其他：`SQLAlchemy`、`Alembic`、`SweetAlert`

## 其他

## 專案資料結構
```
test
├─ Dockerfile
├─ README.md
├─ alembic.ini
├─ app
│  ├─ __init__.py
│  ├─ lanes
│  │  ├─ __init__.py
│  │  └─ views.py
│  ├─ projects
│  │  ├─ __init__.py
│  │  └─ views.py
│  ├─ tasks
│  │  ├─ __init__.py
│  │  └─ views.py
│  └─ users
│     ├─ __init__.py
│     └─ views.py
├─ database
│  ├─ __init__.py
│  └─ db.py
├─ docker-compose.yml
├─ main.py
├─ middleware.py
├─ migrations
│  ├─ README
│  ├─ env.py
│  ├─ script.py.mako
│  └─ versions
├─ models
│  ├─ __init__.py
│  ├─ lane.py
│  ├─ project.py
│  ├─ task.py
│  ├─ user.py
│  └─ user_project.py
├─ poetry.lock
├─ pyproject.toml
├─ requirements.txt
├─ schemas
│  ├─ lane.py
│  ├─ project.py
│  └─ task.py
├─ static
│  ├─ css
│  └─ js
│     ├─ auth_alerts.js
│     ├─ htmx_events.js
│     ├─ lane_actions.js
│     ├─ project_actions.js
│     ├─ sortable.js
│     ├─ sweet_alert.js
│     └─ task_actions.js
├─ templates
│  ├─ auth
│  │  ├─ login.html
│  │  └─ register.html
│  ├─ common
│  │  ├─ error_message.html
│  │  └─ message_data.html
│  ├─ lanes
│  │  ├─ edit.html
│  │  ├─ index.html
│  │  ├─ new.html
│  │  ├─ partials
│  │  │  ├─ lanes_edit.html
│  │  │  ├─ lanes_form.html
│  │  │  └─ lanes_list.html
│  │  └─ show.html
│  ├─ layout.html
│  ├─ projects
│  │  ├─ edit.html
│  │  ├─ index.html
│  │  ├─ partials
│  │  │  ├─ projects_edit.html
│  │  │  ├─ projects_form.html
│  │  │  ├─ projects_list.html
│  │  │  └─ projects_show.html
│  │  └─ show.html
│  ├─ tasks
│  │  ├─ edit.html
│  │  ├─ index.html
│  │  ├─ new.html
│  │  ├─ partials
│  │  │  ├─ lane_tasks.html
│  │  │  ├─ tasks_edit.html
│  │  │  ├─ tasks_form.html
│  │  │  ├─ tasks_item.html
│  │  │  ├─ tasks_list.html
│  │  │  └─ tasks_show.html
│  │  └─ show.html
│  └─ users
│     ├─ edit.html
│     ├─ index.html
│     └─ show.html
└─ utils
   ├─ auth.py
   ├─ flash.py
   └─ get_db.py
```