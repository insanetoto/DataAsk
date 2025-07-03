import { ChangeDetectionStrategy, ChangeDetectorRef, Component, OnInit, inject } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { SHARED_IMPORTS } from '@shared';
import { NzMessageService } from 'ng-zorro-antd/message';
import { finalize } from 'rxjs';

import { SysUserService } from '../user.service';

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

  form!: FormGroup;
  userId: number | null = null;
  isNew = false;
  loading = false;
  submitting = false;

  // 选项数据
  organizationOptions: any[] = [];
  roleOptions: any[] = [];

  ngOnInit(): void {
    this.initForm();
    this.loadOptions();
    this.checkRouteParams();
  }

  private initForm(): void {
    this.form = this.fb.group({
      user_code: ['', [Validators.required]],
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
      } else if (id && !isNaN(+id)) {
        this.userId = +id;
        this.isNew = false;
        this.loadUserDetail();
      } else {
        this.msg.error('无效的用户ID');
        this.goBack();
      }
    });
  }

  private loadOptions(): void {
    this.loadOrganizationOptions();
    this.loadRoleOptions();
  }

  private loadOrganizationOptions(): void {
    this.userService.httpClient.get('/organizations', { pi: 1, ps: 1000, status: 1 }).subscribe({
      next: res => {
        if (res.code === 200 || res.success === true) {
          this.organizationOptions = res.data?.list || res.data?.items || res.data || [];
        } else {
          // 使用默认选项作为后备
          this.organizationOptions = [
            { id: 1, org_code: '050101', org_name: '总公司' },
            { id: 2, org_code: '050102', org_name: '分公司A' },
            { id: 3, org_code: '050103', org_name: '分公司B' }
          ];
        }
        this.cdr.detectChanges();
      },
      error: () => {
        // 使用默认选项作为后备
        this.organizationOptions = [
          { id: 1, org_code: '050101', org_name: '总公司' },
          { id: 2, org_code: '050102', org_name: '分公司A' },
          { id: 3, org_code: '050103', org_name: '分公司B' }
        ];
        this.cdr.detectChanges();
      }
    });
  }

  private loadRoleOptions(): void {
    this.userService.httpClient.get('/roles', { pi: 1, ps: 1000, status: 1 }).subscribe({
      next: res => {
        if (res.code === 200 || res.success === true) {
          this.roleOptions = res.data?.list || res.data?.items || res.data || [];
        } else {
          // 使用默认选项作为后备
          this.roleOptions = [
            { id: 1, role_name: '超级管理员' },
            { id: 2, role_name: '管理员' },
            { id: 3, role_name: '普通用户' }
          ];
        }
        this.cdr.detectChanges();
      },
      error: () => {
        // 使用默认选项作为后备
        this.roleOptions = [
          { id: 1, role_name: '超级管理员' },
          { id: 2, role_name: '管理员' },
          { id: 3, role_name: '普通用户' }
        ];
        this.cdr.detectChanges();
      }
    });
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
          if (res.code === 200 || res.success === true) {
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
