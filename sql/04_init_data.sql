-- 04: 测试数据
USE library_db;

SET FOREIGN_KEY_CHECKS = 0;
TRUNCATE TABLE PenaltyInfo;
TRUNCATE TABLE ReserveInfo;
TRUNCATE TABLE BorrowRecord;
TRUNCATE TABLE Admin;
TRUNCATE TABLE Book;
TRUNCATE TABLE Student;
SET FOREIGN_KEY_CHECKS = 1;

-- 学生
INSERT INTO Student (Sno, Spassword, Sname, Ssex, Sdept, Sstatus) VALUES
('S001', '123456', '张三', '男', '计算机学院', 'Normal'),
('S002', '123456', '李四', '女', '软件学院', 'Normal'),
('S003', '123456', '王五', '男', '人工智能学院', 'Suspended'),
('S004', '123456', '赵六', '女', '网络安全学院', 'Normal'),
('S005', '123456', '陈七', '男', '计算机学院', 'Normal');

-- 图书
INSERT INTO Book (Bno, Bname, Bauthor, Bpublisher, Bcount, cover_image, attachment_pdf, description) VALUES
('B001', '数据库系统概念', 'Silberschatz', '机械工业出版社', 5, '/static/uploads/covers/B001_cover.jpg', '/static/uploads/pdfs/B001_preview.pdf', '数据库领域的经典教材，涵盖关系模型、SQL、数据库设计、事务管理等核心内容。'),
('B002', '深入理解计算机系统', 'Randal E. Bryant', '机械工业出版社', 2, '/static/uploads/covers/B002_cover.jpg', '/static/uploads/pdfs/B002_preview.pdf', '从程序员视角阐述计算机系统本质概念，涵盖处理器架构、存储器层次、链接、异常控制流等主题。'),
('B003', '计算机网络:自顶向下方法', 'Kurose', '机械工业出版社', 0, '/static/uploads/covers/B003_cover.jpg', '/static/uploads/pdfs/B003_preview.pdf', '自顶向下教授计算机网络，从应用层逐渐深入到物理层，涵盖HTTP、TCP/IP、DNS、网络安全等。'),
('B004', '算法导论', 'Thomas H. Cormen', '机械工业出版社', 1, '/static/uploads/covers/B004_cover.jpg', '/static/uploads/pdfs/B004_preview.pdf', '全面介绍计算机算法，涵盖排序、图算法、动态规划、贪心算法、NP完全性等经典主题。'),
('B005', '设计模式', 'GoF', '机械工业出版社', 3, '/static/uploads/covers/B005_cover.jpg', '/static/uploads/pdfs/B005_preview.pdf', '软件工程界经典之作，收录23种面向对象设计模式，包括创建型、结构型和行为型三大类。');

-- 管理员
INSERT INTO Admin (Ano, Apassword, Aname, Ajobno) VALUES
('A001', '123456', '王管理员', 'W001'),
('A002', '123456', '赵管理员', 'Z001');

-- 借阅记录
INSERT INTO BorrowRecord (Borrow_id, Sno, Bno, Ano, Borrow_date, Due_date, Return_date) VALUES
(1, 'S001', 'B001', 'A001', '2026-05-01', '2026-06-01', NULL),
(2, 'S002', 'B002', 'A002', '2026-04-01', '2026-05-01', NULL),
(3, 'S003', 'B004', 'A001', '2026-03-01', '2026-04-01', '2026-04-10'),
(4, 'S004', 'B005', 'A002', '2026-02-01', '2026-03-01', '2026-03-05');

-- 罚款记录
INSERT INTO PenaltyInfo (Penalty_id, Borrow_id, Sno, Days_overdue, Fine_amount, Pstatus) VALUES
(1, 3, 'S003', 9, 9.00, 'Unpaid'),
(2, 4, 'S004', 4, 4.00, 'Paid');

-- 预约记录
INSERT INTO ReserveInfo (Reserve_id, Sno, Bno, Ano, Reserve_date, Expire_date, Rstatus) VALUES
(1, 'S005', 'B003', 'A001', '2026-05-25', '2026-06-25', 'Active');
