import { CommonModule } from '@angular/common';
import { ChangeDetectionStrategy, Component, OnInit, OnDestroy, inject, ChangeDetectorRef } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { ExceptionModule, ExceptionType } from '@delon/abc/exception';
import { DA_SERVICE_TOKEN } from '@delon/auth';
import { NzButtonModule } from 'ng-zorro-antd/button';
import { NzCardModule } from 'ng-zorro-antd/card';
import { NzMessageService } from 'ng-zorro-antd/message';
import { NzProgressModule } from 'ng-zorro-antd/progress';

@Component({
  selector: 'app-exception',
  template: `
    <exception [type]="type" style="min-height: 500px; height: 80%;">
      <nz-card style="margin: 20px auto; max-width: 500px; text-align: center;">
        <div class="auto-redirect-info">
          <h4 style="color: #333; margin-bottom: 16px;">
            <i nz-icon nzType="info-circle" style="color: #1890ff; margin-right: 8px;"></i>
            {{ redirectMessage }}
          </h4>
          <nz-progress [nzPercent]="progressPercent" nzType="circle" [nzWidth]="80">
            <span style="color: #1890ff; font-weight: bold; font-size: 16px;">{{ countdown }}</span>
          </nz-progress>
          <p style="margin: 16px 0 20px; color: #666;">
            系统将在 <strong style="color: #1890ff;">{{ countdown }}</strong> 秒后自动跳转
          </p>
          <div style="display: flex; gap: 12px; justify-content: center;">
            <button nz-button nzType="primary" (click)="redirectNow()" [nzLoading]="isRedirecting">
              <i nz-icon nzType="fast-forward"></i> 立即跳转
            </button>
            <button nz-button nzType="default" (click)="cancelRedirect()">
              <i nz-icon nzType="stop"></i> 取消自动跳转
            </button>
          </div>
          <div style="margin-top: 16px; font-size: 12px; color: #999;">
            <p *ngIf="type === 404">页面不存在或已被移除</p>
            <p *ngIf="type === 500">服务器内部错误，请稍后重试</p>
            <p *ngIf="type === 403">访问被拒绝，权限不足</p>
          </div>
        </div>
      </nz-card>
    </exception>
  `,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [CommonModule, ExceptionModule, NzButtonModule, NzCardModule, NzProgressModule]
})
export class ExceptionComponent implements OnInit, OnDestroy {
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);
  private readonly tokenService = inject(DA_SERVICE_TOKEN);
  private readonly msg = inject(NzMessageService);
  private readonly cdr = inject(ChangeDetectorRef);

  countdown = 2;
  redirectMessage = '正在检查登录状态...';
  isRedirecting = false;
  isCancelled = false;
  private timer: any;
  private countdownTimer: any;

  get type(): ExceptionType {
    return this.route.snapshot.data['type'];
  }

  get progressPercent(): number {
    return ((2 - this.countdown) / 2) * 100;
  }

  ngOnInit(): void {
    this.startCountdown();
    this.scheduleRedirect();
  }

  ngOnDestroy(): void {
    this.clearTimers();
  }

  private clearTimers(): void {
    if (this.timer) {
      clearTimeout(this.timer);
    }
    if (this.countdownTimer) {
      clearInterval(this.countdownTimer);
    }
  }

  private startCountdown(): void {
    this.countdownTimer = setInterval(() => {
      if (!this.isCancelled) {
        this.countdown--;
        this.cdr.detectChanges();
        if (this.countdown <= 0) {
          clearInterval(this.countdownTimer);
        }
      }
    }, 1000);
  }

  private scheduleRedirect(): void {
    const isLoggedIn = this.checkUserLoggedIn();
    if (isLoggedIn) {
      this.redirectMessage = '用户已登录，即将返回仪表板';
    } else {
      this.redirectMessage = '用户未登录，即将跳转到登录页面';
    }
    this.cdr.detectChanges();

    this.timer = setTimeout(() => {
      if (!this.isCancelled) {
        this.redirect();
      }
    }, 2000);
  }

  private checkUserLoggedIn(): boolean {
    try {
      const tokenData = this.tokenService.get();
      if (!tokenData || !tokenData.token) {
        return false;
      }
      if (tokenData.expired && tokenData.expired <= Date.now()) {
        return false;
      }
      return true;
    } catch (error) {
      console.error('检查登录状态时出错:', error);
      return false;
    }
  }

  redirectNow(): void {
    this.isRedirecting = true;
    this.clearTimers();
    this.cdr.detectChanges();
    this.redirect();
  }

  cancelRedirect(): void {
    this.isCancelled = true;
    this.clearTimers();
    this.redirectMessage = '已取消自动跳转';
    this.msg.info('已取消自动跳转，您可以手动选择操作');
    this.cdr.detectChanges();
  }

  private redirect(): void {
    const isLoggedIn = this.checkUserLoggedIn();
    if (isLoggedIn) {
      this.router.navigate(['/dashboard']).then(() => {
        this.msg.success('已返回仪表板');
      }).catch(err => {
        console.error('跳转到仪表板失败:', err);
        this.router.navigate(['/']);
      });
    } else {
      this.router.navigate(['/passport/login']).then(() => {
        this.msg.info('请重新登录');
      }).catch(err => {
        console.error('跳转到登录页失败:', err);
        window.location.href = '/passport/login';
      });
    }
  }
}
