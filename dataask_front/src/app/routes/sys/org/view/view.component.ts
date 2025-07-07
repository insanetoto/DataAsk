import { Component, OnInit, inject } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { SHARED_IMPORTS } from '@shared';
import { NzMessageService } from 'ng-zorro-antd/message';

import { SysOrgService, Organization } from '../org.service';

@Component({
  selector: 'app-sys-org-view',
  imports: [...SHARED_IMPORTS],
  templateUrl: './view.component.html'
})
export class SysViewComponent implements OnInit {
  private readonly msg = inject(NzMessageService);
  private readonly orgService = inject(SysOrgService);
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);

  i: Organization | null = null;
  loading = true;
  orgId: number | null = null;

  ngOnInit(): void {
    // 从路由参数获取机构ID
    this.route.params.subscribe(params => {
      const id = params['id'];
      if (id && !isNaN(+id)) {
        this.orgId = +id;
        this.loadOrgDetail();
      } else {
        this.msg.error('无效的机构ID');
        this.goBack();
      }
    });
  }

  /**
   * 加载机构详情
   */
  loadOrgDetail(): void {
    if (!this.orgId) {
      this.msg.error('机构ID不存在');
      this.goBack();
      return;
    }

    this.loading = true;
    this.orgService.getOrganization(this.orgId).subscribe({
      next: res => {
        this.loading = false;
        if (res.success || res.code === 200) {
          this.i = res.data || res;
        } else {
          this.msg.error(res.message || '获取机构信息失败');
          this.goBack();
        }
      },
      error: () => {
        this.loading = false;
        this.msg.error('获取机构信息失败');
        this.goBack();
      }
    });
  }

  /**
   * 获取上级机构名称
   */
  getParentOrgName(org: Organization): string {
    if (!org) return '-';

    // 优先使用parent对象中的org_name
    if (org.parent?.org_name) {
      return `${org.parent.org_name} (${org.parent.org_code})`;
    }

    // 其次使用parent_org_code
    if (org.parent_org_code) {
      return org.parent_org_code;
    }

    return '-';
  }

  /**
   * 获取层级深度描述
   */
  getLevelDescription(org: Organization): string {
    if (!org || org.level_depth === undefined) return '-';

    const level = org.level_depth;
    const levelMap: Record<number, string> = {
      0: '顶级机构',
      1: '一级机构',
      2: '二级机构',
      3: '三级机构',
      4: '四级机构',
      5: '五级机构'
    };

    return levelMap[level] || `${level}级机构`;
  }

  /**
   * 获取状态描述
   */
  getStatusDescription(org: Organization): string {
    if (!org) return '-';
    return org.status === 1 ? '启用' : '禁用';
  }

  /**
   * 获取状态样式
   */
  getStatusColor(org: Organization): string {
    if (!org) return 'default';
    return org.status === 1 ? 'success' : 'error';
  }

  /**
   * 编辑机构
   */
  editOrg(): void {
    if (this.orgId) {
      this.router.navigate(['/sys/org/edit', this.orgId]);
    }
  }

  /**
   * 返回机构列表
   */
  goBack(): void {
    this.router.navigate(['/sys/org']);
  }
}
