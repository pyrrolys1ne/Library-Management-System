-- 02: 触发器
USE library_db;

DROP TRIGGER IF EXISTS trg_before_book_stock_update;
DROP TRIGGER IF EXISTS trg_after_book_stock_update;
DROP TRIGGER IF EXISTS trg_after_return;

DELIMITER //

-- 还书时自动核算超期罚款并冻结学生
CREATE TRIGGER trg_after_return
AFTER UPDATE ON BorrowRecord
FOR EACH ROW
BEGIN
    DECLARE v_days_overdue INT;
    DECLARE v_fine_amount DECIMAL(10,2);

    IF NEW.Return_date IS NOT NULL AND OLD.Return_date IS NULL AND NEW.Return_date > NEW.Due_date THEN
        SET v_days_overdue = DATEDIFF(NEW.Return_date, NEW.Due_date);
        SET v_fine_amount = v_days_overdue * 0.5;

        INSERT INTO PenaltyInfo (Borrow_id, Sno, Days_overdue, Fine_amount, Pstatus)
        VALUES (NEW.Borrow_id, NEW.Sno, v_days_overdue, v_fine_amount, 'Unpaid');

        UPDATE Student SET Sstatus = 'Suspended' WHERE Sno = NEW.Sno;
    END IF;
END;
//

-- 库存恢复时自动消费首位有效预约
CREATE TRIGGER trg_before_book_stock_update
BEFORE UPDATE ON Book
FOR EACH ROW
BEGIN
    DECLARE v_first_reserve_id INT;
    DECLARE v_sno VARCHAR(20);

    IF OLD.Bcount = 0 AND NEW.Bcount > 0 THEN
        SELECT Reserve_id, Sno INTO v_first_reserve_id, v_sno
        FROM ReserveInfo
        WHERE Bno = NEW.Bno AND Rstatus = 'Active' AND Expire_date >= CURDATE()
        ORDER BY Reserve_date ASC, Reserve_id ASC
        LIMIT 1;

        IF v_first_reserve_id IS NOT NULL THEN
            UPDATE ReserveInfo SET Rstatus = 'Completed' WHERE Reserve_id = v_first_reserve_id;
            INSERT INTO BorrowRecord (Sno, Bno, Ano, Borrow_date, Due_date)
            VALUES (v_sno, NEW.Bno, 'A001', CURDATE(), DATE_ADD(CURDATE(), INTERVAL 30 DAY));
            SET NEW.Bcount = NEW.Bcount - 1;
        END IF;
    END IF;
END;
//

DELIMITER ;
