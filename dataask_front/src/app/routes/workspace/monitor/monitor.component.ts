import { ChangeDetectionStrategy, Component } from '@angular/core';
import { PageHeaderModule } from '@delon/abc/page-header';

@Component({
  selector: 'app-workspace-monitor',
  templateUrl: './monitor.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [PageHeaderModule]
})
export class WorkspaceMonitorComponent {}
