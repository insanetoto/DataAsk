# DataAsk 项目图标使用指南

## 图标系统说明

本项目使用 ng-zorro-antd 的图标系统，采用静态加载方式。所有图标都通过 `@ant-design/icons-angular` 进行管理。

## 项目中已注册的图标

### 导航类图标
- `dashboard` - 仪表盘
- `appstore` - 应用商店/工作空间
- `setting` - 设置/系统管理
- `robot` - 机器人/AI工作区
- `search` - 搜索
- `user` - 用户
- `lock` - 锁定
- `logout` - 退出登录

### 操作类图标
- `plus` - 新增
- `edit` - 编辑
- `delete` - 删除
- `save` - 保存
- `reload` - 刷新
- `close` - 关闭
- `check` - 确认
- `warning` - 警告
- `info` - 信息
- `question` - 帮助

### 状态类图标
- `loading` - 加载中
- `check-circle` - 成功
- `close-circle` - 错误
- `exclamation-circle` - 警告
- `info-circle` - 信息

## 使用方式

### 1. 在模板中使用

```html
<!-- 基础用法 -->
<i nz-icon nzType="dashboard"></i>

<!-- 指定主题 -->
<i nz-icon nzType="setting" nzTheme="outline"></i>

<!-- 旋转效果 -->
<i nz-icon nzType="loading" nzSpin></i>
```

### 2. 在菜单配置中使用

```typescript
{
  text: '仪表盘',
  link: '/dashboard',
  icon: { type: 'icon', value: 'dashboard' }
}
```

## 添加新图标

如果需要添加新的图标，请按照以下步骤操作：

1. 在 `src/style-icons.ts` 中添加图标：
```typescript
import { DashboardOutline, SettingOutline /* 添加新图标 */ } from '@ant-design/icons-angular/icons';
export const ICONS = [DashboardOutline, SettingOutline /* 添加新图标 */];
```

2. 运行图标生成命令：
```bash
ng g ng-alain:plugin icon
```

## 注意事项

1. 优先使用已注册的图标，避免不必要的图标注册
2. 使用图标时注意选择合适的主题样式（outline、fill、twotone）
3. 如果遇到图标不显示的问题，请检查：
   - 图标是否已在 `style-icons.ts` 中注册
   - 图标名称是否正确（区分大小写）
   - 是否正确导入了相关模块

## 相关资源

- [Ant Design 图标库](https://ant.design/components/icon-cn/)
- [ng-alain 图标文档](https://ng-alain.com/theme/icon/zh) 