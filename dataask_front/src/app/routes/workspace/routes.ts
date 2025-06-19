import { Routes } from '@angular/router';
import { WorkspaceDashboardComponent } from './dashboard/dashboard.component';
import { WorkspaceWorkplaceComponent } from './workplace/workplace.component';
import { WorkspaceReportComponent } from './report/report.component';

export const routes: Routes = [

  { path: 'dashboard', component: WorkspaceDashboardComponent },
  { path: 'workplace', component: WorkspaceWorkplaceComponent },
  { path: 'report', component: WorkspaceReportComponent }];

