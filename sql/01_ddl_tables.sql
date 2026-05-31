-- 01: 创建数据库与表结构 (DDL)
CREATE DATABASE IF NOT EXISTS library_db DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE library_db;

-- 1. Student 学生表
CREATE TABLE Student (
    Sno VARCHAR(20) PRIMARY KEY COMMENT '学号',
    Sname VARCHAR(50) NOT NULL COMMENT '姓名',
    Ssex VARCHAR(10) COMMENT '性别',
    Sdept VARCHAR(50) COMMENT '院系',
    Sstatus VARCHAR(20) DEFAULT 'Normal' COMMENT '状态：Normal正常, Suspended冻结'
) COMMENT='学生信息表';

-- 2. Book 图书表
CREATE TABLE Book (
    Bno VARCHAR(20) PRIMARY KEY COMMENT '图书编号',
    Bname VARCHAR(100) NOT NULL COMMENT '书名',
    Bauthor VARCHAR(100) COMMENT '作者',
    Bpublisher VARCHAR(100) COMMENT '出版社',
    Bcount INT DEFAULT 0 COMMENT '在馆数量'
) COMMENT='图书信息表';

-- 3. Admin 管理员表
CREATE TABLE Admin (
    Ano VARCHAR(20) PRIMARY KEY COMMENT '管理员编号',
    Aname VARCHAR(50) NOT NULL COMMENT '姓名',
    Ajobno VARCHAR(20) UNIQUE NOT NULL COMMENT '工号'
) COMMENT='管理员信息表';

-- 4. BorrowRecord 借阅记录表
CREATE TABLE BorrowRecord (
    Borrow_id INT AUTO_INCREMENT PRIMARY KEY COMMENT '流水号',
    Sno VARCHAR(20) NOT NULL COMMENT '学号',
    Bno VARCHAR(20) NOT NULL COMMENT '图书编号',
    Ano VARCHAR(20) NOT NULL COMMENT '经办管理员编号',
    Borrow_date DATE NOT NULL COMMENT '借阅日期',
    Due_date DATE NOT NULL COMMENT '应还日期',
    Return_date DATE COMMENT '实际归还日期',
    FOREIGN KEY (Sno) REFERENCES Student(Sno) ON DELETE CASCADE,
    FOREIGN KEY (Bno) REFERENCES Book(Bno) ON DELETE CASCADE,
    FOREIGN KEY (Ano) REFERENCES Admin(Ano)
) COMMENT='借阅记录表';

-- 5. ReserveInfo 预约信息表
CREATE TABLE ReserveInfo (
    Reserve_id INT AUTO_INCREMENT PRIMARY KEY COMMENT '预约号',
    Sno VARCHAR(20) NOT NULL COMMENT '学号',
    Bno VARCHAR(20) NOT NULL COMMENT '图书编号',
    Ano VARCHAR(20) COMMENT '处理管理员编号',
    Reserve_date DATE NOT NULL COMMENT '预约日期',
    Expire_date DATE NOT NULL COMMENT '失效日期',
    Rstatus VARCHAR(20) DEFAULT 'Active' COMMENT '预约状态: Active生效, Completed完成, Cancelled取消',
    FOREIGN KEY (Sno) REFERENCES Student(Sno) ON DELETE CASCADE,
    FOREIGN KEY (Bno) REFERENCES Book(Bno) ON DELETE CASCADE,
    FOREIGN KEY (Ano) REFERENCES Admin(Ano)
) COMMENT='图书预约信息表';

-- 6. PenaltyInfo 违期信息表
CREATE TABLE PenaltyInfo (
    Penalty_id INT AUTO_INCREMENT PRIMARY KEY COMMENT '违期记录号',
    Borrow_id INT NOT NULL COMMENT '借阅流水号',
    Sno VARCHAR(20) NOT NULL COMMENT '学号',
    Days_overdue INT DEFAULT 0 COMMENT '超期天数',
    Fine_amount DECIMAL(10,2) DEFAULT 0.00 COMMENT '罚款金额',
    Pstatus VARCHAR(20) DEFAULT 'Unpaid' COMMENT '缴费状态: Unpaid未缴清, Paid已缴清',
    FOREIGN KEY (Borrow_id) REFERENCES BorrowRecord(Borrow_id) ON DELETE CASCADE,
    FOREIGN KEY (Sno) REFERENCES Student(Sno) ON DELETE CASCADE
) COMMENT='学生违期与罚款信息表';
