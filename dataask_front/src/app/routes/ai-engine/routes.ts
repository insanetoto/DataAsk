import { Routes } from '@angular/router';

import { AiEngineAskDataComponent } from './ask-data/ask-data.component';
import { AiEngineKnowledgeBaseComponent } from './knowledge-base/knowledge-base.component';

export const routes: Routes = [
  { path: 'ask-data', component: AiEngineAskDataComponent },
  { path: 'knowledge-base', component: AiEngineKnowledgeBaseComponent }
];
