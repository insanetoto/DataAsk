import { ChangeDetectionStrategy, Component } from '@angular/core';
import { PageHeaderModule } from '@delon/abc/page-header';

@Component({
  selector: 'app-ai-engine-ask-data',
  templateUrl: './ask-data.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [PageHeaderModule]
})
export class AiEngineAskDataComponent {}
