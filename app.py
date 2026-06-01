import os
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from database import db
import traceback

app = Flask(__name__)
app.secret_key = 'super_secret_key_for_lab2'
app.config['JSON_AS_ASCII'] = False

# ── 页面路由 ──────────────────────────────────────────
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/student')
def student():
    return render_template('student.html')

@app.route('/admin')
def admin():
    return render_template('admin.html')

# ── 登录与登出 ────────────────────────────────────────
@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    role = data.get('role')
    username = data.get('username')
    password = data.get('password')

    try:
        if role == 'student':
            user = db.fetchall("SELECT Sno, Sname FROM Student WHERE Sno=%s AND Spassword=%s", (username, password))
            if user:
                session['user_id'] = user[0]['Sno']
                session['user_name'] = user[0]['Sname']
                session['role'] = 'student'
                return jsonify({'code': 200, 'msg': '登录成功'})
        elif role == 'admin':
            user = db.fetchall("SELECT Ano, Aname FROM Admin WHERE Ano=%s AND Apassword=%s", (username, password))
            if user:
                session['user_id'] = user[0]['Ano']
                session['user_name'] = user[0]['Aname']
                session['role'] = 'admin'
                return jsonify({'code': 200, 'msg': '登录成功'})

        return jsonify({'code': 401, 'msg': '账号或密码错误'})
    except Exception as e:
        return jsonify({'code': 500, 'msg': str(e)})

@app.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'code': 200, 'msg': '已退出登录'})

@app.route('/api/user_info', methods=['GET'])
def user_info():
    if 'user_id' in session:
        user_id = session['user_id']
        role = session['role']
        status = 'Normal'

        if role == 'student':
            user = db.fetchall("SELECT Sstatus FROM Student WHERE Sno=%s", (user_id,))
            if user:
                status = user[0]['Sstatus']

        return jsonify({'code': 200, 'data': {
            'user_id': user_id,
            'user_name': session['user_name'],
            'role': role,
            'status': status
        }})
    return jsonify({'code': 401, 'msg': '未登录'})

# ── 图书查询 ──────────────────────────────────────────
@app.route('/api/books', methods=['GET'])
def get_books():
    keyword = request.args.get('keyword', '')
    try:
        conn = db.get_conn()
        cursor = conn.cursor()

        if keyword:
            cursor.execute("CALL sp_search_books(%s)", (keyword,))
            books = cursor.fetchall()

            cursor.close()
            cursor = conn.cursor()
            for b in books:
                cursor.execute("SELECT COUNT(*) AS rc FROM ReserveInfo WHERE Bno=%s AND Rstatus='Active' AND Expire_date >= CURDATE()", (b['Bno'],))
                b['ReserveCount'] = cursor.fetchone()['rc']
                cursor.execute("SELECT COUNT(*) AS bc FROM BorrowRecord WHERE Bno=%s AND Return_date IS NULL", (b['Bno'],))
                b['BorrowCount'] = cursor.fetchone()['bc']
        else:
            cursor.execute("""
                SELECT b.*,
                       (SELECT COUNT(*) FROM ReserveInfo r WHERE r.Bno = b.Bno AND r.Rstatus = 'Active' AND r.Expire_date >= CURDATE()) AS ReserveCount,
                       (SELECT COUNT(*) FROM BorrowRecord br WHERE br.Bno = b.Bno AND br.Return_date IS NULL) AS BorrowCount
                FROM Book b
            """)
            books = cursor.fetchall()

        return jsonify({'code': 200, 'data': books})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'code': 500, 'msg': str(e)})

# ── 预约排队查询 ──────────────────────────────────────
@app.route('/api/book/<bno>/queue', methods=['GET'])
def get_book_queue(bno):
    try:
        sql = """
            SELECT r.Reserve_id, r.Sno, s.Sname, r.Reserve_date
            FROM ReserveInfo r
            JOIN Student s ON r.Sno = s.Sno
            WHERE r.Bno = %s AND r.Rstatus = 'Active' AND r.Expire_date >= CURDATE()
            ORDER BY r.Reserve_date ASC, r.Reserve_id ASC
        """
        queue = db.fetchall(sql, (bno,))
        for q in queue:
            if q['Reserve_date']: q['Reserve_date'] = q['Reserve_date'].strftime('%Y-%m-%d')
        return jsonify({'code': 200, 'data': queue})
    except Exception as e:
        return jsonify({'code': 500, 'msg': str(e)})

# ── 借书 ──────────────────────────────────────────────
@app.route('/api/borrow', methods=['POST'])
def borrow_book():
    data = request.json
    sno = data.get('sno')
    bno = data.get('bno')
    ano = data.get('ano', 'A001')

    if not all([sno, bno, ano]):
        return jsonify({'status': -1, 'message': '请求参数不足！'})

    try:
        result = db.callproc_borrow(sno, bno, ano)
        return jsonify(result)
    except Exception as e:
        traceback.print_exc()
        return jsonify({'status': -1, 'message': '服务器遇到内部错误：' + str(e)})

