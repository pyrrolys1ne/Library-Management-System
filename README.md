# 数据库 实验二 (Lab2)

这是一个基于 Web 的数据库应用项目。

## 项目结构
- `app.py`: 应用主程序 (后端路由与逻辑)
- `database.py`: 数据库连接与操作层
- `ER.py`: ER图相关或实体定义
- `sql/`: 数据库初始化脚本 (建表、触发器、存储过程、初始数据)
- `templates/`: 前端 HTML 模板 (管理员视图、学生视图等)
- `static/`: 前端静态资源

## 本地运行指南

1. **激活虚拟环境** (推荐)
   ```bash
   # Windows
   .venv\Scripts\activate
   ```
2. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```
3. **初始化数据库**
   按顺序执行 `sql/` 目录下的 SQL 脚本。
4. **启动应用**
   ```bash
   python app.py
   ```
