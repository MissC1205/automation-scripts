import os

with open('/tmp/server_article.js', 'r') as f:
    content = f.read()

route = """// ===== 文章详情页 =====
app.get('/article/:id', (req, res) => {
    res.sendFile(path.join(__dirname, '../public/article.html'));
});

"""

if "// ===== 全局错误处理 =====" in content:
    idx = content.find("// ===== 全局错误处理 =====")
    content = content[:idx] + route + content[idx:]
    print("✅ 路由插入成功")
    new_len = len(content)
else:
    print("❌ 未找到插入点")
    new_len = 0

with open('/home/ubuntu/server_article.js', 'w') as f:
    f.write(content)

print(f"长度: {new_len}")
