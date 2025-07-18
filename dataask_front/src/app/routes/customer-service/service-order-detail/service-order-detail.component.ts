import { Component, OnInit, inject } from '@angular/core';
import { _HttpClient } from '@delon/theme';
import { NzMessageService } from 'ng-zorro-antd/message';
import { SHARED_IMPORTS } from '@shared';
import { PageHeaderModule } from '@delon/abc/page-header';
import { NzBreadCrumbModule } from 'ng-zorro-antd/breadcrumb';
import { NzCardModule } from 'ng-zorro-antd/card';
import { NzDescriptionsModule } from 'ng-zorro-antd/descriptions';
import { NzButtonModule } from 'ng-zorro-antd/button';
import { NzIconModule } from 'ng-zorro-antd/icon';
import { NzTagModule } from 'ng-zorro-antd/tag';
import { NzTimelineModule } from 'ng-zorro-antd/timeline';

@Component({
  selector: 'app-customer-service-service-order-detail',
  imports: [
    ...SHARED_IMPORTS,
    PageHeaderModule,
    NzBreadCrumbModule,
    NzCardModule,
    NzDescriptionsModule,
    NzButtonModule,
    NzIconModule,
    NzTagModule,
    NzTimelineModule
  ],
  templateUrl: './service-order-detail.component.html',
  styleUrls: ['./service-order-detail.component.less']
})
export class CustomerServiceServiceOrderDetailComponent implements OnInit {
  private readonly http = inject(_HttpClient);
  private readonly msgSrv = inject(NzMessageService);

  // 工单详情数据
  orderDetail = {
    id: 'WO001',
    customer: '张三',
    contact: '138****8888',
    email: 'zhangsan@example.com',
    type: '技术支持',
    priority: 'high',
    status: 'processing',
    createTime: '2024-01-15 09:30:00',
    updateTime: '2024-01-15 14:20:00',
    assignee: '客服小王',
    description: '系统登录异常，无法正常访问，用户反馈已经持续2小时，影响正常工作',
    solution: '正在排查系统登录问题，初步怀疑是服务器负载过高导致',
    timeline: [
      {
        time: '2024-01-15 09:30:00',
        action: '工单创建',
        operator: '系统',
        content: '用户提交技术支持请求'
      },
      {
        time: '2024-01-15 10:00:00',
        action: '工单分配',
        operator: '系统',
        content: '工单已分配给客服小王'
      },
      {
        time: '2024-01-15 14:20:00',
        action: '开始处理',
        operator: '客服小王',
        content: '开始排查登录问题，已联系技术部门'
      }
    ]
  };

  ngOnInit(): void {
    this.loadOrderDetail();
  }

  /**
   * 加载工单详情
   */
  loadOrderDetail(): void {
    // TODO: 调用后端API获取工单详情
    console.log('工单详情已加载');
  }

  /**
   * 更新工单状态
   */
  updateOrderStatus(status: string): void {
    this.msgSrv.success(`工单状态已更新为: ${status}`);
    // TODO: 实现状态更新逻辑
  }

  /**
   * 获取优先级标签颜色
   */
  getPriorityColor(priority: string): string {
    switch (priority) {
      case 'high': return 'red';
      case 'medium': return 'orange';
      case 'low': return 'green';
      default: return 'default';
    }
  }

  /**
   * 获取状态标签颜色
   */
  getStatusColor(status: string): string {
    switch (status) {
      case 'pending': return 'default';
      case 'processing': return 'blue';
      case 'resolved': return 'green';
      default: return 'default';
    }
  }
}
