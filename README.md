面向技能型学习者的学习路径规划系统

本项目旨在开发一个 Web 学习路径规划与进度跟踪系统，解决学习者在自主学习中面临的路径不清晰、进度跟踪滞后等问题。 [cite: 5]

## 🛠 开发环境与运行 (本地启动指南)

### 1. 每次打开项目的固定流程
为了确保环境一致，请务必按照以下顺序操作：

1. **进入项目目录**：`cd skill_path_project`
2. **激活虚拟环境** (Windows): 
   ```powershell
   .\venv\Scripts\Activate.ps1

安装依赖 (如有更新): pip install -r requirements.txt
启动服务: python manage.py runserver
2. 技术栈后端: Python 3.14 + Django 6.0 
数据库: MySQL 
前端: AJAX + ECharts 
🚀 项目开发进度 (TDD 路线图)[x] 
Step 0: 环境初始化[x] Django 项目框架搭建 [x] GitHub 远程仓库关联[x] .gitignore 与 README 配置[ ] 
Step 1: 用户管理模块 [ ] 自定义用户模型 (技能标签/水平设置) [ ] 注册与登录功能 [ ]
 Step 2: 学习路径规划 [ ] 路径节点依赖关系设计 [ ] 
 Step 3: 任务管理与进度跟踪 [ ] 
 Step 4: 可视化反馈系统 (ECharts) 


注意事项：
 初始化自定义用户模型前，需确保数据库为空，否则会触发迁移冲突。