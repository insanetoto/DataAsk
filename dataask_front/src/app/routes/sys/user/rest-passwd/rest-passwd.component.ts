import { CommonModule, Location } from '@angular/common';
import { ChangeDetectionStrategy, ChangeDetectorRef, Component, OnInit, inject } from '@angular/core';
import { AbstractControl, FormBuilder, FormGroup, ValidationErrors, ValidatorFn, Validators } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { ACLService } from '@delon/acl';
import { SettingsService } from '@delon/theme';
import { SHARED_IMPORTS } from '@shared';
import { NzMessageService } from 'ng-zorro-antd/message';
import { finalize } from 'rxjs';

import { SysUserService, User } from '../user.service';

// 自定义验证器：确认密码匹配
export const passwordMatchValidator: ValidatorFn = (control: AbstractControl): ValidationErrors | null => {
  const password = control.get('password');
  const confirmPassword = control.get('confirmPassword');

  if (!password || !confirmPassword) {
    return null;
  }

  return password.value === confirmPassword.value ? null : { passwordMismatch: true };
};

@Component({
  selector: 'app-sys-rest-passwd',
  templateUrl: './rest-passwd.component.html',
  styleUrl: './rest-passwd.component.less',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [CommonModule, ...SHARED_IMPORTS]
})
export class SysRestPasswdComponent implements OnInit {
  private readonly msg = inject(NzMessageService);
  private readonly cdr = inject(ChangeDetectorRef);
  private readonly router = inject(Router);
  private readonly route = inject(ActivatedRoute);
  private readonly location = inject(Location);
  private readonly fb = inject(FormBuilder);
  private readonly userService = inject(SysUserService);
  private readonly aclService = inject(ACLService);
  private readonly settings = inject(SettingsService);

  // 页面状态
  loading = false;
  submitting = false;
  userId!: number;
  userInfo: User | null = null;

  // 表单
  form: FormGroup;

  constructor() {
    // 初始化表单
    this.form = this.fb.group(
      {
        password: ['', [Validators.required, Validators.minLength(6), Validators.maxLength(20)]],
        confirmPassword: ['', [Validators.required]]
      },
      { validators: passwordMatchValidator }
    );
  }

  ngOnInit(): void {
    this.getUserId();
    this.loadUserInfo();
  }

  /**
   * 获取用户ID
   */
  private getUserId(): void {
    // 获取路由参数
    const id = this.route.snapshot.paramMap.get('id');
    if (!id) {
      this.msg.error('缺少用户ID参数');
      this.goBack();
      return;
    }

    this.userId = parseInt(id, 10);
    if (isNaN(this.userId)) {
      this.msg.error('无效的用户ID');
      this.goBack();
      return;
    }
  }

  /**
   * 加载用户信息
   */
  loadUserInfo(): void {
    this.loading = true;

    this.userService.getUserById(this.userId).subscribe({
      next: res => {
        this.loading = false;

        if (res.success || res.code === 200) {
          this.userInfo = res.data || res;
          // 加载用户信息后检查权限
          this.checkPermissions();
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
      }
    });
  }

  /**
   * 检查当前用户是否有权限重置目标用户的密码
   */
  private checkPermissions(): void {
    const currentUser = this.settings.user;
    if (!currentUser || !this.userInfo) {
      return;
    }

    // 获取当前用户角色
    const currentRoleCode = currentUser.role_code || currentUser.role?.role_code;

    // 如果是机构管理员，需要检查是否是同一机构
    if (currentRoleCode === 'ORG_ADMIN') {
      const currentOrgCode = currentUser.org_code || currentUser.organization?.org_code;
      const targetOrgCode = this.userInfo.org_code || (this.userInfo as any).organization?.org_code;

      if (currentOrgCode !== targetOrgCode) {
        this.msg.error('您只能重置本机构用户的密码');
        this.router.navigate(['/sys/user']);
        return;
      }
    }
  }

  /**
   * 保存重置密码
   */
  save(): void {
    if (this.form.invalid) {
      // 标记所有字段为已触摸，以显示验证错误
      Object.keys(this.form.controls).forEach(key => {
        this.form.get(key)?.markAsTouched();
        this.form.get(key)?.updateValueAndValidity();
      });
      return;
    }

    this.submitting = true;
    const formData = this.form.getRawValue();

    // 调用重置密码API
    this.userService
      .resetPassword(this.userId, formData.password)
      .pipe(
        finalize(() => {
          this.submitting = false;
          this.cdr.detectChanges();
        })
      )
      .subscribe({
        next: res => {
          if (res.code === 200 || res.success === true) {
            this.msg.success('密码重置成功');
            this.goBack();
          } else {
            this.msg.error(res.message || res.error || '重置密码失败');
          }
        },
        error: error => {
          // 检查是否是权限错误
          if (error.status === 403) {
            this.msg.error('权限不足，无法重置该用户的密码');
          } else if (error.status === 400) {
            this.msg.error('请求参数错误');
          } else {
            this.msg.error('重置密码失败，请稍后重试');
          }
        }
      });
  }

  /**
   * 返回用户列表
   */
  goBack(): void {
    this.location.back();
  }
}
