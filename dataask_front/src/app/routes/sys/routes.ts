import { Routes } from '@angular/router';

import { SysMessageComponent } from './message/message.component';
import { SysOrgComponent } from './org/org.component';
import { SysPermissionComponent } from './permission/permission.component';
import { SysRoleComponent } from './role/role.component';
import { SysUserComponent } from './user/user.component';
import { SysWorkflowComponent } from './workflow/workflow.component';

export const routes: Routes = [
  { path: 'user', component: SysUserComponent, data: { title: '用户管理' } },
  { path: 'org', component: SysOrgComponent, data: { title: '机构管理' } },
  { path: 'role', component: SysRoleComponent, data: { title: '角色管理' } },
  { path: 'permission', component: SysPermissionComponent, data: { title: '权限管理' } },
  { path: 'workflow', component: SysWorkflowComponent, data: { title: '工作流管理' } },
  { path: 'message', component: SysMessageComponent, data: { title: '消息管理' } }
];
