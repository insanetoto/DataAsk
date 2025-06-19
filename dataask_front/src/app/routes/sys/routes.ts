import { Routes } from '@angular/router';
import { SysOrgComponent } from './org/org.component';
import { SysUerComponent } from './uer/uer.component';
import { SysRoleComponent } from './role/role.component';
import { SysPermissionComponent } from './permission/permission.component';

export const routes: Routes = [

  { path: 'org', component: SysOrgComponent },
  { path: 'uer', component: SysUerComponent },
  { path: 'role', component: SysRoleComponent },
  { path: 'permission', component: SysPermissionComponent }];

