import { Routes } from '@angular/router';
import { startPageGuard } from '@core';
import { authSimpleCanActivate, authSimpleCanActivateChild } from '@delon/auth';

import { LayoutBasicComponent } from '../layout';
import { DashboardComponent } from './dashboard/dashboard.component';
import { DataSourceComponent } from './data-source/data-source.component';
import { HomeComponent } from './home/home.component';
import { IntelligentQaComponent } from './intelligent-qa/intelligent-qa.component';
import { IntelligentTrainingComponent } from './intelligent-training/intelligent-training.component';
import { KnowledgeBaseComponent } from './knowledge-base/knowledge-base.component';
import { PersonalWorkspaceComponent } from './personal-workspace/personal-workspace.component';

export const routes: Routes = [
  {
    path: '',
    component: LayoutBasicComponent,
    canActivate: [startPageGuard, authSimpleCanActivate],
    canActivateChild: [authSimpleCanActivateChild],
    data: {},
    children: [
      { path: '', redirectTo: 'home', pathMatch: 'full' },
      { path: 'home', component: HomeComponent },
      { path: 'dashboard', component: DashboardComponent },
      { path: 'personal-workspace', component: PersonalWorkspaceComponent },
      { path: 'data-source', component: DataSourceComponent },
      { path: 'intelligent-qa', component: IntelligentQaComponent },
      { path: 'intelligent-training', component: IntelligentTrainingComponent },
      { path: 'knowledge-base', component: KnowledgeBaseComponent },
      { 
        path: 'system-management', 
        loadChildren: () => import('./system-management/system-management.routes').then(m => m.systemManagementRoutes) 
      }
    ]
  },
  // passport
  { path: '', loadChildren: () => import('./passport/routes').then(m => m.routes) },
  { path: 'exception', loadChildren: () => import('./exception/routes').then(m => m.routes) },
  { path: '**', redirectTo: 'exception/404' }
];
