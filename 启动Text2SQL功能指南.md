# 🚀 Text2SQL功能快速启动指南

## 🎯 快速体验Text2SQL功能

### 1. 启动后端服务
```bash
# 确保在项目根目录
cd /Users/xinz/Dev/DataAsk

# 激活conda环境
conda activate DataAsk

# 启动后端服务
python app.py
```
**预期输出**: 服务将在 http://localhost:9000 启动

### 2. 启动前端服务
```bash
# 在新终端窗口中
cd /Users/xinz/Dev/DataAsk/dataask_front

# 启动前端开发服务器
yarn start
```
**预期输出**: 前端将在 http://localhost:4200 启动

### 3. 访问Text2SQL功能
**访问地址**: http://localhost:4200/ai-app/text2sql

---

## 💡 功能体验建议

### 试试这些查询:
1. **简单查询**: "查询所有用户的ID和用户名"
2. **条件查询**: "查询年龄大于25岁的用户"  
3. **聚合查询**: "统计每个机构下有多少个用户"
4. **排序查询**: "按照创建时间排序显示最新的5个用户"

### 界面功能:
- ✅ 点击"新对话"创建会话
- ✅ 输入自然语言查询
- ✅ 查看实时生成的SQL
- ✅ 自动执行并显示结果
- ✅ 复制生成的SQL代码

---

## 🔧 故障排除

### 如果后端启动失败:
```bash
# 检查端口占用
lsof -i :9000

# 重新安装依赖
pip install -r requirements.txt
```

### 如果前端启动失败:
```bash
# 重新安装依赖
yarn install

# 清除缓存后重启
yarn cache clean
yarn start
```

### 如果API调用失败:
1. 确认后端服务正常运行 (http://localhost:9000/api/text2sql/health)
2. 检查网络连接
3. 查看浏览器控制台错误信息

---

## 📊 性能指标

期望的性能表现:
- SQL生成时间: < 1秒
- 查询执行时间: < 2秒  
- 前端响应时间: < 500ms

---

## 🎉 体验完成后

如果一切正常，您将看到:
1. ✅ 现代化的聊天界面
2. ✅ 实时的SQL生成
3. ✅ 准确的查询结果
4. ✅ 流畅的用户体验

**恭喜！Text2SQL功能已成功集成并可以正常使用！** 🎊 