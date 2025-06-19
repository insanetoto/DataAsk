import { ChangeDetectionStrategy, Component, inject } from '@angular/core';
import { PageHeaderModule } from '@delon/abc/page-header';
import { environment } from '@env/environment';
import { NzButtonModule } from 'ng-zorro-antd/button';
import { NzCardModule } from 'ng-zorro-antd/card';
import { NzMessageService } from 'ng-zorro-antd/message';
import { HealthService } from '../../core/services/health.service';

@Component({
  selector: 'app-dashboard',
  templateUrl: './dashboard.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
  standalone: true,
  imports: [PageHeaderModule, NzButtonModule, NzCardModule]
})
export class DashboardComponent {
  private readonly healthService = inject(HealthService);
  private readonly message = inject(NzMessageService);

  checkHealth(): void {
    const apiUrl = `${environment.api.baseUrl}/api/health`;
    this.healthService.checkHealth().subscribe({
      next: res => {
        console.log('Health check response:', res);
        this.message.success(`系统运行正常 (API: ${apiUrl})`);
      },
      error: err => {
        console.error('Health check error:', err);
        this.message.error(`系统异常，请检查后端服务 (API: ${apiUrl})`);
      }
    });
  }
}