# ── 预约排队 ──────────────────────────────────────────
@app.route('/api/reserve', methods=['POST'])
def reserve_book():
    data = request.json
    sno = data.get('sno')
    bno = data.get('bno')

    if not sno or not bno:
        return jsonify({'code': 400, 'msg': '参数不完整'})

    try:
        conn = db.get_conn()
        cursor = conn.cursor()

        cursor.execute("SELECT Sstatus FROM Student WHERE Sno=%s", (sno,))
        if cursor.fetchone()['Sstatus'] == 'Suspended':
            return jsonify({'code': 403, 'msg': '您的账号已被冻结，无法预约！请先缴清罚款。'})

        cursor.execute("SELECT * FROM ReserveInfo WHERE Sno=%s AND Bno=%s AND Rstatus='Active'", (sno, bno))
        if cursor.fetchone():
            return jsonify({'code': 400, 'msg': '您已经预约过该书了，请勿重复排队！'})

        cursor.execute("""
            INSERT INTO ReserveInfo (Sno, Bno, Reserve_date, Expire_date, Rstatus)
            VALUES (%s, %s, CURDATE(), DATE_ADD(CURDATE(), INTERVAL 30 DAY), 'Active')
        """, (sno, bno))
        conn.commit()

        return jsonify({'code': 200, 'msg': '预约成功！已为您登记排队。'})
    except Exception as e:
        traceback.print_exc()
        return jsonify({'code': 500, 'msg': '预约操作失败：' + str(e)})

# ── 学生借阅记录 ──────────────────────────────────────
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

        for row in records:
            if row['Borrow_date']: row['Borrow_date'] = row['Borrow_date'].strftime('%Y-%m-%d')
            if row['Due_date']: row['Due_date'] = row['Due_date'].strftime('%Y-%m-%d')
            if row['Return_date']: row['Return_date'] = row['Return_date'].strftime('%Y-%m-%d')

        return jsonify({'code': 200, 'data': records})
    except Exception as e:
        traceback.print_exc()
        return jsonify({'code': 500, 'msg': str(e)})

# ── 管理员：待还图书 ──────────────────────────────────
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

# ── 管理员：归还图书 ──────────────────────────────────
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

        ano = session.get('user_id', 'A001')

        cursor.execute("UPDATE BorrowRecord SET Return_date = CURDATE() WHERE Borrow_id = %s", (borrow_id,))

        cursor.execute("""
            SELECT Reserve_id, Sno FROM ReserveInfo
            WHERE Bno = %s AND Rstatus = 'Active' AND Expire_date >= CURDATE()
            ORDER BY Reserve_date ASC, Reserve_id ASC LIMIT 1
        """, (bno,))
        reserver = cursor.fetchone()

        msg = '归还成功，已自动核算可能产生的违期。'

        if reserver:
            cursor.execute("UPDATE ReserveInfo SET Rstatus = 'Completed' WHERE Reserve_id = %s", (reserver['Reserve_id'],))
            cursor.execute("""
                INSERT INTO BorrowRecord (Sno, Bno, Ano, Borrow_date, Due_date)
                VALUES (%s, %s, %s, CURDATE(), DATE_ADD(CURDATE(), INTERVAL 30 DAY))
            """, (reserver['Sno'], bno, ano))

            cursor.execute("SELECT Sname FROM Student WHERE Sno=%s", (reserver['Sno'],))
            r_name = cursor.fetchone()['Sname']
            msg += f' 此书已有排队，已自动分配转借给预约学生【{r_name}】！'
        else:
            cursor.execute("UPDATE Book SET Bcount = Bcount + 1 WHERE Bno = %s", (bno,))

        conn.commit()
        return jsonify({'code': 200, 'msg': msg})
    except Exception as e:
        traceback.print_exc()
        return jsonify({'code': 500, 'msg': '归还失败：' + str(e)})

# ── 管理员：罚款台账 ──────────────────────────────────
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
            if 'Fine_amount' in row and row['Fine_amount'] is not None:
                row['Fine_amount'] = float(row['Fine_amount'])
        return jsonify({'code': 200, 'data': records})
    except Exception as e:
        return jsonify({'code': 500, 'msg': str(e)})

# ── 管理员：缴纳罚款与解冻 ────────────────────────────
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

        cursor.execute("UPDATE PenaltyInfo SET Pstatus = 'Paid' WHERE Penalty_id = %s", (penalty_id,))

        cursor.execute("SELECT COUNT(*) as cnt FROM PenaltyInfo WHERE Sno = %s AND Pstatus = 'Unpaid'", (sno,))
        unpaid = cursor.fetchone()['cnt']

        msg = '缴纳成功！'
        if unpaid == 0:
            cursor.execute("UPDATE Student SET Sstatus = 'Normal' WHERE Sno = %s", (sno,))
            msg += ' 该学生已无未缴罚款，账号已恢复 Normal 冻结解除。'

        conn.commit()
        return jsonify({'code': 200, 'msg': msg})
    except Exception as e:
        traceback.print_exc()
        return jsonify({'code': 500, 'msg': '缴费操作失败：' + str(e)})

