import { Routes } from '@angular/router';

import { CustomerServiceServiceDashboardComponent } from './service-dashboard/service-dashboard.component';
import { CustomerServiceServiceWorkbenchComponent } from './service-workbench/service-workbench.component';
import { CustomerServiceServiceOrderDetailComponent } from './service-order-detail/service-order-detail.component';

export const routes: Routes = [
  { path: 'dashboard', component: CustomerServiceServiceDashboardComponent, data: { title: '客服仪表板' } },
  { path: 'workbench', component: CustomerServiceServiceWorkbenchComponent, data: { title: '客服工作台' } },
  { path: 'order-detail', component: CustomerServiceServiceOrderDetailComponent, data: { title: '服务工单详情' } }
];

