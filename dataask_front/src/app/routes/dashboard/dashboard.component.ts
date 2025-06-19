import { ChangeDetectionStrategy, Component, OnInit } from '@angular/core';
import { PageHeaderModule } from '@delon/abc/page-header';
import { NzMessageService } from 'ng-zorro-antd/message';
import { HealthService } from '../../core/services/health.service';

@Component({
  selector: 'app-dashboard',
  templateUrl: './dashboard.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
  standalone: true,
  imports: [PageHeaderModule]
})
export class DashboardComponent implements OnInit {
  constructor(
    private healthService: HealthService,
    private message: NzMessageService
  ) {}

  ngOnInit(): void {
    this.checkHealth();
  }

  private checkHealth(): void {
    this.healthService.checkHealth().subscribe({
      next: res => {
        this.message.success('系统运行正常');
        console.log('健康检查结果：', res);
      },
      error: err => {
        this.message.error('系统异常，请检查服务状态');
        console.error('健康检查错误：', err);
      }
    });
  }
}
