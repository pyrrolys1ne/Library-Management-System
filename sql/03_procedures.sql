-- 03: 建立存储过程
USE library_db;

DELIMITER //

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
    
    -- 异常捕获机制
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        SET p_status = -1;
        SET p_message = '发生数据库内部错误，借阅已回滚。';
    END;

    START TRANSACTION;
    
    -- 1. 锁行并检查学生状态
    SELECT Sstatus INTO v_Sstatus FROM Student WHERE Sno = p_Sno FOR UPDATE;
    IF v_Sstatus != 'Normal' THEN
        SET p_status = 1;
        SET p_message = '学生账号状态异常（可能被冻结）。';
        ROLLBACK;
    ELSE
        -- 2. 检查是否有未缴清的罚款
        SELECT COUNT(*) INTO v_unpaid_count FROM PenaltyInfo WHERE Sno = p_Sno AND Pstatus = 'Unpaid';
        IF v_unpaid_count > 0 THEN
            SET p_status = 2;
            SET p_message = '该学生有未缴清的超期罚款。';
            ROLLBACK;
        ELSE
            -- 3. 锁行并检查图书库存
            SELECT Bcount INTO v_Bcount FROM Book WHERE Bno = p_Bno FOR UPDATE;
            IF v_Bcount <= 0 THEN
                SET p_status = 3;
                SET p_message = '图书在馆数量不足。';
                ROLLBACK;
            ELSE
                -- 4. 通过所有校验，执行业务流
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

DELIMITER ;
