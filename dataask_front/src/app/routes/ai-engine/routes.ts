import { Routes } from '@angular/router';

import { AiEngineAskDataComponent } from './ask-data/ask-data.component';
import { AiEngineKnowledgeBaseComponent } from './knowledge-base/knowledge-base.component';

export const routes: Routes = [
  { path: 'ask-data', component: AiEngineAskDataComponent, data: { title: 'AI问答' } },
  { path: 'knowledge-base', component: AiEngineKnowledgeBaseComponent, data: { title: '知识库' } }
];
