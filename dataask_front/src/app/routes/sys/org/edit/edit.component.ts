import { ChangeDetectorRef, Component, OnInit, inject } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { SettingsService } from '@delon/theme';
import { SHARED_IMPORTS } from '@shared';
import { NzMessageService } from 'ng-zorro-antd/message';
import { finalize } from 'rxjs';

import { SysOrgService } from '../org.service';

// 定义类型接口
interface OrganizationOption {
  id: number;
  org_code: string;
  org_name: string;
  level_depth: number;
}

@Component({
  selector: 'app-sys-org-edit',
  templateUrl: './edit.component.html',
  imports: [...SHARED_IMPORTS]
})
export class SysEditComponent implements OnInit {
  private readonly msg = inject(NzMessageService);
  private readonly cdr = inject(ChangeDetectorRef);
  private readonly orgService = inject(SysOrgService);
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);
  private readonly fb = inject(FormBuilder);
  private readonly settings = inject(SettingsService);

  form!: FormGroup;
  orgId: number | null = null;
  isNew = false;
  loading = false;
  submitting = false;

  // 使用更好的类型定义
  parentOrgOptions: OrganizationOption[] = [];

  // 当前用户信息
  get currentUser() {
    return this.settings.user;
  }

  get currentUserRoleCode() {
    const user = this.currentUser;
    return user?.roleCode || user?.role_code || user?.role?.role_code || '';
  }

  get currentUserOrgCode() {
    const user = this.currentUser;
    return user?.orgCode || user?.org_code || user?.organization?.org_code || '';
  }

  get currentUserOrgName() {
    const user = this.currentUser;
    return user?.orgName || user?.org_name || user?.organization?.org_name || '';
  }

  ngOnInit(): void {
    this.initForm();
    this.checkRouteParams();
  }

  private initForm(): void {
    this.form = this.fb.group({
      org_code: [''], // 新增时不需要，编辑时会被设置
      org_name: ['', [Validators.required]],
      parent_org_code: [''], // 暂时设为可选，后续根据用户权限调整
      contact_person: ['', [Validators.required]],
      contact_phone: ['', [Validators.required, Validators.pattern(/^1[3-9]\d{9}$/)]],
      contact_email: ['', [Validators.required, Validators.email]],
      status: [1]
    });

    // 根据用户权限动态设置上级机构字段的验证规则
    this.updateParentOrgValidation();
  }

  private updateParentOrgValidation(): void {
    const currentUser = this.currentUser;
    
    // 更智能的超级管理员判断
    const isAdmin =
      this.currentUserRoleCode === 'SUPER_ADMIN' ||
      currentUser?.role_code === 'SUPER_ADMIN' ||
      currentUser?.role?.role_code === 'SUPER_ADMIN' ||
      currentUser?.username === 'admin' ||
      currentUser?.username === '超级管理员' ||
      currentUser?.user_code === 'admin';

    if (isAdmin) {
      // 超级管理员：上级机构可选
      this.form.get('parent_org_code')?.clearValidators();
    } else {
      // 其他角色：上级机构必填
      this.form.get('parent_org_code')?.setValidators([Validators.required]);
    }
    
    this.form.get('parent_org_code')?.updateValueAndValidity();
  }

  private checkRouteParams(): void {
    this.route.params.subscribe(params => {
      const id = params['id'];
      if (id === 'new') {
        this.isNew = true;
        // 新增模式下不需要机构编码验证
        this.form.get('org_code')?.clearValidators();
        this.form.get('org_code')?.updateValueAndValidity();

        // 加载选项数据
        this.loadOptions();

        // 如果是机构管理员，自动设置上级机构编码
        this.setDefaultParentOrgCode();
      } else if (id && !isNaN(+id)) {
        this.orgId = +id;
        this.isNew = false;
        // 编辑模式下需要机构编码验证
        this.form.get('org_code')?.setValidators([Validators.required]);
        this.form.get('org_code')?.updateValueAndValidity();

        // 加载选项数据
        this.loadOptions();

        this.loadOrgDetail();
      } else {
        this.msg.error('无效的机构ID');
        this.goBack();
      }
    });
  }

  private setDefaultParentOrgCode(): void {
    const currentRole = this.currentUserRoleCode;
    const currentOrgCode = this.currentUserOrgCode;
    const currentUser = this.currentUser;

    // 更智能的超级管理员判断
    const isAdmin =
      currentRole === 'SUPER_ADMIN' ||
      currentUser?.role_code === 'SUPER_ADMIN' ||
      currentUser?.role?.role_code === 'SUPER_ADMIN' ||
      currentUser?.username === 'admin' ||
      currentUser?.username === '超级管理员' ||
      currentUser?.user_code === 'admin';

    if (isAdmin) {
      // 超级管理员：上级机构字段设为可选
      this.form.get('parent_org_code')?.clearValidators();
      this.form.get('parent_org_code')?.updateValueAndValidity();
      // 设置为空，让用户自己选择
      this.form.patchValue({
        parent_org_code: ''
      });
    } else if (currentRole === 'ORG_ADMIN' && currentOrgCode) {
      // 机构管理员只能选择自己的机构作为上级机构
      this.form.patchValue({
        parent_org_code: currentOrgCode
      });
      // 设置为只读，防止修改
      this.form.get('parent_org_code')?.disable();
    } else {
      // 其他角色也只能选择当前用户的机构
      if (currentOrgCode) {
        this.form.patchValue({
          parent_org_code: currentOrgCode
        });
        // 设置为只读，防止修改
        this.form.get('parent_org_code')?.disable();
      }
    }
  }

  private loadOptions(): void {
    this.loadParentOrgOptions();
  }

  private loadParentOrgOptions(): void {
    const currentRole = this.currentUserRoleCode;
    const currentOrgCode = this.currentUserOrgCode;



    if (currentRole === 'SUPER_ADMIN') {
      // 超级管理员可以选择所有机构作为上级机构
      this.orgService.getOrganizations({ pi: 1, ps: 1000, status: 1 }).subscribe({
        next: res => {
          if ((res.code && res.code >= 200 && res.code < 300) || res.success === true) {
            // 获取机构列表并过滤掉当前编辑的机构（避免循环引用）
            let orgList = res.data?.list || res.data?.items || res.data || [];

            // 如果是编辑模式，过滤掉当前机构和其子机构
            if (!this.isNew && this.orgId) {
              const currentEditOrgCode = this.form.get('org_code')?.value;
              if (currentEditOrgCode) {
                orgList = orgList.filter((org: any) => {
                  // 过滤掉当前编辑的机构
                  if (org.org_code === currentEditOrgCode) {
                    return false;
                  }
                  // 过滤掉以当前机构编码开头的子机构（避免循环引用）
                  if (org.org_code.startsWith(currentEditOrgCode)) {
                    return false;
                  }
                  return true;
                });
              }
            }

            this.parentOrgOptions = orgList;
          } else {
            this.handleParentOrgLoadError();
          }
          this.cdr.detectChanges();
        },
        error: error => {
          // 检查是否是被HTTP拦截器误判的成功响应
          if (error.status === 200 && error.ok && error.body) {
            if (error.body.success === true || error.body.code === 200) {
              let orgList = error.body.data?.list || error.body.data?.items || error.body.data || [];

              // 如果是编辑模式，过滤掉当前机构和其子机构
              if (!this.isNew && this.orgId) {
                const currentEditOrgCode = this.form.get('org_code')?.value;
                if (currentEditOrgCode) {
                  orgList = orgList.filter((org: any) => {
                    if (org.org_code === currentEditOrgCode) {
                      return false;
                    }
                    if (org.org_code.startsWith(currentEditOrgCode)) {
                      return false;
                    }
                    return true;
                  });
                }
              }

              this.parentOrgOptions = orgList;
              this.cdr.detectChanges();
              return;
            }
          }
          this.handleParentOrgLoadError();
        }
      });
    } else if (currentOrgCode) {
      // 机构管理员和其他角色：如果有机构编码但没有机构名称，从API获取
      if (this.currentUserOrgName) {
        // 如果已有机构名称，直接使用
        this.parentOrgOptions = [
          {
            id: this.currentUser.id || 0,
            org_code: currentOrgCode,
            org_name: this.currentUserOrgName,
            level_depth: this.currentUser.level_depth || 0
          }
        ];
        this.cdr.detectChanges();
      } else {
        // 没有机构名称，从API获取机构信息
        this.loadCurrentUserOrgInfo(currentOrgCode);
      }
    } else {
      // 如果没有机构编码，显示错误
      this.handleParentOrgLoadError();
    }
  }

  private loadCurrentUserOrgInfo(orgCode: string): void {
    console.log('正在获取机构信息:', orgCode);
    
    this.orgService.getOrganizationByCode(orgCode).subscribe({
      next: res => {
        console.log('机构信息响应:', res);
        
        if (res.success && res.data) {
          const orgInfo = res.data;
          this.parentOrgOptions = [
            {
              id: orgInfo.id || 0,
              org_code: orgInfo.org_code,
              org_name: orgInfo.org_name,
              level_depth: orgInfo.level_depth || 0
            }
          ];
          
          // 设置默认上级机构为当前用户机构
          this.form.patchValue({
            parent_org_code: orgCode
          });
          this.form.get('parent_org_code')?.disable();
          
          console.log('成功加载机构信息:', this.parentOrgOptions);
        } else {
          this.handleParentOrgLoadError();
        }
        this.cdr.detectChanges();
      },
      error: error => {
        console.error('获取机构信息失败:', error);
        
        // 检查是否是被HTTP拦截器误判的成功响应
        if (error.status === 200 && error.ok && error.body) {
          if (error.body.success === true && error.body.data) {
            const orgInfo = error.body.data;
            this.parentOrgOptions = [
              {
                id: orgInfo.id || 0,
                org_code: orgInfo.org_code,
                org_name: orgInfo.org_name,
                level_depth: orgInfo.level_depth || 0
              }
            ];
            
            this.form.patchValue({
              parent_org_code: orgCode
            });
            this.form.get('parent_org_code')?.disable();
            
            this.cdr.detectChanges();
            return;
          }
        }
        
        this.handleParentOrgLoadError();
      }
    });
  }

  private handleParentOrgLoadError(): void {
    const currentRole = this.currentUserRoleCode;
    const currentOrgCode = this.currentUserOrgCode;
    const currentUser = this.currentUser;

    // 打印调试信息
    console.log('handleParentOrgLoadError 调试信息:', {
      currentRole,
      currentOrgCode,
      currentUser
    });

    // 更智能的超级管理员判断：检查多种可能的字段
    const isAdmin =
      currentRole === 'SUPER_ADMIN' ||
      currentUser?.role_code === 'SUPER_ADMIN' ||
      currentUser?.role?.role_code === 'SUPER_ADMIN' ||
      currentUser?.username === 'admin' ||
      currentUser?.username === '超级管理员' ||
      currentUser?.user_code === 'admin';

    if (isAdmin) {
      // 超级管理员：即使加载失败，也提供空选项让用户操作
      this.parentOrgOptions = [];
      this.msg.warning('暂时无法加载机构列表，您可以手动输入上级机构编码或留空创建顶级机构');
      
      // 对于超级管理员，上级机构字段设为可选
      this.form.get('parent_org_code')?.clearValidators();
      this.form.get('parent_org_code')?.updateValueAndValidity();
    } else {
      // 机构管理员和其他角色：如果有当前用户机构信息，使用它
      if (currentOrgCode && this.currentUserOrgName) {
        this.parentOrgOptions = [
          {
            id: this.currentUser.id || 0,
            org_code: currentOrgCode,
            org_name: this.currentUserOrgName,
            level_depth: this.currentUser.level_depth || 0
          }
        ];
      } else {
        // 如果没有用户机构信息，显示错误
        this.parentOrgOptions = [];
        this.msg.error('无法获取用户机构信息，请重新登录');
      }
    }
    this.cdr.detectChanges();
  }

  private loadOrgDetail(): void {
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
          const orgData = res.data || res;

          this.form.patchValue(orgData);
          // 编辑模式下机构编码不可修改
          this.form.get('org_code')?.disable();
        } else {
          this.msg.error(res.message || '获取机构信息失败');
          this.goBack();
        }
        this.cdr.detectChanges();
      },
      error: () => {
        this.loading = false;
        this.msg.error('获取机构信息失败');
        this.goBack();
        this.cdr.detectChanges();
      }
    });
  }

  submit(): void {
    // 标记所有字段为dirty来触发验证
    Object.keys(this.form.controls).forEach(key => {
      const control = this.form.controls[key];
      if (control.invalid) {
        control.markAsDirty();
        control.updateValueAndValidity({ onlySelf: true });
      }
    });

    if (this.form.invalid) {
      return;
    }

    this.submitting = true;
    const formData = this.form.getRawValue();

    // 如果是新增模式，删除org_code字段（系统自动生成）
    if (this.isNew) {
      delete formData.org_code;
    }

    const request = this.isNew ? this.orgService.createOrganization(formData) : this.orgService.updateOrganization(this.orgId!, formData);

    request
      .pipe(
        finalize(() => {
          this.submitting = false;
          this.cdr.detectChanges();
        })
      )
      .subscribe({
        next: res => {
          if ((res.code && res.code >= 200 && res.code < 300) || res.success === true) {
            this.msg.success(this.isNew ? '创建成功' : '更新成功');
            this.goBack();
          } else {
            this.msg.error(res.message || res.error || '保存失败');
          }
        },
        error: error => {
          this.msg.error(`保存失败: ${error.message || error.error?.message || '未知错误'}`);
        }
      });
  }

  goBack(): void {
    this.router.navigate(['/sys/org']);
  }
}
