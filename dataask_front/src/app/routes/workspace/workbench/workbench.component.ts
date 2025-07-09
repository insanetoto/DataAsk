import { DatePipe } from '@angular/common';
import { ChangeDetectionStrategy, ChangeDetectorRef, Component, OnInit, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { PageHeaderModule } from '@delon/abc/page-header';
import { G2RadarModule } from '@delon/chart/radar';
import { _HttpClient } from '@delon/theme';
import { SHARED_IMPORTS } from '@shared';
import { NzAvatarModule } from 'ng-zorro-antd/avatar';
import { NzBreadCrumbModule } from 'ng-zorro-antd/breadcrumb';
import { NzCheckboxModule } from 'ng-zorro-antd/checkbox';
import { NzEmptyModule } from 'ng-zorro-antd/empty';
import { NzMessageService } from 'ng-zorro-antd/message';
import { NzModalService } from 'ng-zorro-antd/modal';
import { NzTagModule } from 'ng-zorro-antd/tag';

interface UserInfo {
  id: number;
  username: string;
  role_name: string;
  org_name: string;
  avatar?: string;
  last_login_at: string;
}

interface WorkStats {
  totalTasks: number;
  completedTasks: number;
  monthlyQueries: number;
}

interface Task {
  id: number;
  title: string;
  description: string;
  type: string;
  priority: string;
  updated_at: string;
  completed?: boolean;
}

interface QuickLink {
  title: string;
  route: string;
  icon: string;
  description: string;
}

@Component({
  selector: 'app-workspace-workbench',
  templateUrl: './workbench.component.html',
  styleUrls: ['./workbench.component.less'],
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    ...SHARED_IMPORTS,
    DatePipe,
    PageHeaderModule,
    NzAvatarModule,
    NzBreadCrumbModule,
    NzCheckboxModule,
    NzEmptyModule,
    NzTagModule,
    G2RadarModule,
    FormsModule
  ]
})
export class WorkspaceWorkbenchComponent implements OnInit {
  private readonly http = inject(_HttpClient);
  private readonly msg = inject(NzMessageService);
  private readonly modal = inject(NzModalService);
  private readonly router = inject(Router);
  private readonly cdr = inject(ChangeDetectorRef);

  // 页面数据
  userInfo: UserInfo | null = null;
  workStats: WorkStats | null = null;
  activeTasks: Task[] = [];
  radarData: any[] = [];
  loading = true;

  // 快速导航链接
  quickLinks: QuickLink[] = [
    {
      title: '数据问答',
      route: '/ai-engine/ask-data',
      icon: 'message',
      description: '开始数据问答'
    },
    {
      title: '数据源管理',
      route: '/ai-engine/datasource',
      icon: 'database',
      description: '管理数据源'
    },
    {
      title: '知识库',
      route: '/ai-engine/knowledge-base',
      icon: 'file-text',
      description: '访问知识库'
    },
    {
      title: '大模型管理',
      route: '/ai-engine/llmmanage',
      icon: 'setting',
      description: '管理大模型'
    },
    {
      title: '用户管理',
      route: '/sys/user',
      icon: 'user',
      description: '管理用户'
    },
    {
      title: '系统监控',
      route: '/workspace/monitor',
      icon: 'monitor',
      description: '查看系统状态'
    }
  ];

  ngOnInit(): void {
    this.loadUserInfo();
    this.loadWorkStats();
    this.loadActiveTasks();
    this.loadRadarData();
  }

  /**
   * 获取问候语
   */
  getGreeting(): string {
    const hour = new Date().getHours();
    if (hour < 12) {
      return '早上好';
    } else if (hour < 18) {
      return '下午好';
    } else {
      return '晚上好';
    }
  }

  /**
   * 根据任务类型获取图标
   */
  getTaskIcon(type: string): string {
    const iconMap: Record<string, string> = {
      query: 'search',
      analysis: 'bar-chart',
      report: 'file-text',
      data: 'database',
      ai: 'robot',
      default: 'project'
    };
    return iconMap[type] || iconMap['default'];
  }

  /**
   * 根据优先级获取颜色
   */
  getTaskColor(priority: string): string {
    const colorMap: Record<string, string> = {
      高: 'red',
      中: 'orange',
      低: 'green',
      紧急: 'volcano'
    };
    return colorMap[priority] || 'default';
  }

  /**
   * 加载用户信息
   */
  private loadUserInfo(): void {
    // 模拟用户数据，实际应从认证服务获取
    this.userInfo = {
      id: 1,
      username: '管理员',
      role_name: '超级管理员',
      org_name: '洞察魔方',
      avatar: '',
      last_login_at: new Date().toISOString()
    };
  }

  /**
   * 加载工作统计
   */
  private loadWorkStats(): void {
    // 模拟统计数据
    this.workStats = {
      totalTasks: 15,
      completedTasks: 8,
      monthlyQueries: 236
    };
  }

  /**
   * 加载进行中的任务
   */
  private loadActiveTasks(): void {
    this.activeTasks = [
      {
        id: 1,
        title: '客户数据分析报告',
        description: '分析Q4季度客户行为数据，生成详细报告',
        type: 'analysis',
        priority: '高',
        updated_at: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString()
      },
      {
        id: 2,
        title: '数据源配置优化',
        description: '优化MySQL数据源连接池配置，提升查询性能',
        type: 'data',
        priority: '中',
        updated_at: new Date(Date.now() - 4 * 60 * 60 * 1000).toISOString()
      },
      {
        id: 3,
        title: 'AI模型训练任务',
        description: '基于最新数据集训练推荐算法模型',
        type: 'ai',
        priority: '高',
        updated_at: new Date(Date.now() - 6 * 60 * 60 * 1000).toISOString()
      }
    ];
  }

  /**
   * 加载工作指数雷达图数据
   */
  private loadRadarData(): void {
    this.radarData = [
      { item: '数据查询', user: '本月', score: 80 },
      { item: '报告生成', user: '本月', score: 60 },
      { item: '任务完成', user: '本月', score: 90 },
      { item: '协作效率', user: '本月', score: 70 },
      { item: '知识积累', user: '本月', score: 85 },
      { item: '创新应用', user: '本月', score: 65 }
    ];

    this.loading = false;
    this.cdr.detectChanges();
  }

  /**
   * 查看所有任务
   */
  viewAllTasks(): void {
    this.msg.info('跳转到任务管理页面');
    // this.router.navigate(['/workspace/tasks']);
  }

  /**
   * 查看任务详情
   */
  viewTask(task: Task): void {
    this.msg.info(`查看任务：${task.title}`);
  }

  /**
   * 查看用户信息
   */
  viewUser(): void {
    this.msg.info(`查看用户信息`);
  }

  /**
   * 导航到指定路由
   */
  navigateTo(route: string): void {
    this.router.navigate([route]);
  }

  /**
   * 添加自定义链接
   */
  addCustomLink(): void {
    this.msg.info('添加自定义链接功能');
  }
}
