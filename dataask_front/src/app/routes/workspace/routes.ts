import { Routes } from '@angular/router';

import { WorkspaceMonitorComponent } from './monitor/monitor.component';
import { WorkspaceReportComponent } from './report/report.component';
import { WorkspaceWorkbenchComponent } from './workbench/workbench.component';

export const routes: Routes = [
  { path: '', redirectTo: 'workbench', pathMatch: 'full' },
  { path: 'monitor', component: WorkspaceMonitorComponent, data: { title: '系统监控' } },
  { path: 'workbench', component: WorkspaceWorkbenchComponent, data: { title: '个人工作台' } },
  { path: 'report', component: WorkspaceReportComponent, data: { title: '工作报表' } }
];
