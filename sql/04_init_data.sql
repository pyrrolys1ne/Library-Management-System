-- 04: 插入基础测试数据
USE library_db;

INSERT INTO Student (Sno, Sname, Ssex, Sdept, Sstatus) VALUES 
('S001', '张三', '男', '计算机学院', 'Normal'),
('S002', '李四', '女', '软件学院', 'Normal');

INSERT INTO Book (Bno, Bname, Bauthor, Bpublisher, Bcount) VALUES 
('B001', '数据库系统概念', 'Silberschatz', '机械工业出版社', 5),
('B002', '深入理解计算机系统', 'Randal E. Bryant', '机械工业出版社', 2);

INSERT INTO Admin (Ano, Aname, Ajobno) VALUES 
('A001', '王管理员', 'W001'),
('A002', '赵管理员', 'Z001');
