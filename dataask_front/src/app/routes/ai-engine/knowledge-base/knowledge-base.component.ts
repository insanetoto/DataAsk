import { ChangeDetectionStrategy, Component } from '@angular/core';
import { PageHeaderModule } from '@delon/abc/page-header';

@Component({
  selector: 'app-ai-engine-knowledge-base',
  templateUrl: './knowledge-base.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [PageHeaderModule]
})
export class AiEngineKnowledgeBaseComponent {}
