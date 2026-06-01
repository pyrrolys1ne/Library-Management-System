# 数据库 实验二 (Lab2) —— 图书馆信息管理系统

基于 **Flask + Vue 3 + Element Plus + MySQL** 的 Web 图书馆管理系统，支持学生借阅预约、管理员核销罚款、图书底库管理等完整业务流程。

## 技术栈

| 层级     | 技术                                               |
| -------- | -------------------------------------------------- |
| 前端     | Vue 3 (CDN), Element Plus, Axios                   |
| 后端     | Python Flask                                       |
| 数据库   | MySQL 8.x，通过 PyMySQL + DBUtils 连接池访问       |
| ER 图    | Graphviz (Python)                                  |

## 项目结构

```
Lab2/
├── app.py                  # Flask 主应用 (路由、API、业务逻辑)
├── database.py             # 数据库连接池封装 (PooledDB + PyMySQL)
├── ER.py                   # E-R 图生成脚本 (Graphviz)
├── requirements.txt        # Python 依赖清单
├── static/
│   ├── default.svg         # 默认封面占位图
│   └── uploads/
│       ├── covers/         # 图书封面上传归档目录 ({书号}_cover.{ext})
│       └── pdfs/           # 试读电子版上传归档目录 ({书号}_preview.{ext})
├── templates/
│   ├── base.html           # Jinja2 母版 (Vue + Element Plus 骨架)
│   ├── index.html          # 登录页 (学生端 / 管理端切换)
│   ├── student.html        # 学生端主页 (馆藏检索、借书、预约、借阅记录)
│   └── admin.html          # 管理端后台 (还书、罚款处理、图书底库管理)
└── sql/
    ├── 01_ddl_tables.sql   # DDL：6 张核心表定义
    ├── 02_triggers.sql     # 2 个触发器 (还书违约核算、入库自动分配预约)
    ├── 03_procedures.sql   # 1 个借书存储过程 + 1 个函数 + 1 个搜索过程
    └── 04_init_data.sql    # 测试数据 (5 学生、5 图书、2 管理员、4 借阅记录等)
```

## 数据库设计 (6 张表)

| 表名           | 说明           | 核心字段                                                     |
| -------------- | -------------- | ------------------------------------------------------------ |
| Student        | 学生信息       | Sno (PK), Sname, Ssex, Sdept, Sstatus (Normal/Suspended)     |
| Book           | 图书信息       | Bno (PK), Bname, Bauthor, Bcount, cover_image, attachment_pdf, description |
| Admin          | 管理员信息     | Ano (PK), Aname, Ajobno                                      |
| BorrowRecord   | 借阅记录       | Borrow_id (PK), Sno→Student, Bno→Book, Ano→Admin, Borrow_date, Due_date, Return_date |
| ReserveInfo    | 预约排队信息   | Reserve_id (PK), Sno→Student, Bno→Book, Reserve_date, Expire_date, Rstatus |
| PenaltyInfo    | 违期罚款信息   | Penalty_id (PK), Borrow_id→BorrowRecord, Sno→Student, Days_overdue, Fine_amount, Pstatus |

ER 图见 `Library_ER_Diagram.png`，可由 `python ER.py` 重新生成。

## 核心业务功能

### 学生端
- 🔍 馆藏检索：按书名模糊 / 书号精确搜索，展示库存、排队人数、他人在借数
- 📖 借书：调用事务存储过程 `sp_borrow_book`，校验学生状态 + 罚单 + 库存后扣减
- 📝 预约排队：库存为 0 时可预约（有效期 30 天），还书/入库时自动流转
- 📋 借阅记录：查看个人历史借阅与归还状态
- 🖼️ 图书详情弹窗：封面预览、内容简介、电子版下载

### 管理端
- 📦 还书核销：归还自动触发 `trg_after_return` 核算超期罚款 (¥0.5/天)，有预约则自动转借
- 💰 罚款处理：核销罚单，全部缴清后自动解冻学生账号
- 📖 图书底库管理：新书入库（支持封面上传 + PDF 上传 + 简介录入）、库存增减、排队明细查看
- 🔍 搜索馆藏：与学生端同款搜索

## 本地运行指南

### 前置条件
- MySQL 8.x 已安装并运行
- Python 3.10+ 已安装

### 1. 激活虚拟环境
```bash
# Windows
.venv\Scripts\activate
```

### 2. 安装依赖
```bash
pip install -r requirements.txt
```

### 3. 初始化数据库
按顺序执行 `sql/` 目录下的 SQL 脚本：
```bash
# 在 MySQL 客户端中依次执行：
source sql/01_ddl_tables.sql;
source sql/02_triggers.sql;
source sql/03_procedures.sql;
source sql/04_init_data.sql;
```
> 或者在 MySQL Workbench / Navicat 中按序打开并运行这 4 个文件。

### 4. 配置数据库连接
在 `database.py` 中修改数据库连接参数，或通过环境变量注入：
```bash
export DB_HOST=127.0.0.1
export DB_PORT=3306
export DB_USER=root
export DB_PASS=your_password
export DB_NAME=library_db
```

### 5. 启动应用
```bash
python app.py
```
访问 http://127.0.0.1:5000

### 6. 测试账号

| 角色   | 账号  | 密码    | 备注          |
| ------ | ----- | ------- | ------------- |
| 学生   | S001  | 123456  | 正常状态      |
| 学生   | S002  | 123456  | 有超期未还书  |
| 学生   | S003  | 123456  | 已冻结(有欠款) |
| 学生   | S004  | 123456  | 正常状态      |
| 学生   | S005  | 123456  | 已预约 B003   |
| 管理员 | A001  | 123456  | 王管理员      |
| 管理员 | A002  | 123456  | 赵管理员      |

## 存储过程与触发器

| 名称                        | 类型     | 说明                                                |
| --------------------------- | -------- | --------------------------------------------------- |
| `sp_borrow_book`            | 存储过程 | 借书事务：行级锁校验状态→罚单→库存，ACID 保证       |
| `sp_search_books`           | 存储过程 | 按关键字搜索图书 (书名模糊 + 书号精确)               |
| `fn_get_book_status_label`  | 函数     | 返回图书状态标签 (Available / 其他人在借 / Out of Stock) |
| `trg_after_return`          | 触发器   | 还书时自动核算超期天数并生成罚单 + 冻结学生          |
| `trg_after_book_stock_update` | 触发器 | 库存从 0 变 >0 时自动消费首位预约，完成流转分配      |

## 封面上传命名规范

| 类型 | 格式                  | 示例                        |
| ---- | --------------------- | --------------------------- |
| 封面 | `{书号}_cover.{ext}`  | `B001_cover.jpg`            |
| PDF  | `{书号}_preview.{ext}` | `B001_preview.pdf`          |