# ── 管理员：新书入库 ──────────────────────────────────
@app.route('/api/admin/book/add', methods=['POST'])
def add_book():
    bname = request.form.get('bname')
    bauthor = request.form.get('bauthor', '')
    bpublisher = request.form.get('bpublisher', '')
    bcount = int(request.form.get('bcount', 0))
    description = request.form.get('description', '')

    if not bname:
        return jsonify({'code': 400, 'msg': '书名不能为空'})

    try:
        conn = db.get_conn()
        cursor = conn.cursor()

        cursor.execute("SELECT MAX(Bno) as max_bno FROM Book WHERE Bno LIKE 'B%'")
        row = cursor.fetchone()
        if row and row['max_bno']:
            max_id = int(row['max_bno'][1:])
            bno = f"B{max_id + 1:03d}"
        else:
            bno = "B001"

        cover_path = ''
        pdf_path = ''

        cover_file = request.files.get('cover')
        if cover_file and cover_file.filename:
            ext = cover_file.filename.rsplit('.', 1)[-1]
            filename = f"{bno}_cover.{ext}"
            filepath = os.path.join('static', 'uploads', 'covers', filename)
            cover_file.save(filepath)
            cover_path = f"/{filepath}".replace('\\', '/')

        pdf_file = request.files.get('pdf')
        if pdf_file and pdf_file.filename:
            ext = pdf_file.filename.rsplit('.', 1)[-1]
            filename = f"{bno}_preview.{ext}"
            filepath = os.path.join('static', 'uploads', 'pdfs', filename)
            pdf_file.save(filepath)
            pdf_path = f"/{filepath}".replace('\\', '/')

        cursor.execute("""
            INSERT INTO Book (Bno, Bname, Bauthor, Bpublisher, Bcount, description, cover_image, attachment_pdf)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (bno, bname, bauthor, bpublisher, bcount, description, cover_path, pdf_path))
        conn.commit()
        return jsonify({'code': 200, 'msg': f'新书入库成功，分配书号：{bno}'})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'code': 500, 'msg': str(e)})

# ── 管理员：库存增减 ──────────────────────────────────
@app.route('/api/admin/book/stock', methods=['POST'])
def update_stock():
    data = request.json
    bno = data.get('bno')
    delta = int(data.get('delta', data.get('direction', 0)))

    try:
        conn = db.get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT Bcount FROM Book WHERE Bno=%s FOR UPDATE", (bno,))
        book = cursor.fetchone()
        if not book:
            return jsonify({'code': 404, 'msg': '未找到书籍'})

        new_count = book['Bcount'] + delta
        if new_count < 0:
            return jsonify({'code': 400, 'msg': '出库失败：库存不能为负'})

        if new_count == 0:
            cursor.execute("SELECT COUNT(*) AS in_borrow FROM BorrowRecord WHERE Bno=%s AND Return_date IS NULL", (bno,))
            in_borrow = cursor.fetchone()['in_borrow']
            if in_borrow == 0:
                cursor.execute("DELETE FROM Book WHERE Bno = %s", (bno,))
                conn.commit()
                return jsonify({'code': 200, 'msg': '库存与在借皆为0，已将该书目从底库彻底移除。'})

        cursor.execute("UPDATE Book SET Bcount = %s WHERE Bno = %s", (new_count, bno))
        msg = '库存更新成功'

        if delta > 0:
            cursor.execute("""
                SELECT Reserve_id, Sno FROM ReserveInfo
                WHERE Bno = %s AND Rstatus = 'Active' AND Expire_date >= CURDATE()
                ORDER BY Reserve_date ASC, Reserve_id ASC LIMIT 1
            """, (bno,))
            reserver = cursor.fetchone()

            if reserver and new_count > 0:
                ano = session.get('user_id', 'A001')
                cursor.execute("UPDATE ReserveInfo SET Rstatus = 'Completed' WHERE Reserve_id = %s", (reserver['Reserve_id'],))
                cursor.execute("""
                    INSERT INTO BorrowRecord (Sno, Bno, Ano, Borrow_date, Due_date)
                    VALUES (%s, %s, %s, CURDATE(), DATE_ADD(CURDATE(), INTERVAL 30 DAY))
                """, (reserver['Sno'], bno, ano))
                cursor.execute("UPDATE Book SET Bcount = Bcount - 1 WHERE Bno = %s", (bno,))
                msg = '入库成功。库存已自动分配流转给排队首位的学生！'

        conn.commit()
        return jsonify({'code': 200, 'msg': msg})
    except Exception as e:
        return jsonify({'code': 500, 'msg': str(e)})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
