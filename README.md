# SkillPath - 面向技能型学习者的学习路径规划系统

SkillPath 是一个基于 Django 开发的 Web 学习路径规划与进度跟踪系统，主要面向长期自主学习场景，用于帮助学习者完成学习目标拆分、阶段任务管理、多泳道路径规划以及成长成果归档。

系统围绕 “目标 → 子任务 → 路径节点 → 成果归档 → 技能反馈” 的学习闭环进行设计，并结合 AJAX 异步更新、ORM 聚合查询以及 ECharts 数据可视化实现动态学习反馈。

---

## 📌 核心功能

* 学习目标创建与阶段规划
* 子任务拆分与实时进度更新
* Multi-Path 多泳道技能路径管理
* 学习成果归档与统计分析
* 技能画像与成长反馈系统
* 游戏化动态交互反馈

---

## 🛠 技术栈

### 后端

* Python
* Django
* MySQL

### 前端

* HTML5 / CSS3
* JavaScript
* AJAX
* ECharts

---

## 🚀 本地运行方式

### 1. 进入项目目录

```bash
cd skill_path_project
```

### 2. 激活虚拟环境（Windows）

```powershell
.\venv\Scripts\Activate.ps1
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 执行数据库迁移

```bash
python manage.py migrate
```

### 5. 启动开发服务器

```bash
python manage.py runserver
```

---

## 📂 项目模块结构

| 模块             | 功能说明       |
| -------------- | ---------- |
| LearningGoal   | 学习目标管理     |
| SubTask        | 子任务拆分与状态跟踪 |
| Tag            | 技能标签分类     |
| CustomPathNode | 多泳道路径节点管理  |
| Archive System | 归档统计与成果分析  |

---

## 📈 系统特点

* 基于 Django MTV 架构进行开发
* 使用 AJAX 实现局部异步刷新
* 使用 ORM 完成数据库对象映射
* 支持 archived_at 时间聚合统计
* 支持多泳道技能路径动态组织
* 支持技能成长可视化反馈

---

## ⚠ 注意事项

* 首次运行前请确保 MySQL 服务已启动
* 修改模型结构后需重新执行 migrate
* 建议使用虚拟环境进行依赖隔离

```
```
