import { JsonPipe, NgIf } from '@angular/common';
import { ChangeDetectionStrategy, ChangeDetectorRef, Component, inject } from '@angular/core';
import { PageHeaderModule } from '@delon/abc/page-header';

import { NzBadgeModule } from 'ng-zorro-antd/badge';
import { NzButtonModule } from 'ng-zorro-antd/button';
import { NzCardModule } from 'ng-zorro-antd/card';
import { NzDescriptionsModule } from 'ng-zorro-antd/descriptions';
import { NzMessageService } from 'ng-zorro-antd/message';

import { HealthService, HealthCheckResult } from '../../core/services/health.service';

@Component({
  selector: 'app-dashboard',
  templateUrl: './dashboard.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
  standalone: true,
  imports: [PageHeaderModule, NzButtonModule, NzCardModule, NzDescriptionsModule, NzBadgeModule, JsonPipe, NgIf]
})
export class DashboardComponent {
  private readonly healthService = inject(HealthService);
  private readonly message = inject(NzMessageService);
  private readonly cdr = inject(ChangeDetectorRef);

  healthResult?: HealthCheckResult;
  loading = false;

  checkHealth(): void {
    this.loading = true;
    this.healthService.checkHealth().subscribe({
      next: result => {
        this.healthResult = result;
        this.message.success(result.status === 'ok' ? `系统运行正常 (API: ${result.apiUrl})` : `系统异常，请检查后端服务 (API: ${result.apiUrl})`);
        this.loading = false;
        this.cdr.markForCheck();
      },
      error: () => {
        this.loading = false;
        this.cdr.markForCheck();
      }
    });
  }
}
