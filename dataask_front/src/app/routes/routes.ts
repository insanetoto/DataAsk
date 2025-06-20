import { Routes } from '@angular/router';
import { startPageGuard } from '@core';
import { authSimpleCanActivate, authSimpleCanActivateChild } from '@delon/auth';
import { LayoutBasicComponent } from '../layout';

export const routes: Routes = [
  { path: '', loadChildren: () => import('./passport/routes').then(m => m.routes) },
  {
    path: '',
    component: LayoutBasicComponent,
    canActivate: [startPageGuard, authSimpleCanActivate],
    canActivateChild: [authSimpleCanActivateChild],
    data: {},
    children: [
      { path: '', redirectTo: 'dashboard', pathMatch: 'full' },
      { path: 'dashboard', loadChildren: () => import('./dashboard/routes').then(m => m.routes) },
      { path: 'sys', loadChildren: () => import('./sys/routes').then(m => m.routes) },
      { path: 'workspace', loadChildren: () => import('./workspace/routes').then(m => m.routes) },
      { path: 'ai-workspace', loadChildren: () => import('./ai-workspace/routes').then(m => m.routes) }
    ]
  },
  { path: 'exception', loadChildren: () => import('./exception/routes').then(m => m.routes) },
  { path: '**', redirectTo: 'exception/404' }
];
