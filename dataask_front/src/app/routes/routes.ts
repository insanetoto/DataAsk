import { Routes } from '@angular/router';
import { startPageGuard } from '@core';
import { authSimpleCanActivate, authSimpleCanActivateChild } from '@delon/auth';

import { LayoutBasicComponent } from '../layout';
import { DashboardComponent } from './dashboard/dashboard.component';

export const routes: Routes = [
  {
    path: '',
    component: LayoutBasicComponent,
    canActivate: [startPageGuard, authSimpleCanActivate],
    canActivateChild: [authSimpleCanActivateChild],
    data: {},
    children: [
      { path: '', redirectTo: 'dashboard', pathMatch: 'full' },
      { path: 'dashboard', component: DashboardComponent, data: { title: 'AI监控大屏' } },
      { path: 'sys', loadChildren: () => import('./sys/routes').then(m => m.routes) },
      { path: 'portal', loadChildren: () => import('./portal/routes').then(m => m.routes) },
      { path: 'ai-engine', loadChildren: () => import('./ai-engine/routes').then(m => m.routes) },
      { path: 'workspace', loadChildren: () => import('./workspace/routes').then(m => m.routes) }
    ,  { path: 'ai-app', loadChildren: () => import('./ai-app/routes').then((m) => m.routes) },  { path: 'customer-service', loadChildren: () => import('./customer-service/routes').then((m) => m.routes) }]
  },
  // passport
  { path: '', loadChildren: () => import('./passport/routes').then(m => m.routes) },
  { path: 'exception', loadChildren: () => import('./exception/routes').then(m => m.routes) },
  { path: '**', redirectTo: 'exception/404' }
];
