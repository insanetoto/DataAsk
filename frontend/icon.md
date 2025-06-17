# 系统支持的图标列表

本文档汇总了DataAsk智能问答系统中支持使用的所有图标名称。

## 🎨 图标库说明

系统使用 **Ant Design Icons** 作为主要图标库，所有图标都通过 `nz-icon` 组件使用。

## 📋 当前系统中使用的图标

### 🏠 工作台模块
- `user` - 用户图标（通用）
- `dashboard` - 仪表盘图标
- `home` - 首页图标

### 🤖 智能问数模块
- `database` - 数据源管理
- `message` - 智能问答
- `experiment` - 智能训练
- `book` - 知识库
- `robot` - AI机器人

### ⚙️ 系统管理模块
- `setting` - 系统设置图标
- `apartment` - 机构管理
- `team` - 角色管理
- `user` - 人员管理
- `safety-certificate` - 权限管理

### 🔧 操作类图标
- `search` - 搜索
- `reload` - 重置/刷新
- `plus` - 新增/添加
- `edit` - 编辑
- `delete` - 删除
- `key` - 重置密码
- `download` - 下载
- `upload` - 上传
- `export` - 导出
- `import` - 导入

### 📊 状态类图标
- `check-circle` - 成功状态
- `close-circle` - 失败状态
- `exclamation-circle` - 警告状态
- `info-circle` - 信息状态
- `loading` - 加载状态

### 📱 界面控制图标
- `menu-fold` - 折叠菜单
- `menu-unfold` - 展开菜单
- `fullscreen` - 全屏
- `fullscreen-exit` - 退出全屏
- `eye` - 查看
- `eye-invisible` - 隐藏

### 🔐 登录认证图标
- `login` - 登录
- `logout` - 登出
- `lock` - 锁定
- `unlock` - 解锁
- `user-add` - 注册

### 📂 文件管理图标
- `folder` - 文件夹
- `file` - 文件
- `file-text` - 文本文件
- `file-excel` - Excel文件
- `file-pdf` - PDF文件
- `cloud-upload` - 云上传

### 🔄 流程控制图标
- `play-circle` - 开始/播放
- `pause-circle` - 暂停
- `stop` - 停止
- `sync` - 同步
- `redo` - 重做
- `undo` - 撤销

### 📈 数据分析图标
- `line-chart` - 折线图
- `bar-chart` - 柱状图
- `pie-chart` - 饼图
- `area-chart` - 面积图
- `dot-chart` - 散点图

### 🌐 网络通信图标
- `api` - API接口
- `cloud` - 云服务
- `wifi` - 网络连接
- `global` - 全球/国际化

## 🎯 图标使用规范

### 基本用法
\`\`\`html
<span nz-icon nzType="user"></span>
\`\`\`

### 带颜色的图标
\`\`\`html
<span nz-icon nzType="check-circle" nzTheme="twoTone" nzTwotoneColor="#52c41a"></span>
\`\`\`

### 旋转动画图标
\`\`\`html
<span nz-icon nzType="loading" nzSpin></span>
\`\`\`

## 🎨 主题色彩

### 状态颜色
- `#52c41a` - 成功绿色
- `#f5222d` - 错误红色
- `#faad14` - 警告橙色
- `#1890ff` - 信息蓝色

### 角色等级颜色
- `red` - 超级管理员
- `orange` - 机构管理员
- `blue` - 普通用户

### HTTP方法颜色
- `blue` - GET请求
- `green` - POST请求
- `orange` - PUT请求
- `red` - DELETE请求

## 📖 扩展图标

如需使用更多图标，请参考 [Ant Design Icons 官方文档](https://ant.design/components/icon-cn/)

常用的额外图标包括：
- `heart` - 收藏/喜欢
- `star` - 星标/评级
- `bell` - 通知/消息
- `mail` - 邮件
- `phone` - 电话
- `calendar` - 日历
- `clock-circle` - 时间
- `environment` - 位置/地点 