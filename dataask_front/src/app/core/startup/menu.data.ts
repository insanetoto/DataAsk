import { Menu } from '@delon/theme';

export const MENU_DATA: Menu[] = [
  {
    text: '洞察魔方',
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
            text: '个人工作台',
            i18n: 'menu.dataask.workspace.workplace',
            icon: { type: 'icon', value: 'laptop' },
            link: '/workspace/workbench'
          },
          {
            text: '工作报表',
            i18n: 'menu.dataask.workspace.report',
            icon: { type: 'icon', value: 'bar-chart' },
            link: '/workspace/report'
          },
          {
            text: '系统监控',
            i18n: 'menu.dataask.workspace.monitor',
            icon: { type: 'icon', value: 'monitor' },
            link: '/workspace/monitor'
          }
        ]
      },
      {
        text: 'AI引擎',
        i18n: 'menu.ai-engine',
        icon: { type: 'icon', value: 'robot' },
        children: [
          {
            text: 'AI问答',
            i18n: 'menu.ai-engine.ask-data',
            icon: { type: 'icon', value: 'message' },
            link: '/ai-engine/ask-data'
          },
          {
            text: '知识库',
            i18n: 'menu.ai-engine.knowledge-base',
            icon: { type: 'icon', value: 'database' },
            link: '/ai-engine/knowledge-base'
          },
          {
            text: '数据源管理',
            i18n: 'menu.ai-engine.datasource',
            icon: { type: 'icon', value: 'api' },
            link: '/ai-engine/datasource'
          },
          {
            text: '大模型管理',
            i18n: 'menu.ai-engine.llmmanage',
            icon: { type: 'icon', value: 'deployment-unit' },
            link: '/ai-engine/llmmanage'
          },
          {
            text: '多模态管理',
            i18n: 'menu.ai-engine.multimodal',
            icon: { type: 'icon', value: 'experiment' },
            link: '/ai-engine/multimodal'
          }
        ]
      },
      {
        text: '客服服务',
        i18n: 'menu.customer-service',
        icon: { type: 'icon', value: 'team' },
        children: [
          {
            text: '客服仪表板',
            i18n: 'menu.customer-service.dashboard',
            icon: { type: 'icon', value: 'dashboard' },
            link: '/customer-service/dashboard'
          },
          {
            text: '客服工作台',
            i18n: 'menu.customer-service.workbench',
            icon: { type: 'icon', value: 'monitor' },
            link: '/customer-service/workbench'
          },
          {
            text: '服务工单详情',
            i18n: 'menu.customer-service.order-detail',
            icon: { type: 'icon', value: 'file-text' },
            link: '/customer-service/order-detail'
          }
        ]
      },
      {
        text: '系统管理',
        i18n: 'menu.sys',
        icon: { type: 'icon', value: 'setting' },
        acl: { role: ['SUPER_ADMIN', 'ORG_ADMIN'], mode: 'oneOf' },
        children: [
          {
            text: '用户管理',
            i18n: 'menu.sys.user',
            icon: { type: 'icon', value: 'user' },
            link: '/sys/user',
            acl: { role: ['SUPER_ADMIN', 'ORG_ADMIN'], mode: 'oneOf' }
          },
          {
            text: '角色管理',
            i18n: 'menu.sys.role',
            icon: { type: 'icon', value: 'team' },
            link: '/sys/role',
            acl: { role: ['SUPER_ADMIN', 'ORG_ADMIN'], mode: 'oneOf' }
          },
          {
            text: '权限管理',
            i18n: 'menu.sys.permission',
            icon: { type: 'icon', value: 'safety' },
            link: '/sys/permission',
            acl: { role: ['SUPER_ADMIN', 'ORG_ADMIN'], mode: 'oneOf' }
          },
          {
            text: '机构管理',
            i18n: 'menu.sys.org',
            icon: { type: 'icon', value: 'cluster' },
            link: '/sys/org',
            acl: { role: ['SUPER_ADMIN', 'ORG_ADMIN'], mode: 'oneOf' }
          },
          {
            text: '工作流管理',
            i18n: 'menu.sys.workflow',
            icon: { type: 'icon', value: 'apartment' },
            link: '/sys/workflow',
            acl: { role: ['SUPER_ADMIN', 'ORG_ADMIN'], mode: 'oneOf' }
          },
          {
            text: '消息管理',
            i18n: 'menu.sys.message',
            icon: { type: 'icon', value: 'message' },
            link: '/sys/message',
            acl: { role: ['SUPER_ADMIN', 'ORG_ADMIN'], mode: 'oneOf' }
          }
        ]
      }
    ]
  }
];
