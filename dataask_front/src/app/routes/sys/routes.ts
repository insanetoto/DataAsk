import { Routes } from '@angular/router';
import { aclCanActivate } from '@delon/acl';

import { SysMessageComponent } from './message/message.component';
import { SysEditComponent } from './org/edit/edit.component';
import { SysOrgComponent } from './org/org.component';
import { SysViewComponent } from './org/view/view.component';
import { SysPermissionEditComponent } from './permission/permission-edit/permission-edit.component';
import { SysPermissionViewComponent } from './permission/permission-view/permission-view.component';
import { SysPermissionComponent } from './permission/permission.component';
import { SysRoleEditComponent } from './role/role-edit/role-edit.component';
import { SysRoleViewComponent } from './role/role-view/role-view.component';
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
  { path: 'org/view/:id', component: SysViewComponent, data: { title: '机构详情' } },
  { path: 'org/edit/:id', component: SysEditComponent, data: { title: '编辑机构' } },
  { path: 'org/edit/new', component: SysEditComponent, data: { title: '新增机构' } },
  {
    path: 'role',
    component: SysRoleComponent,
    canActivate: [aclCanActivate],
    data: {
      title: '角色管理',
      guard: { role: ['SUPER_ADMIN', 'ORG_ADMIN'], mode: 'oneOf' },
      guard_url: '/exception/403'
    }
  },
  {
    path: 'role/view/:id',
    component: SysRoleViewComponent,
    canActivate: [aclCanActivate],
    data: {
      title: '角色详情',
      guard: { role: ['SUPER_ADMIN', 'ORG_ADMIN'], mode: 'oneOf' },
      guard_url: '/exception/403'
    }
  },
  {
    path: 'role/edit/:id',
    component: SysRoleEditComponent,
    canActivate: [aclCanActivate],
    data: {
      title: '编辑角色',
      guard: { role: ['SUPER_ADMIN', 'ORG_ADMIN'], mode: 'oneOf' },
      guard_url: '/exception/403'
    }
  },
  {
    path: 'role/edit/new',
    component: SysRoleEditComponent,
    canActivate: [aclCanActivate],
    data: {
      title: '新增角色',
      guard: { role: ['SUPER_ADMIN', 'ORG_ADMIN'], mode: 'oneOf' },
      guard_url: '/exception/403'
    }
  },
  {
    path: 'permission',
    component: SysPermissionComponent,
    canActivate: [aclCanActivate],
    data: {
      title: '权限管理',
      guard: { role: ['SUPER_ADMIN', 'ORG_ADMIN'], mode: 'oneOf' },
      guard_url: '/exception/403'
    }
  },
  {
    path: 'permission/view/:id',
    component: SysPermissionViewComponent,
    canActivate: [aclCanActivate],
    data: {
      title: '权限详情',
      guard: { role: ['SUPER_ADMIN', 'ORG_ADMIN'], mode: 'oneOf' },
      guard_url: '/exception/403'
    }
  },
  {
    path: 'permission/edit/:id',
    component: SysPermissionEditComponent,
    canActivate: [aclCanActivate],
    data: {
      title: '编辑权限',
      guard: { role: ['SUPER_ADMIN'], mode: 'oneOf' },
      guard_url: '/exception/403'
    }
  },
  {
    path: 'permission/edit/new',
    component: SysPermissionEditComponent,
    canActivate: [aclCanActivate],
    data: {
      title: '新增权限',
      guard: { role: ['SUPER_ADMIN'], mode: 'oneOf' },
      guard_url: '/exception/403'
    }
  },
  { path: 'workflow', component: SysWorkflowComponent, data: { title: '工作流管理' } },
  { path: 'message', component: SysMessageComponent, data: { title: '消息管理' } }
];
