"""
图书馆管理系统 E-R 图生成脚本
运行: python ER.py
输出: Library_ER_Diagram.png
实体与属性对应 01_ddl_tables.sql 中的表结构。
"""
from graphviz import Digraph

dot = Digraph('Library_ER_Diagram', filename='Library_ER_Diagram', format='png')
dot.attr(rankdir='LR', size='16,16', dpi='300')

# ── 实体：矩形 ────────────────────────────────────────
dot.attr('node', shape='box', style='filled', color='#1e1b4b', fillcolor='#f0f4f8', fontname='Microsoft YaHei')
entities = ['学生', '图书', '管理员', '借阅记录', '预约信息', '违期信息']
for entity in entities:
    dot.node(entity, label=entity, shape='box', penwidth='2')

# ── 联系：菱形 ────────────────────────────────────────
dot.attr('node', shape='diamond', style='filled', color='#b45309', fillcolor='#fef3c7', fontname='Microsoft YaHei')
relationships = [
    ('学生_借阅', '借阅'), ('图书_借阅', '被借阅'),
    ('学生_预约', '发起预约'), ('图书_预约', '被预约'),
    ('借阅_产生', '产生'), ('学生_违期', '拥有'),
    ('处理_借阅', '经办借还'), ('处理_违期', '处理罚款'), ('处理_预约', '管理预约')
]
for rel_id, rel_label in relationships:
    dot.node(rel_id, label=rel_label, penwidth='1.5')

# ── 属性：椭圆形 ──────────────────────────────────────
dot.attr('node', shape='ellipse', style='filled', color='#475569', fillcolor='#f1f5f9', fontname='Microsoft YaHei')

# 学生 (Student)
stud_attrs = ['学号(主键)', '姓名', '性别', '院系', '状态']
for attr in stud_attrs:
    dot.node(f'S_{attr}', label=attr)
    dot.edge('学生', f'S_{attr}')

# 图书 (Book)
book_attrs = [
    '图书编号(主键)', '书名', '作者', '出版社', '在馆数量',
    '封面图片路径', '电子版路径', '图书简介'
]
for attr in book_attrs:
    dot.node(f'B_{attr}', label=attr)
    dot.edge('图书', f'B_{attr}')

# 管理员 (Admin)
admin_attrs = ['管理员编号(主键)', '姓名', '工号']
for attr in admin_attrs:
    dot.node(f'A_{attr}', label=attr)
    dot.edge('管理员', f'A_{attr}')

# 借阅记录 (BorrowRecord)
borrow_attrs = ['流水号(主键)', '借阅日期', '应还日期', '实际归还日期']
for attr in borrow_attrs:
    dot.node(f'BW_{attr}', label=attr)
    dot.edge('借阅记录', f'BW_{attr}')

# 预约信息 (ReserveInfo)
reserve_attrs = ['预约号(主键)', '预约日期', '失效日期', '预约状态']
for attr in reserve_attrs:
    dot.node(f'R_{attr}', label=attr)
    dot.edge('预约信息', f'R_{attr}')

# 违期信息 (PenaltyInfo)
overdue_attrs = ['违期记录号(主键)', '超期天数', '罚款金额', '缴费状态']
for attr in overdue_attrs:
    dot.node(f'O_{attr}', label=attr)
    dot.edge('违期信息', f'O_{attr}')

# ── 基数映射 ──────────────────────────────────────────
dot.attr('edge', color='#1e1b4b', fontname='Microsoft YaHei', fontsize='10')

# 借阅
dot.edge('学生', '学生_借阅', label='1')
dot.edge('学生_借阅', '借阅记录', label='N')
dot.edge('图书', '图书_借阅', label='1')
dot.edge('图书_借阅', '借阅记录', label='N')

# 预约
dot.edge('学生', '学生_预约', label='1')
dot.edge('学生_预约', '预约信息', label='N')
dot.edge('图书', '图书_预约', label='1')
dot.edge('图书_预约', '预约信息', label='N')

# 违期
dot.edge('借阅记录', '借阅_产生', label='1')
dot.edge('借阅_产生', '违期信息', label='1')
dot.edge('学生', '学生_违期', label='1')
dot.edge('学生_违期', '违期信息', label='N')

# 管理员
dot.edge('管理员', '处理_借阅', label='1')
dot.edge('处理_借阅', '借阅记录', label='N')
dot.edge('管理员', '处理_违期', label='1')
dot.edge('处理_违期', '违期信息', label='N')
dot.edge('管理员', '处理_预约', label='1')
dot.edge('处理_预约', '预约信息', label='N')

dot.render(view=True)
