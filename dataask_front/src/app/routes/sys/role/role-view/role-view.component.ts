import { ChangeDetectorRef, Component, OnInit, inject } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { SHARED_IMPORTS } from '@shared';
import { NzMessageService } from 'ng-zorro-antd/message';
import { finalize } from 'rxjs';

import { SysRoleService, Role } from '../role.service';

@Component({
  selector: 'app-sys-role-view',
  imports: [...SHARED_IMPORTS],
  templateUrl: './role-view.component.html',
})
export class SysRoleViewComponent implements OnInit {
  private readonly msg = inject(NzMessageService);
  private readonly cdr = inject(ChangeDetectorRef);
  private readonly roleService = inject(SysRoleService);
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);

  roleId: number | null = null;
  roleData: Role | null = null;
  loading = false;

  // 角色等级选项映射
  roleLevelMap = new Map([
    [1, '超级管理员'],
    [2, '机构管理员'],
    [3, '普通用户']
  ]);

  ngOnInit(): void {
    this.checkRouteParams();
  }

  private checkRouteParams(): void {
    this.route.params.subscribe(params => {
      const id = params['id'];
      if (id && !isNaN(+id)) {
        this.roleId = +id;
        this.loadRoleDetail();
      } else {
        this.msg.error('无效的角色ID');
        this.goBack();
      }
    });
  }

  private loadRoleDetail(): void {
    if (!this.roleId) {
      this.msg.error('角色ID不存在');
      this.goBack();
      return;
    }

    this.loading = true;

    this.roleService.getRoleById(this.roleId)
      .pipe(
        finalize(() => {
          this.loading = false;
          this.cdr.detectChanges();
        })
      )
      .subscribe({
        next: res => {
          if ((res.code && res.code >= 200 && res.code < 300) || res.success === true) {
            this.roleData = res.data || res;
          } else {
            this.msg.error(res.message || '获取角色信息失败');
            this.goBack();
          }
        },
        error: () => {
          this.msg.error('获取角色信息失败');
          this.goBack();
        }
      });
  }

  getRoleLevelName(level: number): string {
    return this.roleLevelMap.get(level) || '未知';
  }

  getStatusText(status: number): string {
    return status === 1 ? '启用' : '禁用';
  }

  editRole(): void {
    if (this.roleId) {
      this.router.navigate(['/sys/role/edit', this.roleId]);
    }
  }

  goBack(): void {
    this.router.navigate(['/sys/role']);
  }
}
