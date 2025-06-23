import { ChangeDetectionStrategy, Component } from '@angular/core';
import { PageHeaderModule } from '@delon/abc/page-header';

@Component({
  selector: 'app-workspace-workbench',
  templateUrl: './workbench.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [PageHeaderModule]
})
export class WorkspaceWorkbenchComponent {}
