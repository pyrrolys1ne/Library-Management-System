-- 02: 建立触发器
USE library_db;

DELIMITER //

CREATE TRIGGER trg_after_return
AFTER UPDATE ON BorrowRecord
FOR EACH ROW
BEGIN
    DECLARE v_days_overdue INT;
    DECLARE v_fine_amount DECIMAL(10,2);
    
    -- 当归还日期被更新且不为空，且以前为空，且超期时触发
    IF NEW.Return_date IS NOT NULL AND OLD.Return_date IS NULL AND NEW.Return_date > NEW.Due_date THEN
        SET v_days_overdue = DATEDIFF(NEW.Return_date, NEW.Due_date);
        SET v_fine_amount = v_days_overdue * 0.5; -- 假设每天超期罚款 0.5 元
        
        INSERT INTO PenaltyInfo (Borrow_id, Sno, Days_overdue, Fine_amount, Pstatus)
        VALUES (NEW.Borrow_id, NEW.Sno, v_days_overdue, v_fine_amount, 'Unpaid');
        
        -- 可选：若违期自动冻结学生借阅状态
        UPDATE Student SET Sstatus = 'Suspended' WHERE Sno = NEW.Sno;
    END IF;
END;
//

DELIMITER ;
