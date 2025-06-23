import { Menu } from '@delon/theme';

export const MENU_DATA: Menu[] = [
  {
    text: '百惟数问',
    i18n: 'menu.dataask',
    icon: { type: 'icon', value: 'home' },
    children: [
      {
        text: '监控台',
        i18n: 'menu.dataask.monitor',
        icon: { type: 'icon', value: 'dashboard' },
        children: [
          {
            text: 'AI监控大屏',
            i18n: 'menu.dataask.monitor.dashboard',
            icon: { type: 'icon', value: 'bar-chart' },
            link: '/dashboard'
          }
        ]
      },
      {
        text: '工作台',
        i18n: 'menu.dataask.workspace',
        icon: { type: 'icon', value: 'appstore' },
        children: [
          {
            text: '工作区',
            i18n: 'menu.dataask.workspace.workplace',
            icon: { type: 'icon', value: 'laptop' },
            link: '/workspace/workplace'
          },
          {
            text: '报表',
            i18n: 'menu.dataask.workspace.report',
            icon: { type: 'icon', value: 'bar-chart' },
            link: '/workspace/report'
          }
        ]
      }
    ]
  },
  {
    text: 'AI工作区',
    i18n: 'menu.ai-workspace',
    icon: { type: 'icon', value: 'robot' },
    children: [
      {
        text: 'AI问答',
        i18n: 'menu.ai-workspace.ask-data',
        icon: { type: 'icon', value: 'message' },
        link: '/ai-workspace/ask-data'
      },
      {
        text: '知识库',
        i18n: 'menu.ai-workspace.knowledge-base',
        icon: { type: 'icon', value: 'database' },
        link: '/ai-workspace/knowledge-base'
      }
    ]
  },
  {
    text: '系统管理',
    i18n: 'menu.sys',
    icon: { type: 'icon', value: 'setting' },
    children: [
      {
        text: '用户管理',
        i18n: 'menu.sys.user',
        icon: { type: 'icon', value: 'user' },
        link: '/sys/user'
      },
      {
        text: '角色管理',
        i18n: 'menu.sys.role',
        icon: { type: 'icon', value: 'team' },
        link: '/sys/role'
      },
      {
        text: '权限管理',
        i18n: 'menu.sys.permission',
        icon: { type: 'icon', value: 'safety' },
        link: '/sys/permission'
      },
      {
        text: '机构管理',
        i18n: 'menu.sys.org',
        icon: { type: 'icon', value: 'cluster' },
        link: '/sys/org'
      }
    ]
  }
];
