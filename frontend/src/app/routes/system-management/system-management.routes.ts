import { Routes } from '@angular/router';

export const systemManagementRoutes: Routes = [
  {
    path: 'organization',
    loadComponent: () => import('./organization/organization.component').then(m => m.OrganizationComponent)
  },
  {
    path: 'role',
    loadComponent: () => import('./role/role.component').then(m => m.RoleComponent)
  },
  {
    path: 'user',
    loadComponent: () => import('./user/user.component').then(m => m.UserComponent)
  },
  {
    path: 'permission',
    loadComponent: () => import('./permission/permission.component').then(m => m.PermissionComponent)
  }
]; 