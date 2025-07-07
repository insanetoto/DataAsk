import { ChangeDetectorRef, Component, OnInit, inject } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { SettingsService } from '@delon/theme';
import { SHARED_IMPORTS } from '@shared';
import { NzMessageService } from 'ng-zorro-antd/message';
import { finalize } from 'rxjs';

import { SysPermissionService } from '../permission.service';

// 定义类型接口
interface HttpMethodOption {
  label: string;
  value: string;
}

interface ResourceTypeOption {
  label: string;
  value: string;
}

@Component({
  selector: 'app-sys-permission-edit',
  imports: [...SHARED_IMPORTS],
  templateUrl: './permission-edit.component.html'
})
export class SysPermissionEditComponent implements OnInit {
  private readonly msg = inject(NzMessageService);
  private readonly cdr = inject(ChangeDetectorRef);
  private readonly permissionService = inject(SysPermissionService);
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);
  private readonly fb = inject(FormBuilder);
  private readonly settings = inject(SettingsService);

  form!: FormGroup;
  permissionId: number | null = null;
  isNew = false;
  loading = false;
  submitting = false;

  // HTTP方法选项
  httpMethodOptions: HttpMethodOption[] = [];
  // 资源类型选项
  resourceTypeOptions: ResourceTypeOption[] = [];

  // 当前用户信息
  get currentUser() {
    return this.settings.user;
  }

  get currentUserRoleCode() {
    return this.currentUser?.roleCode || this.currentUser?.role_code || '';
  }

  ngOnInit(): void {
    // 添加调试信息
    console.log('权限编辑组件 - 当前用户信息:', this.currentUser);
    console.log('权限编辑组件 - 当前用户角色编码:', this.currentUserRoleCode);

    this.initForm();
    this.loadOptions();
    this.checkRouteParams();
    this.checkPermissions();
  }

  private initForm(): void {
    this.form = this.fb.group({
      permission_code: [
        '',
        [Validators.required, Validators.pattern(/^[a-zA-Z0-9_:]+$/), Validators.minLength(2), Validators.maxLength(100)]
      ],
      permission_name: ['', [Validators.required, Validators.minLength(2), Validators.maxLength(100)]],
      api_path: ['', [Validators.required, Validators.pattern(/^\/.*$/), Validators.maxLength(200)]],
      api_method: ['', [Validators.required]],
      resource_type: [''],
      description: ['', [Validators.maxLength(500)]],
      status: [1, [Validators.required]]
    });
  }

  private loadOptions(): void {
    this.httpMethodOptions = this.permissionService.getHttpMethodOptions();
    this.resourceTypeOptions = this.permissionService.getResourceTypeOptions();
  }

  private checkPermissions(): void {
    const currentRole = this.currentUserRoleCode;

    // 只有超级管理员可以管理权限
    if (currentRole !== 'SUPER_ADMIN') {
      this.msg.warning('只有超级管理员可以编辑权限设置');
      this.goBack();
    }
  }

  private checkRouteParams(): void {
    this.route.params.subscribe(params => {
      const id = params['id'];
      if (id === 'new') {
        this.isNew = true;
        // 新增模式下不需要权限编码验证
        this.form.get('permission_code')?.setValidators([Validators.required, Validators.pattern(/^[a-zA-Z0-9_:]+$/)]);
        this.form.get('permission_code')?.updateValueAndValidity();
      } else if (id && !isNaN(+id)) {
        this.permissionId = +id;
        this.isNew = false;
        // 编辑模式下权限编码不可修改
        this.form.get('permission_code')?.setValidators([Validators.required]);
        this.form.get('permission_code')?.updateValueAndValidity();
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

    this.permissionService.getPermissionById(this.permissionId).subscribe({
      next: res => {
        this.loading = false;

        if ((res.code && res.code >= 200 && res.code < 300) || res.success === true) {
          const permissionData = res.data || res;

          this.form.patchValue(permissionData);
          // 编辑模式下权限编码不可修改
          this.form.get('permission_code')?.disable();
        } else {
          this.msg.error(res.message || '获取权限信息失败');
          this.goBack();
        }
        this.cdr.detectChanges();
      },
      error: () => {
        this.loading = false;
        this.msg.error('获取权限信息失败');
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

    // 如果是编辑模式，需要包含权限编码（因为表单中被禁用了）
    if (!this.isNew && this.form.get('permission_code')?.disabled) {
      formData.permission_code = this.form.get('permission_code')?.value;
    }

    const request$ = this.isNew
      ? this.permissionService.createPermission(formData)
      : this.permissionService.updatePermission(this.permissionId!, formData);

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
            this.msg.success(this.isNew ? '权限创建成功' : '权限更新成功');
            this.goBack();
          } else {
            this.msg.error(res.message || (this.isNew ? '创建权限失败' : '更新权限失败'));
          }
        },
        error: error => {
          console.error('权限操作失败:', error);
          this.msg.error(this.isNew ? '创建权限失败' : '更新权限失败');
        }
      });
  }

  goBack(): void {
    this.router.navigate(['/sys/permission']);
  }
}
