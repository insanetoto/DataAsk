import { ChangeDetectorRef, Component, OnInit, inject } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { SettingsService } from '@delon/theme';
import { SHARED_IMPORTS } from '@shared';
import { NzMessageService } from 'ng-zorro-antd/message';
import { finalize } from 'rxjs';

import { SysRoleService } from '../role.service';

// 定义类型接口
interface RoleLevelOption {
  label: string;
  value: number;
}

@Component({
  selector: 'app-sys-role-edit',
  imports: [...SHARED_IMPORTS],
  templateUrl: './role-edit.component.html',
})
export class SysRoleEditComponent implements OnInit {
  private readonly msg = inject(NzMessageService);
  private readonly cdr = inject(ChangeDetectorRef);
  private readonly roleService = inject(SysRoleService);
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);
  private readonly fb = inject(FormBuilder);
  private readonly settings = inject(SettingsService);

  form!: FormGroup;
  roleId: number | null = null;
  isNew = false;
  loading = false;
  submitting = false;

  // 角色等级选项
  roleLevelOptions: RoleLevelOption[] = [];

  // 当前用户信息
  get currentUser() {
    return this.settings.user;
  }

  get currentUserRoleCode() {
    // 后端API返回的字段名是 roleCode，不是 role_code
    return this.currentUser?.roleCode || this.currentUser?.role_code || '';
  }

  ngOnInit(): void {
    this.initForm();
    this.loadRoleLevelOptions();
    this.checkRouteParams();
  }

  private initForm(): void {
    this.form = this.fb.group({
      role_code: ['', [
        Validators.required, 
        Validators.pattern(/^[A-Z_]+$/),
        Validators.minLength(2),
        Validators.maxLength(50)
      ]],
      role_name: ['', [
        Validators.required,
        Validators.minLength(2),
        Validators.maxLength(100)
      ]],
      role_level: [null, [Validators.required]],
      description: ['', [Validators.maxLength(500)]],
      status: [1, [Validators.required]]
    });
  }

  private loadRoleLevelOptions(): void {
    const currentRole = this.currentUserRoleCode;
    
    if (currentRole === 'SUPER_ADMIN') {
      // 超级管理员可以创建所有等级的角色
      this.roleLevelOptions = this.roleService.getRoleLevelOptions();
    } else if (currentRole === 'ORG_ADMIN') {
      // 机构管理员只能创建机构管理员和普通用户角色
      this.roleLevelOptions = this.roleService.getRoleLevelOptions().filter(
        option => option.value !== 1 // 过滤掉超级管理员
      );
    } else {
      // 其他角色没有权限
      this.roleLevelOptions = [];
      this.msg.warning('您没有权限管理角色');
      this.goBack();
    }
  }

  private checkRouteParams(): void {
    this.route.params.subscribe(params => {
      const id = params['id'];
      if (id === 'new') {
        this.isNew = true;
        // 新增模式下不需要角色编码验证
        this.form.get('role_code')?.setValidators([Validators.required, Validators.pattern(/^[A-Z_]+$/)]);
        this.form.get('role_code')?.updateValueAndValidity();
      } else if (id && !isNaN(+id)) {
        this.roleId = +id;
        this.isNew = false;
        // 编辑模式下角色编码不可修改
        this.form.get('role_code')?.setValidators([Validators.required]);
        this.form.get('role_code')?.updateValueAndValidity();
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

    this.roleService.getRoleById(this.roleId).subscribe({
      next: res => {
        this.loading = false;

        if ((res.code && res.code >= 200 && res.code < 300) || res.success === true) {
          const roleData = res.data || res;

          this.form.patchValue(roleData);
          // 编辑模式下角色编码不可修改
          this.form.get('role_code')?.disable();
        } else {
          this.msg.error(res.message || '获取角色信息失败');
          this.goBack();
        }
        this.cdr.detectChanges();
      },
      error: () => {
        this.loading = false;
        this.msg.error('获取角色信息失败');
        this.goBack();
        this.cdr.detectChanges();
      }
    });
  }

  submit(): void {
    if (this.form.invalid) {
      Object.values(this.form.controls).forEach(control => {
        if (control.invalid) {
          control.markAsDirty();
          control.updateValueAndValidity({ onlySelf: true });
        }
      });
      return;
    }

    this.submitting = true;

    const formData = { ...this.form.value };
    
    // 如果是编辑模式，需要包含角色编码（因为表单中被禁用了）
    if (!this.isNew && this.form.get('role_code')?.disabled) {
      formData.role_code = this.form.get('role_code')?.value;
    }

    const request$ = this.isNew
      ? this.roleService.createRole(formData)
      : this.roleService.updateRole(this.roleId!, formData);

    request$
      .pipe(
        finalize(() => {
          this.submitting = false;
          this.cdr.detectChanges();
        })
      )
      .subscribe({
        next: res => {
          if ((res.code && res.code >= 200 && res.code < 300) || res.success === true) {
            this.msg.success(this.isNew ? '角色创建成功' : '角色更新成功');
            this.goBack();
          } else {
            this.msg.error(res.message || (this.isNew ? '创建角色失败' : '更新角色失败'));
          }
        },
        error: () => {
          this.msg.error(this.isNew ? '创建角色失败' : '更新角色失败');
        }
      });
  }

  goBack(): void {
    this.router.navigate(['/sys/role']);
  }
}
