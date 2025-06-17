import { HttpContext } from '@angular/common/http';
import { ChangeDetectionStrategy, ChangeDetectorRef, Component, OnDestroy, inject } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { StartupService } from '@core';
import { ReuseTabService } from '@delon/abc/reuse-tab';
import { ALLOW_ANONYMOUS, DA_SERVICE_TOKEN } from '@delon/auth';
import { _HttpClient } from '@delon/theme';

import { NzAlertModule } from 'ng-zorro-antd/alert';
import { NzButtonModule } from 'ng-zorro-antd/button';
import { NzCheckboxModule } from 'ng-zorro-antd/checkbox';
import { NzFormModule } from 'ng-zorro-antd/form';
import { NzIconModule } from 'ng-zorro-antd/icon';
import { NzInputModule } from 'ng-zorro-antd/input';
import { NzMessageService } from 'ng-zorro-antd/message';

import { finalize } from 'rxjs';

@Component({
  selector: 'passport-login',
  templateUrl: './login.component.html',
  styleUrls: ['./login.component.less'],

  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    RouterLink,
    ReactiveFormsModule,
    NzCheckboxModule,
    NzAlertModule,
    NzFormModule,
    NzInputModule,
    NzButtonModule,
    NzIconModule
  ]
})
export class UserLoginComponent implements OnDestroy {
  private readonly router = inject(Router);
  private readonly reuseTabService = inject(ReuseTabService, { optional: true });
  private readonly tokenService = inject(DA_SERVICE_TOKEN);
  private readonly startupSrv = inject(StartupService);
  private readonly http = inject(_HttpClient);
  private readonly cdr = inject(ChangeDetectorRef);
  private readonly message = inject(NzMessageService);

  form = inject(FormBuilder).nonNullable.group({
    userName: ['', [Validators.required, Validators.minLength(2)]],
    password: ['', [Validators.required, Validators.minLength(6)]],
    remember: [true]
  });
  error = '';
  loading = false;

  submit(): void {
    this.error = '';
    const { userName, password } = this.form.controls;
    userName.markAsDirty();
    userName.updateValueAndValidity();
    password.markAsDirty();
    password.updateValueAndValidity();
    
    if (userName.invalid || password.invalid) {
      return;
    }

    // 使用兼容的前端登录接口
    this.loading = true;
    this.cdr.detectChanges();
    
    this.http
      .post(
        '/login/account',
        {
          userName: this.form.value.userName,
          password: this.form.value.password
        },
        null,
        {
          context: new HttpContext().set(ALLOW_ANONYMOUS, true)
        }
      )
      .pipe(
        finalize(() => {
          this.loading = false;
          this.cdr.detectChanges();
        })
      )
      .subscribe({
        next: (res: any) => {
          if (res.msg !== 'ok') {
            this.error = res.msg || '登录失败';
            this.cdr.detectChanges();
            return;
          }
          
          // 显示登录成功消息
          this.message.success('登录成功');
          
          // 清空路由复用信息
          this.reuseTabService?.clear();
          
          // 设置用户Token信息
          res.user.expired = +new Date() + 1000 * 60 * 60 * 8; // 8小时过期
          this.tokenService.set(res.user);
          
          // 重新获取 StartupService 内容
          this.startupSrv.load().subscribe(() => {
            let url = this.tokenService.referrer!.url || '/';
            if (url.includes('/passport')) {
              url = '/dashboard';
            }
            this.router.navigateByUrl(url);
          });
        },
        error: (err) => {
          console.error('登录请求失败:', err);
          this.error = err.error?.msg || err.message || '登录请求失败，请稍后重试';
          this.cdr.detectChanges();
        }
      });
  }

  ngOnDestroy(): void {
    // 组件销毁时清理资源
  }
}
