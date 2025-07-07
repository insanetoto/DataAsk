import { ChangeDetectionStrategy, ChangeDetectorRef, Component, OnInit, inject } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { SettingsService } from '@delon/theme';
import { SHARED_IMPORTS } from '@shared';
import { NzMessageService } from 'ng-zorro-antd/message';
import { finalize } from 'rxjs';

import { SysUserService } from '../user.service';

// 定义类型接口
interface OrganizationOption {
  id: number;
  org_code: string;
  org_name: string;
}

interface RoleOption {
  id: number;
  role_code: string;
  role_name: string;
}

@Component({
  selector: 'app-sys-user-edit',
  templateUrl: './user-edit.component.html',
  styleUrl: './user-edit.component.less',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [...SHARED_IMPORTS]
})
export class SysUserEditComponent implements OnInit {
  private readonly msg = inject(NzMessageService);
  private readonly cdr = inject(ChangeDetectorRef);
  private readonly userService = inject(SysUserService);
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);
  private readonly fb = inject(FormBuilder);
  private readonly settings = inject(SettingsService);

  form!: FormGroup;
  userId: number | null = null;
  isNew = false;
  loading = false;
  submitting = false;

  // 使用更好的类型定义
  organizationOptions: OrganizationOption[] = [];
  roleOptions: RoleOption[] = [];

  // 当前用户信息
  get currentUser() {
    return this.settings.user;
  }

  get currentUserRoleCode() {
    return this.currentUser?.roleCode || this.currentUser?.role_code || this.currentUser?.role?.role_code;
  }

  get currentUserOrgCode() {
    return this.currentUser?.orgCode || this.currentUser?.org_code || this.currentUser?.organization?.org_code;
  }

  ngOnInit(): void {
    this.initForm();
    this.checkRouteParams();
  }

  private initForm(): void {
    this.form = this.fb.group({
      user_code: [''], // 新增时不需要，编辑时会被设置
      username: ['', [Validators.required]],
      org_code: ['', [Validators.required]],
      role_id: [null, [Validators.required]],
      password: [''],
      phone: ['', [Validators.pattern(/^1[3-9]\d{9}$/)]],
      address: [''],
      status: [1]
    });
  }

  private checkRouteParams(): void {
    this.route.params.subscribe(params => {
      const id = params['id'];
      if (id === 'new') {
        this.isNew = true;
        this.form.get('password')?.setValidators([Validators.required]);
        this.form.get('password')?.updateValueAndValidity();
        // 新增模式下不需要用户编码验证
        this.form.get('user_code')?.clearValidators();
        this.form.get('user_code')?.updateValueAndValidity();

        // 加载选项数据
        this.loadOptions();

        // 如果是机构管理员，自动设置机构编码
        this.setDefaultOrgCodeForNewUser();
      } else if (id && !isNaN(+id)) {
        this.userId = +id;
        this.isNew = false;
        // 编辑模式下需要用户编码验证
        this.form.get('user_code')?.setValidators([Validators.required]);
        this.form.get('user_code')?.updateValueAndValidity();

        // 加载选项数据
        this.loadOptions();

        this.loadUserDetail();
      } else {
        this.msg.error('无效的用户ID');
        this.goBack();
      }
    });
  }

  private setDefaultOrgCodeForNewUser(): void {
    const currentRole = this.currentUserRoleCode;
    const currentOrgCode = this.currentUserOrgCode;

    // 如果是机构管理员，自动设置为当前用户的机构编码
    if (currentRole === 'ORG_ADMIN' && currentOrgCode) {
      this.form.patchValue({
        org_code: currentOrgCode
      });
      // 机构管理员可以选择自己的机构及下级机构，不禁用选择
    }
  }

  private loadOptions(): void {
    this.loadOrganizationOptions();
    this.loadRoleOptions();
  }

  private loadOrganizationOptions(): void {
    const currentRole = this.currentUserRoleCode;
    const currentOrgCode = this.currentUserOrgCode;

    if (currentRole === 'SUPER_ADMIN') {
      // 超级管理员可以选择所有机构
      this.userService.httpClient.get('/organizations', { pi: 1, ps: 1000, status: 1 }).subscribe({
        next: res => {
          if ((res.code && res.code >= 200 && res.code < 300) || res.success === true) {
            this.organizationOptions = res.data?.list || res.data?.items || res.data || [];
          } else {
            this.handleOrganizationLoadError();
          }
          this.cdr.detectChanges();
        },
        error: () => {
          this.handleOrganizationLoadError();
        }
      });
    } else if (currentRole === 'ORG_ADMIN' && currentOrgCode) {
      // 机构管理员只能选择本机构及下级机构
      this.userService.httpClient.get(`/organizations/${currentOrgCode}/children`, { include_self: true }).subscribe({
        next: res => {
          if ((res.code && res.code >= 200 && res.code < 300) || res.success === true) {
            this.organizationOptions = res.data || [];
          } else {
            this.handleOrganizationLoadError();
          }
          this.cdr.detectChanges();
        },
        error: () => {
          this.handleOrganizationLoadError();
        }
      });
    } else {
      // 其他情况使用默认选项
      this.handleOrganizationLoadError();
    }
  }

  private handleOrganizationLoadError(): void {
    // 使用默认选项作为后备
    this.organizationOptions = [
      { id: 1, org_code: '050101', org_name: '总公司' },
      { id: 2, org_code: '050102', org_name: '分公司A' },
      { id: 3, org_code: '050103', org_name: '分公司B' }
    ];
    this.cdr.detectChanges();
  }

  private loadRoleOptions(): void {
    this.userService.httpClient.get('/roles', { pi: 1, ps: 1000, status: 1 }).subscribe({
      next: res => {
        if ((res.code && res.code >= 200 && res.code < 300) || res.success === true) {
          let roles = res.data?.list || res.data?.items || res.data || [];
          // 根据当前用户权限过滤角色选项
          this.roleOptions = this.filterRolesByPermission(roles);
        } else {
          // 使用默认选项作为后备
          this.roleOptions = this.getDefaultRoleOptions();
        }
        this.cdr.detectChanges();
      },
      error: () => {
        // 使用默认选项作为后备
        this.roleOptions = this.getDefaultRoleOptions();
        this.cdr.detectChanges();
      }
    });
  }

  private filterRolesByPermission(roles: RoleOption[]): RoleOption[] {
    const currentRole = this.currentUserRoleCode;

    if (currentRole === 'SUPER_ADMIN') {
      // 超级管理员可以选择所有角色
      return roles;
    } else if (currentRole === 'ORG_ADMIN') {
      // 机构管理员不能选择超级管理员角色
      return roles.filter(
        role => role.role_code !== 'SUPER_ADMIN' && role.role_name !== '超级管理员' && role.role_name !== '超级系统管理员'
      );
    }

    // 其他角色默认只能选择普通用户角色
    return roles.filter(role => role.role_code === 'NORMAL_USER' || role.role_name === '普通用户');
  }

  private getDefaultRoleOptions(): RoleOption[] {
    const currentRole = this.currentUserRoleCode;

    if (currentRole === 'SUPER_ADMIN') {
      return [
        { id: 1, role_code: 'SUPER_ADMIN', role_name: '超级管理员' },
        { id: 2, role_code: 'ORG_ADMIN', role_name: '机构管理员' },
        { id: 3, role_code: 'NORMAL_USER', role_name: '普通用户' }
      ];
    } else if (currentRole === 'ORG_ADMIN') {
      return [
        { id: 2, role_code: 'ORG_ADMIN', role_name: '机构管理员' },
        { id: 3, role_code: 'NORMAL_USER', role_name: '普通用户' }
      ];
    }

    return [{ id: 3, role_code: 'NORMAL_USER', role_name: '普通用户' }];
  }

  private loadUserDetail(): void {
    if (!this.userId) {
      this.msg.error('用户ID不存在');
      this.goBack();
      return;
    }

    this.loading = true;

    this.userService.getUserById(this.userId).subscribe({
      next: res => {
        this.loading = false;

        if (res.success || res.code === 200) {
          const userData = res.data || res;

          this.form.patchValue(userData);
          // 编辑模式下用户编码不可修改
          this.form.get('user_code')?.disable();
        } else {
          this.msg.error(res.message || '获取用户信息失败');
          this.goBack();
        }
        this.cdr.detectChanges();
      },
      error: () => {
        this.loading = false;
        this.msg.error('获取用户信息失败');
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

    // 如果是新增模式，删除user_code字段（系统自动生成）
    if (this.isNew) {
      delete formData.user_code;
    }

    // 如果是编辑模式且没有输入密码，则删除密码字段
    if (!this.isNew && !formData.password) {
      delete formData.password;
    }

    const request = this.isNew ? this.userService.createUser(formData) : this.userService.updateUser(this.userId!, formData);

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
    this.router.navigate(['/sys/user']);
  }
}
