import { Routes } from '@angular/router';

import { SysOrgComponent } from './org/org.component';
import { SysPermissionComponent } from './permission/permission.component';
import { SysRoleComponent } from './role/role.component';
import { SysUserComponent } from './user/user.component';

export const routes: Routes = [
  { path: 'user', component: SysUserComponent },
  { path: 'org', component: SysOrgComponent },
  { path: 'role', component: SysRoleComponent },
  { path: 'permission', component: SysPermissionComponent }
];
