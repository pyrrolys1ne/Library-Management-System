from flask import Flask, render_template, request, jsonify
from database import db
import traceback

app = Flask(__name__)
# 保持 JSON 响应中文不乱码
app.config['JSON_AS_ASCII'] = False 

# ==========================
# 页面渲染路由
# ==========================
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/student')
def student():
    return render_template('student.html')

@app.route('/admin')
def admin():
    return render_template('admin.html')

# ==========================
# API 接口路由
# ==========================

# 1. 获取所有图书列表
@app.route('/api/books', methods=['GET'])
def get_books():
    try:
        books = db.fetchall("SELECT * FROM Book")
        return jsonify({'code': 200, 'data': books, 'msg': 'success'})
    except Exception as e:
        return jsonify({'code': 500, 'msg': str(e)})

# 2. 调用存储过程进行借书
@app.route('/api/borrow', methods=['POST'])
def borrow_book():
    data = request.json
    sno = data.get('sno')
    bno = data.get('bno')
    ano = data.get('ano', 'A001') # 前端不传则默认从管理员 A001 借出
    
    if not all([sno, bno, ano]):
        return jsonify({'status': -1, 'message': '请求参数不足！'})
        
    try:
        # DBUtils 封装的存储过程调用，内含独立事务 ACID
        result = db.callproc_borrow(sno, bno, ano)
        # 该 result 形式为： {'status': 0或1或2或3, 'message': 'xxx信息'}
        return jsonify(result)
    except Exception as e:
        traceback.print_exc()
        return jsonify({'status': -1, 'message': '服务器遇到内部错误：' + str(e)})

# 3. 获取特定学生的借阅记录
@app.route('/api/student/<sno>/records', methods=['GET'])
def get_student_records(sno):
    try:
        sql = """
            SELECT br.Borrow_id, br.Bno, bk.Bname, br.Ano, 
                   br.Borrow_date, br.Due_date, br.Return_date 
            FROM BorrowRecord br
            JOIN Book bk ON br.Bno = bk.Bno
            WHERE br.Sno = %s
            ORDER BY br.Borrow_date DESC
        """
        records = db.fetchall(sql, (sno,))
        
        # 将 date 对象转成字符串，解决 jsonify 的序列化问题
        for row in records:
            if row['Borrow_date']: row['Borrow_date'] = row['Borrow_date'].strftime('%Y-%m-%d')
            if row['Due_date']: row['Due_date'] = row['Due_date'].strftime('%Y-%m-%d')
            if row['Return_date']: row['Return_date'] = row['Return_date'].strftime('%Y-%m-%d')
            
        return jsonify({'code': 200, 'data': records})
    except Exception as e:
        traceback.print_exc()
        return jsonify({'code': 500, 'msg': str(e)})

# ==========================
# 管理员后台 API 接口路由
# ==========================

# 4. 获取所有未还借阅记录（供管理员核销）
@app.route('/api/admin/borrow_records', methods=['GET'])
def get_all_borrows():
    try:
        sql = """
            SELECT br.Borrow_id, br.Sno, s.Sname, br.Bno, bk.Bname, br.Borrow_date, br.Due_date, br.Return_date
            FROM BorrowRecord br
            JOIN Student s ON br.Sno = s.Sno
            JOIN Book bk ON br.Bno = bk.Bno
            WHERE br.Return_date IS NULL
            ORDER BY br.Borrow_date DESC
        """
        records = db.fetchall(sql)
        for row in records:
            if row['Borrow_date']: row['Borrow_date'] = row['Borrow_date'].strftime('%Y-%m-%d')
            if row['Due_date']: row['Due_date'] = row['Due_date'].strftime('%Y-%m-%d')
            if row['Return_date']: row['Return_date'] = row['Return_date'].strftime('%Y-%m-%d')
        return jsonify({'code': 200, 'data': records})
    except Exception as e:
        return jsonify({'code': 500, 'msg': str(e)})

# 5. 管理员操作：归还图书
@app.route('/api/admin/return_book', methods=['POST'])
def return_book():
    data = request.json
    borrow_id = data.get('borrow_id')
    bno = data.get('bno')
    if not borrow_id or not bno:
        return jsonify({'code': 400, 'msg': '参数不完整'})
    
    try:
        conn = db.get_conn()
        cursor = conn.cursor()
        # 更新借阅状态: 填上当前日期
        # 此时触发器(trg_after_return)会在背后判定：如果大于应还日期，自动插入罚款表并挂起学生状态
        cursor.execute("UPDATE BorrowRecord SET Return_date = CURDATE() WHERE Borrow_id = %s", (borrow_id,))
        # 归还后需要把书的在馆数量 +1
        cursor.execute("UPDATE Book SET Bcount = Bcount + 1 WHERE Bno = %s", (bno,))
        conn.commit()
        
        return jsonify({'code': 200, 'msg': '归还成功，已自动核算可能产生的违期。'})
    except Exception as e:
        traceback.print_exc()
        return jsonify({'code': 500, 'msg': '归还失败：' + str(e)})

# 6. 获取所有罚单记录
@app.route('/api/admin/penalties', methods=['GET'])
def get_penalties():
    try:
        sql = """
            SELECT p.Penalty_id, p.Borrow_id, p.Sno, s.Sname, p.Days_overdue, p.Fine_amount, p.Pstatus
            FROM PenaltyInfo p
            JOIN Student s ON p.Sno = s.Sno
            ORDER BY p.Penalty_id DESC
        """
        records = db.fetchall(sql)
        for row in records:
            # Fine_amount 属于 Decimal 类型，需要进行 JSON 友好的浮点转换
            if 'Fine_amount' in row and row['Fine_amount'] is not None:
                row['Fine_amount'] = float(row['Fine_amount'])
        return jsonify({'code': 200, 'data': records})
    except Exception as e:
        return jsonify({'code': 500, 'msg': str(e)})

# 7. 管理员操作：缴纳罚款与解除冻结
@app.route('/api/admin/pay_penalty', methods=['POST'])
def pay_penalty():
    data = request.json
    penalty_id = data.get('penalty_id')
    sno = data.get('sno')
    
    if not penalty_id or not sno:
        return jsonify({'code': 400, 'msg': '参数不完整'})
        
    try:
        conn = db.get_conn()
        cursor = conn.cursor()
        
        # 1. 核销该笔罚款
        cursor.execute("UPDATE PenaltyInfo SET Pstatus = 'Paid' WHERE Penalty_id = %s", (penalty_id,))
        
        # 2. 检查该学生是否还有其他未缴清的罚款
        cursor.execute("SELECT COUNT(*) as cnt FROM PenaltyInfo WHERE Sno = %s AND Pstatus = 'Unpaid'", (sno,))
        unpaid = cursor.fetchone()['cnt']
        
        msg = '缴纳成功！'
        # 3. 如果所有欠款处理完毕，将账号解冻
        if unpaid == 0:
            cursor.execute("UPDATE Student SET Sstatus = 'Normal' WHERE Sno = %s", (sno,))
            msg += ' 该学生已无未缴罚款，账号已恢复 Normal 冻结解除。'
            
        conn.commit()
        return jsonify({'code': 200, 'msg': msg})
    except Exception as e:
        traceback.print_exc()
        return jsonify({'code': 500, 'msg': '缴费操作失败：' + str(e)})

if __name__ == '__main__':
    # 启用 Debug 模式支持热更新
    app.run(debug=True, port=5000)
