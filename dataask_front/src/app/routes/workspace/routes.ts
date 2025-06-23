import { Routes } from '@angular/router';

import { WorkspaceMonitorComponent } from './monitor/monitor.component';
import { WorkspaceWorkbenchComponent } from './workbench/workbench.component';

export const routes: Routes = [
  { path: 'monitor', component: WorkspaceMonitorComponent },
  { path: 'workbench', component: WorkspaceWorkbenchComponent }
];
