import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';

import { SysOrgComponent } from './org/org.component';
import { SysPermissionComponent } from './permission/permission.component';
import { SysRoleComponent } from './role/role.component';
import { SysUserComponent } from './user/user.component';

export const routes: Routes = [
  { path: 'org', title: '机构管理', component: SysOrgComponent },
  { path: 'user', title: '用户管理', component: SysUserComponent },
  { path: 'role', title: '角色管理', component: SysRoleComponent },
  { path: 'permission', title: '权限管理', component: SysPermissionComponent }
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule]
})
export class SysRoutingModule {}

