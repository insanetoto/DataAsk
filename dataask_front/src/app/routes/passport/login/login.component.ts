import { HttpContext } from '@angular/common/http';
import { ChangeDetectionStrategy, ChangeDetectorRef, Component, inject } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { StartupService } from '@core';
import { ReuseTabService } from '@delon/abc/reuse-tab';
import { ALLOW_ANONYMOUS, DA_SERVICE_TOKEN } from '@delon/auth';
import { SettingsService, _HttpClient } from '@delon/theme';
import { NzAlertModule } from 'ng-zorro-antd/alert';
import { NzButtonModule } from 'ng-zorro-antd/button';
import { NzCheckboxModule } from 'ng-zorro-antd/checkbox';
import { NzFormModule } from 'ng-zorro-antd/form';
import { NzGridModule } from 'ng-zorro-antd/grid';
import { NzIconModule } from 'ng-zorro-antd/icon';
import { NzInputModule } from 'ng-zorro-antd/input';
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
    NzIconModule,
    NzGridModule
  ],
  standalone: true
})
export class UserLoginComponent {
  private readonly router = inject(Router);
  private readonly settingsService = inject(SettingsService);
  private readonly reuseTabService = inject(ReuseTabService, { optional: true });
  private readonly tokenService = inject(DA_SERVICE_TOKEN);
  private readonly startupSrv = inject(StartupService);
  private readonly http = inject(_HttpClient);
  private readonly cdr = inject(ChangeDetectorRef);

  form = inject(FormBuilder).nonNullable.group({
    username: ['', [Validators.required]],
    password: ['', [Validators.required]],
    remember: [true]
  });

  error = '';
  loading = false;

  submit(): void {
    this.error = '';
    const { username, password } = this.form.controls;
    username.markAsDirty();
    username.updateValueAndValidity();
    password.markAsDirty();
    password.updateValueAndValidity();
    if (username.invalid || password.invalid) {
      return;
    }

    this.loading = true;
    this.cdr.detectChanges();
    this.http
      .post(
        '/api/auth/login',
        {
          username: this.form.value.username,
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
          if (res.code !== 200) {
            this.error = res.message || '登录失败';
            this.cdr.detectChanges();
            return;
          }
          // 清空路由复用信息
          this.reuseTabService?.clear();
          // 设置用户Token信息
          const token = {
            token: res.data.access_token,
            refresh_token: res.data.refresh_token,
            expired: Date.now() + res.data.expires_in * 1000
          };
          this.tokenService.set(token);
          // 重新获取 StartupService 内容，我们始终认为应用信息一般都会受当前用户授权范围而影响
          this.startupSrv.load().subscribe(() => {
            // 登录成功后直接跳转到dashboard
            this.router.navigateByUrl('/dashboard');
          });
        },
        error: err => {
          this.error = err.error?.message || '登录失败，请稍后重试';
          this.cdr.detectChanges();
        }
      });
  }
}
