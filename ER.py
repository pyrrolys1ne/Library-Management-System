from graphviz import Digraph

# 创建一个无向图
dot = Digraph('Library_ER_Diagram', filename='Library_ER_Diagram', format='png')
dot.attr(rankdir='LR', size='14,14', dpi='300')

# 全局节点样式定义设置
# 实体：矩形 (box)
dot.attr('node', shape='box', style='filled', color='#1e1b4b', fillcolor='#f0f4f8', fontname='Microsoft YaHei')
entities = ['学生', '图书', '管理员', '借阅记录', '预约信息', '违期信息']
for entity in entities:
    dot.node(entity, label=entity, shape='box', penwidth='2')

# 联系：菱形 (diamond)
dot.attr('node', shape='diamond', style='filled', color='#b45309', fillcolor='#fef3c7', fontname='Microsoft YaHei')
relationships = [
    ('学生_借阅', '借阅'), ('图书_借阅', '被借阅'),   # 优化命名
    ('学生_预约', '发起预约'), ('图书_预约', '被预约'), # 补全图书与预约的联系
    ('借阅_产生', '产生'), ('学生_违期', '拥有'),
    ('处理_借阅', '经办借还'), ('处理_违期', '处理罚款'), ('处理_预约', '管理预约') # 补全管理员对预约的管理
]
for rel_id, rel_label in relationships:
    dot.node(rel_id, label=rel_label, penwidth='1.5')

# 属性：椭圆形 (ellipse)
dot.attr('node', shape='ellipse', style='filled', color='#475569', fillcolor='#f1f5f9', fontname='Microsoft YaHei')

# 1. 学生属性
stud_attrs = ['学号(主键)', '姓名', '性别', '院系', '状态']
for attr in stud_attrs:
    dot.node(f'S_{attr}', label=attr)
    dot.edge('学生', f'S_{attr}')

# 2. 图书属性
book_attrs = ['图书编号(主键)', '书名', '作者', '出版社', '在馆数量']
for attr in book_attrs:
    dot.node(f'B_{attr}', label=attr)
    dot.edge('图书', f'B_{attr}')

# 3. 管理员属性
admin_attrs = ['管理员编号(主键)', '姓名', '工号']
for attr in admin_attrs:
    dot.node(f'A_{attr}', label=attr)
    dot.edge('管理员', f'A_{attr}')

# 4. 借阅记录属性
borrow_attrs = ['流水号(主键)', '借阅日期', '应还日期', '实际归还日期']
for attr in borrow_attrs:
    dot.node(f'BW_{attr}', label=attr)
    dot.edge('借阅记录', f'BW_{attr}')

# 5. 预约信息属性
reserve_attrs = ['预约号(主键)', '预约日期', '失效日期', '预约状态']
for attr in reserve_attrs:
    dot.node(f'R_{attr}', label=attr)
    dot.edge('预约信息', f'R_{attr}')

# 6. 违期信息属性
overdue_attrs = ['违期记录号(主键)', '超期天数', '罚款金额', '缴费状态']
for attr in overdue_attrs:
    dot.node(f'O_{attr}', label=attr)
    dot.edge('违期信息', f'O_{attr}')


# ---- 连接实体与联系，并标出基数映射关系 ----
dot.attr('edge', color='#1e1b4b', fontname='Microsoft YaHei', fontsize='10')

# 【借阅业务闭环】
dot.edge('学生', '学生_借阅', label='1')
dot.edge('学生_借阅', '借阅记录', label='N')
dot.edge('图书', '图书_借阅', label='1')
dot.edge('图书_借阅', '借阅记录', label='N')

# 【预约业务闭环】(完全修复：学生和图书都能通过预约记录连通)
dot.edge('学生', '学生_预约', label='1')
dot.edge('学生_预约', '预约信息', label='N')     
dot.edge('图书', '图书_预约', label='1')
dot.edge('图书_预约', '预约信息', label='N')     

# 【违期衍生业务】
dot.edge('借阅记录', '借阅_产生', label='1')
dot.edge('借阅_产生', '违期信息', label='1')     
dot.edge('学生', '学生_违期', label='1')
dot.edge('学生_违期', '违期信息', label='N')

# 【管理员审计闭环】
dot.edge('管理员', '处理_借阅', label='1')
dot.edge('处理_借阅', '借阅记录', label='N')
dot.edge('管理员', '处理_违期', label='1')
dot.edge('处理_违期', '违期信息', label='N')
dot.edge('管理员', '处理_预约', label='1')
dot.edge('处理_预约', '预约信息', label='N')

# 渲染保存
dot.render(view=True)
print("完美闭环版 E-R 图已成功生成！")