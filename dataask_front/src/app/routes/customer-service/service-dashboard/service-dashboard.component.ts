import { CommonModule } from '@angular/common';
import { Component, OnInit, inject } from '@angular/core';
import { PageHeaderModule } from '@delon/abc/page-header';
import { _HttpClient } from '@delon/theme';
import { NzBreadCrumbModule } from 'ng-zorro-antd/breadcrumb';
import { NzCardModule } from 'ng-zorro-antd/card';
import { NzIconModule } from 'ng-zorro-antd/icon';
import { NzMessageService } from 'ng-zorro-antd/message';
import { NzStatisticModule } from 'ng-zorro-antd/statistic';
import { SHARED_IMPORTS } from '@shared';

@Component({
  selector: 'app-customer-service-service-dashboard',
  imports: [
    CommonModule,
    PageHeaderModule,
    NzBreadCrumbModule,
    NzCardModule,
    NzStatisticModule,
    NzIconModule,
    ...SHARED_IMPORTS
  ],
  templateUrl: './service-dashboard.component.html',
  styleUrls: ['./service-dashboard.component.less']
})
export class CustomerServiceServiceDashboardComponent implements OnInit {
  private readonly http = inject(_HttpClient);
  private readonly msgSrv = inject(NzMessageService);

  // 仪表板数据
  dashboardData = {
    totalCustomers: 1250,
    todayRequests: 89,
    resolvedToday: 76,
    averageResponseTime: 1.5,
    satisfactionRate: 95.8
  };

  ngOnInit(): void {
    this.loadDashboardData();
  }

  /**
   * 加载仪表板数据
   */
  loadDashboardData(): void {
    // TODO: 调用后端API获取仪表板数据
    // this.http.get('/api/customer-service/dashboard').subscribe({
    //   next: (data) => {
    //     this.dashboardData = data;
    //   },
    //   error: () => {
    //     this.msgSrv.error('加载数据失败');
    //   }
    // });
    
    // 模拟数据加载
    console.log('客服仪表板数据已加载');
  }
}
