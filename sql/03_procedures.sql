-- 03: 存储过程与函数
USE library_db;

DELIMITER //

-- 借书存储过程：行级锁校验状态 → 罚单 → 库存，单事务 ACID
CREATE PROCEDURE sp_borrow_book(
    IN p_Sno VARCHAR(20),
    IN p_Bno VARCHAR(20),
    IN p_Ano VARCHAR(20),
    OUT p_status INT,
    OUT p_message VARCHAR(100)
)
BEGIN
    DECLARE v_Sstatus VARCHAR(20);
    DECLARE v_unpaid_count INT;
    DECLARE v_Bcount INT;

    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        SET p_status = -1;
        SET p_message = '发生数据库内部错误，借阅已回滚。';
    END;

    START TRANSACTION;

    SELECT Sstatus INTO v_Sstatus FROM Student WHERE Sno = p_Sno FOR UPDATE;
    IF v_Sstatus != 'Normal' THEN
        SET p_status = 1;
        SET p_message = '学生账号状态异常，可能被冻结。';
        ROLLBACK;
    ELSE
        SELECT COUNT(*) INTO v_unpaid_count FROM PenaltyInfo WHERE Sno = p_Sno AND Pstatus = 'Unpaid';
        IF v_unpaid_count > 0 THEN
            SET p_status = 2;
            SET p_message = '该学生有未缴清的超期罚款。';
            ROLLBACK;
        ELSE
            SELECT Bcount INTO v_Bcount FROM Book WHERE Bno = p_Bno FOR UPDATE;
            IF v_Bcount <= 0 THEN
                SET p_status = 3;
                SET p_message = '图书在馆数量不足。';
                ROLLBACK;
            ELSE
                INSERT INTO BorrowRecord (Sno, Bno, Ano, Borrow_date, Due_date)
                VALUES (p_Sno, p_Bno, p_Ano, CURDATE(), DATE_ADD(CURDATE(), INTERVAL 30 DAY));

                UPDATE Book SET Bcount = Bcount - 1 WHERE Bno = p_Bno;

                SET p_status = 0;
                SET p_message = '借书成功。';
                COMMIT;
            END IF;
        END IF;
    END IF;
END;
//

-- 图书状态标签函数
CREATE FUNCTION fn_get_book_status_label(p_Bno VARCHAR(20)) RETURNS VARCHAR(50)
DETERMINISTIC
BEGIN
    DECLARE v_count INT;
    DECLARE v_active_borrow INT;
    SELECT Bcount INTO v_count FROM Book WHERE Bno = p_Bno;

    IF v_count > 0 THEN
        RETURN 'Available';
    ELSE
        SELECT COUNT(*) INTO v_active_borrow FROM BorrowRecord WHERE Bno = p_Bno AND Return_date IS NULL;
        IF v_active_borrow > 0 THEN
            RETURN '其他人在借';
        ELSE
            RETURN 'Out of Stock';
        END IF;
    END IF;
END;
//

-- 搜索图书存储过程：支持书名模糊 + 书号精确
CREATE PROCEDURE sp_search_books(IN p_keyword VARCHAR(100))
BEGIN
    SELECT Bno, Bname, Bauthor, Bpublisher, Bcount, cover_image, attachment_pdf, description,
           fn_get_book_status_label(Bno) as Status_Label
    FROM Book
    WHERE Bname LIKE CONCAT('%', p_keyword, '%')
       OR Bno = p_keyword;
END;
//

DELIMITER ;
