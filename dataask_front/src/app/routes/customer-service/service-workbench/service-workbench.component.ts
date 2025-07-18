import { Component, OnInit, inject } from '@angular/core';
import { _HttpClient } from '@delon/theme';
import { NzMessageService } from 'ng-zorro-antd/message';
import { SHARED_IMPORTS } from '@shared';
import { PageHeaderModule } from '@delon/abc/page-header';
import { NzBreadCrumbModule } from 'ng-zorro-antd/breadcrumb';
import { NzCardModule } from 'ng-zorro-antd/card';
import { NzTableModule } from 'ng-zorro-antd/table';
import { NzButtonModule } from 'ng-zorro-antd/button';
import { NzIconModule } from 'ng-zorro-antd/icon';
import { NzTagModule } from 'ng-zorro-antd/tag';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-customer-service-service-workbench',
  imports: [
    ...SHARED_IMPORTS,
    PageHeaderModule,
    NzBreadCrumbModule,
    NzCardModule,
    NzTableModule,
    NzButtonModule,
    NzIconModule,
    NzTagModule,
    CommonModule
  ],
  templateUrl: './service-workbench.component.html',
  styleUrls: ['./service-workbench.component.less']
})
export class CustomerServiceServiceWorkbenchComponent implements OnInit {
  private readonly http = inject(_HttpClient);
  private readonly msgSrv = inject(NzMessageService);

  // 工作台数据
  workOrders = [
    {
      id: 'WO001',
      customer: '张三',
      type: '技术支持',
      priority: 'high',
      status: 'pending',
      createTime: '2024-01-15 09:30:00',
      description: '系统登录异常，无法正常访问'
    },
    {
      id: 'WO002',
      customer: '李四',
      type: '产品咨询',
      priority: 'medium',
      status: 'processing',
      createTime: '2024-01-15 10:15:00',
      description: '希望了解新功能的使用方法'
    },
    {
      id: 'WO003',
      customer: '王五',
      type: '故障报修',
      priority: 'low',
      status: 'resolved',
      createTime: '2024-01-15 11:00:00',
      description: '数据同步问题已解决'
    }
  ];

  ngOnInit(): void {
    this.loadWorkOrders();
  }

  /**
   * 加载工单列表
   */
  loadWorkOrders(): void {
    // TODO: 调用后端API获取工单数据
    // this.http.get('/api/customer-service/work-orders').subscribe({
    //   next: (data) => {
    //     this.workOrders = data;
    //   },
    //   error: () => {
    //     this.msgSrv.error('加载工单失败');
    //   }
    // });
    
    console.log('工单数据已加载');
  }

  /**
   * 处理工单
   */
  handleOrder(orderId: string): void {
    this.msgSrv.success(`开始处理工单 ${orderId}`);
    // TODO: 实现工单处理逻辑
  }

  /**
   * 查看工单详情
   */
  viewOrderDetail(orderId: string): void {
    this.msgSrv.info(`查看工单 ${orderId} 详情`);
    // TODO: 跳转到工单详情页面
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
