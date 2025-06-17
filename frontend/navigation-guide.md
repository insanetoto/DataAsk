# 📖 导航菜单使用指南

## 🎯 概述

DataAsk智能问答系统的左侧导航栏使用ng-alain内置的LayoutDefault组件，支持完整的侧边栏折叠展开功能和主题切换。

## ✨ ng-alain内置功能

### 🎨 默认特性
- **内置折叠**: ng-alain提供完整的侧边栏折叠/展开功能
- **主题切换**: 支持亮色/暗色主题
- **响应式**: 自动适配移动端和平板设备
- **平滑动画**: 内置的CSS3过渡动画效果

### 🔄 侧边栏控制
- **折叠按钮**: 顶部菜单栏自动显示折叠/展开按钮
- **自动折叠**: 在平板模式下自动关闭侧边栏
- **宽度配置**: 可配置展开和折叠状态的宽度
- **状态持久化**: ng-alain自动保存折叠状态

## 🗂️ 菜单结构

### 🏠 工作台
```
🏠 工作台
├── 📊 驾驶舱 (/dashboard)
└── 👤 个人工作台 (/personal-workspace)
```

### 🤖 智能问数
```
🤖 智能问数
├── 🗄️ 数据源管理 (/data-source)
├── 💬 智能问答 (/intelligent-qa)
├── 🧪 智能训练 (/intelligent-training)
└── 📚 知识库 (/knowledge-base)
```

### ⚙️ 系统管理
```
⚙️ 系统管理
├── 🏢 机构管理 (/system-management/organization)
├── 👥 角色管理 (/system-management/role)
├── 👤 人员管理 (/system-management/user)
└── 🔐 权限管理 (/system-management/permission)
```

## 🔧 ng-alain配置

### 布局配置
```typescript
// 在 LayoutBasicComponent 中
options: LayoutDefaultOptions = {
  logoExpanded: `./assets/logo-full.svg`,    // 展开时的Logo
  logoCollapsed: `./assets/logo.svg`         // 折叠时的Logo
};

constructor() {
  // 使用ng-alain内置的布局设置
  this.settings.setLayout('collapsed', false);      // 默认不折叠
  this.settings.setLayout('collapsedWidth', 64);    // 折叠后宽度
  this.settings.setLayout('siderWidth', 200);       // 展开时宽度
}
```

### 主题配置
ng-alain支持通过SettingsService进行主题配置：
```typescript
// 设置主题
this.settings.setTheme('dark');  // 或 'light'

// 设置布局模式
this.settings.setLayout('mode', 'side');  // 侧边栏模式
```

## 🎪 简化的菜单服务

### EnhancedMenuService（简化版）
只保留必要的菜单状态管理，不干扰ng-alain内置功能：

```typescript
export class EnhancedMenuService {
  public activeMenuKey = signal('');
  public expandedMenuKeys = signal<string[]>([]);

  // 设置激活菜单
  setActiveMenu(menuKey: string): void;
  
  // 展开/收起子菜单
  toggleSubMenu(menuKey: string): void;
  
  // 检查菜单状态
  isMenuExpanded(menuKey: string): boolean;
  isMenuActive(menuKey: string): boolean;
}
```

## 🎨 使用ng-alain主题配置

### CSS变量
ng-alain内置了完整的CSS变量系统：
```less
// 侧边栏相关变量（在color.less中配置）
@alain-default-aside-wd: 200px;                    // 侧边栏宽度
@alain-default-aside-collapsed-wd: 64px;           // 折叠后宽度
@alain-default-aside-nav-fs: 14px;                 // 导航字体大小
@alain-default-aside-nav-padding-top-bottom: 12px; // 菜单项垂直padding
```

### 主题变量
```less
// 主题色彩配置
@primary-color: #1890ff;           // 主色调
@alain-default-aside-bg: #fff;     // 侧边栏背景色
@text-color: rgba(0, 0, 0, 0.85);  // 文字颜色
```

## 🚀 性能特性

### ng-alain内置优化
- **虚拟滚动**: 大量菜单项时的性能优化
- **懒加载**: 子菜单按需加载
- **缓存机制**: 菜单状态缓存
- **响应式断点**: 智能响应式处理

### 路由懒加载
```typescript
// 系统管理模块懒加载
{
  path: 'system-management',
  loadChildren: () => import('./system-management/system-management.routes')
    .then(m => m.systemManagementRoutes)
}
```

## 📱 响应式特性

### ng-alain内置断点
- **Desktop**: `> 992px` - 完整侧边栏
- **Tablet**: `768px - 992px` - 可选折叠
- **Mobile**: `< 768px` - 自动隐藏，抽屉模式

### 自动适配
```typescript
// ng-alain自动处理响应式
autoCloseUnderPad: true,  // 平板下自动关闭
```

## 🛠️ 自定义扩展

### 添加新菜单项
1. 在 `startup.service.ts` 中添加菜单配置
2. 选择合适的图标（参考 `icon.md`）
3. 创建对应的路由和组件
4. ng-alain自动处理动画和响应式

### 主题定制
1. 修改 `color.less` 中的变量
2. 使用ng-alain的主题系统
3. 通过SettingsService动态切换

## 🎯 最佳实践

### 1. 使用ng-alain原生功能
- 优先使用内置的LayoutDefault组件
- 利用SettingsService进行配置
- 遵循ng-alain的设计规范

### 2. 菜单设计原则
- 使用语义化的图标
- 保持菜单层级扁平
- 合理使用Emoji增强识别度

### 3. 性能优化
- 利用ng-alain的内置缓存
- 使用懒加载路由
- 避免过度定制

## 📖 ng-alain文档参考

- [Layout 布局](https://ng-alain.com/theme/layout)
- [Settings 设置](https://ng-alain.com/theme/settings)
- [Menu 菜单](https://ng-alain.com/theme/menu)

## 🎉 总结

使用ng-alain内置配置的优势：
- ✅ 完整的功能支持
- ✅ 优秀的性能表现
- ✅ 标准化的用户体验
- ✅ 自动的响应式处理
- ✅ 内置主题切换支持
- ✅ 持续的官方维护

现在您可以享受ng-alain提供的专业级导航体验！🚀 