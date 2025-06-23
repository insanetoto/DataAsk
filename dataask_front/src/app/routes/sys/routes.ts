import { Routes } from '@angular/router';

import { SysOrgComponent } from './org/org.component';
import { SysPermissionComponent } from './permission/permission.component';
import { SysRoleComponent } from './role/role.component';
import { SysUserComponent } from './user/user.component';

export const routes: Routes = [
  { path: 'user', component: SysUserComponent, data: { title: '用户管理' } },
  { path: 'org', component: SysOrgComponent, data: { title: '机构管理' } },
  { path: 'role', component: SysRoleComponent, data: { title: '角色管理' } },
  { path: 'permission', component: SysPermissionComponent, data: { title: '权限管理' } }
];
