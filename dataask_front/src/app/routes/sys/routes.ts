import { Routes } from '@angular/router';
import { aclCanActivate } from '@delon/acl';

import { SysMessageComponent } from './message/message.component';
import { SysOrgComponent } from './org/org.component';
import { SysPermissionComponent } from './permission/permission.component';
import { SysRoleComponent } from './role/role.component';
import { SysRestPasswdComponent } from './user/rest-passwd/rest-passwd.component';
import { SysUserEditComponent } from './user/user-edit/user-edit.component';
import { SysUserViewComponent } from './user/user-view/user-view.component';
import { SysUserComponent } from './user/user.component';
import { SysWorkflowComponent } from './workflow/workflow.component';

export const routes: Routes = [
  { path: 'user', component: SysUserComponent, data: { title: '用户管理' } },
  { path: 'user/view/:id', component: SysUserViewComponent, data: { title: '用户详情' } },
  { path: 'user/edit/:id', component: SysUserEditComponent, data: { title: '编辑用户' } },
  { path: 'user/edit/new', component: SysUserEditComponent, data: { title: '新增用户' } },
  {
    path: 'user/reset-password/:id',
    component: SysRestPasswdComponent,
    canActivate: [aclCanActivate],
    data: {
      title: '重置密码',
      guard: { role: ['SUPER_ADMIN', 'ORG_ADMIN'], mode: 'oneOf' },
      guard_url: '/exception/403'
    }
  },
  { path: 'org', component: SysOrgComponent, data: { title: '机构管理' } },
  { path: 'role', component: SysRoleComponent, data: { title: '角色管理' } },
  { path: 'permission', component: SysPermissionComponent, data: { title: '权限管理' } },
  { path: 'workflow', component: SysWorkflowComponent, data: { title: '工作流管理' } },
  { path: 'message', component: SysMessageComponent, data: { title: '消息管理' } }
];
