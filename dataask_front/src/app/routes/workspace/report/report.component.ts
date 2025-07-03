import { ChangeDetectionStrategy, ChangeDetectorRef, Component, OnInit, inject } from '@angular/core';
import { _HttpClient } from '@delon/theme';
import { SHARED_IMPORTS } from '@shared';
import { NzMessageService } from 'ng-zorro-antd/message';

import { WorkspaceReportService, ReportStatistics } from './report.service';

@Component({
  selector: 'app-workspace-report',
  templateUrl: './report.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: SHARED_IMPORTS
})
export class WorkspaceReportComponent implements OnInit {
  private readonly http = inject(_HttpClient);
  private readonly msg = inject(NzMessageService);
  private readonly cdr = inject(ChangeDetectorRef);
  private readonly reportService = inject(WorkspaceReportService);

  loading = false;
  statistics: ReportStatistics = {
    total_users: 0,
    total_organizations: 0,
    total_queries: 0,
    system_availability: 0
  };

  ngOnInit(): void {
    this.loadReportData();
  }

  /**
   * 加载工作报表数据
   */
  loadReportData(): void {
    this.loading = true;

    // 模拟数据，实际应该调用API
    setTimeout(() => {
      this.statistics = {
        total_users: 1234,
        total_organizations: 56,
        total_queries: 8901,
        system_availability: 99.9
      };
      this.loading = false;
      this.cdr.detectChanges();
    }, 1000);
  }

  /**
   * 刷新工作报表
   */
  refreshReport(): void {
    this.msg.info('正在刷新工作报表数据...');
    this.loadReportData();
  }

  /**
   * 导出工作报表
   */
  exportReport(): void {
    this.msg.info('工作报表导出功能正在开发中...');
  }
}
