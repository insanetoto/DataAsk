import { ChangeDetectorRef, Component, OnInit, inject } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { SettingsService } from '@delon/theme';
import { SHARED_IMPORTS } from '@shared';
import { NzMessageService } from 'ng-zorro-antd/message';
import { finalize } from 'rxjs';

import { SysPermissionService, Permission } from '../permission.service';

@Component({
  selector: 'app-sys-permission-view',
  imports: [...SHARED_IMPORTS],
  templateUrl: './permission-view.component.html'
})
export class SysPermissionViewComponent implements OnInit {
  private readonly msg = inject(NzMessageService);
  private readonly cdr = inject(ChangeDetectorRef);
  private readonly permissionService = inject(SysPermissionService);
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);
  private readonly settings = inject(SettingsService);

  permissionId: number | null = null;
  permissionData: Permission | null = null;
  loading = false;

  // 当前用户信息
  get currentUser() {
    return this.settings.user;
  }

  get currentUserRoleCode() {
    return this.currentUser?.roleCode || this.currentUser?.role_code || '';
  }

  // 资源类型映射
  resourceTypeMap = new Map([
    ['user', '用户管理'],
    ['role', '角色管理'],
    ['permission', '权限管理'],
    ['organization', '机构管理'],
    ['system', '系统管理'],
    ['ai-engine', 'AI引擎'],
    ['workspace', '工作空间']
  ]);

  ngOnInit(): void {
    this.checkRouteParams();
  }

  private checkRouteParams(): void {
    this.route.params.subscribe(params => {
      const id = params['id'];
      if (id && !isNaN(+id)) {
        this.permissionId = +id;
        this.loadPermissionDetail();
      } else {
        this.msg.error('无效的权限ID');
        this.goBack();
      }
    });
  }

  private loadPermissionDetail(): void {
    if (!this.permissionId) {
      this.msg.error('权限ID不存在');
      this.goBack();
      return;
    }

    this.loading = true;

    this.permissionService
      .getPermissionById(this.permissionId)
      .pipe(
        finalize(() => {
          this.loading = false;
          this.cdr.detectChanges();
        })
      )
      .subscribe({
        next: res => {
          if ((res.code && res.code >= 200 && res.code < 300) || res.success === true) {
            this.permissionData = res.data || res;
          } else {
            this.msg.error(res.message || '获取权限信息失败');
            this.goBack();
          }
        },
        error: () => {
          this.msg.error('获取权限信息失败');
          this.goBack();
        }
      });
  }

  /**
   * 检查是否可以编辑权限
   */
  canEditPermission(): boolean {
    const currentRole = this.currentUserRoleCode;
    // 只有超级管理员可以编辑权限
    return currentRole === 'SUPER_ADMIN';
  }

  getResourceTypeName(resourceType: string | undefined): string {
    if (!resourceType) return '未分类';
    return this.resourceTypeMap.get(resourceType) || resourceType || '未知';
  }

  getStatusText(status: number): string {
    return status === 1 ? '启用' : '禁用';
  }

  editPermission(): void {
    if (this.permissionId) {
      this.router.navigate(['/sys/permission/edit', this.permissionId]);
    }
  }

  goBack(): void {
    this.router.navigate(['/sys/permission']);
  }
}
