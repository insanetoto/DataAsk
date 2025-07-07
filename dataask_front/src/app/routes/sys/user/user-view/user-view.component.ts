import { Location } from '@angular/common';
import { Component, OnInit, inject } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { _HttpClient } from '@delon/theme';
import { SHARED_IMPORTS } from '@shared';
import { NzMessageService } from 'ng-zorro-antd/message';

import { SysUserService, User } from '../user.service';

@Component({
  selector: 'app-sys-user-view',
  imports: [...SHARED_IMPORTS],
  templateUrl: './user-view.component.html',
  styleUrl: './user-view.component.less'
})
export class SysUserViewComponent implements OnInit {
  private readonly http = inject(_HttpClient);
  private readonly msgSrv = inject(NzMessageService);
  private readonly userService = inject(SysUserService);
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);
  private readonly location = inject(Location);

  i: User | null = null;
  loading = true;
  userId: number | null = null;

  ngOnInit(): void {
    // 从路由参数获取用户ID
    this.route.params.subscribe(params => {
      const id = params['id'];
      if (id && !isNaN(+id)) {
        this.userId = +id;
        this.loadUserDetail();
      } else {
        this.msgSrv.error('无效的用户ID');
        this.goBack();
      }
    });
  }

  /**
   * 加载用户详情
   */
  loadUserDetail(): void {
    if (!this.userId) {
      this.msgSrv.error('用户ID不存在');
      this.goBack();
      return;
    }

    this.loading = true;
    this.userService.getUserById(this.userId).subscribe({
      next: res => {
        this.loading = false;
        if (res.success || res.code === 200) {
          this.i = res.data || res;
        } else {
          this.msgSrv.error(res.message || '获取用户信息失败');
        }
      },
      error: () => {
        this.loading = false;
        this.msgSrv.error('获取用户信息失败');
      }
    });
  }

  /**
   * 获取机构名称
   */
  getOrgName(user: User): string {
    if (!user) return '-';

    // 优先使用organization对象中的org_name
    if (user.organization?.org_name) {
      return `${user.organization.org_name} (${user.org_code})`;
    }

    // 其次使用直接的org_name字段
    if ((user as any).org_name) {
      return `${(user as any).org_name} (${user.org_code})`;
    }

    // 最后显示org_code
    return user.org_code || '-';
  }

  /**
   * 获取角色名称
   */
  getRoleName(user: User): string {
    if (!user) return '-';

    // 优先使用role对象中的role_name
    if (user.role?.role_name) {
      return user.role.role_name;
    }

    // 其次使用直接的role_name字段
    if ((user as any).role_name) {
      return (user as any).role_name;
    }

    // 最后使用role_code映射
    const roleCode = (user as any).role_code || user.role?.role_code;
    if (roleCode) {
      const roleMap: Record<string, string> = {
        SUPER_ADMIN: '超级系统管理员',
        ORG_ADMIN: '机构管理员',
        NORMAL_USER: '普通用户'
      };
      return roleMap[roleCode] || roleCode;
    }

    return '-';
  }

  /**
   * 编辑用户
   */
  editUser(): void {
    if (this.userId) {
      this.router.navigate(['/sys/user/edit', this.userId]);
    }
  }

  /**
   * 返回用户列表
   */
  goBack(): void {
    this.router.navigate(['/sys/user']);
  }
}
