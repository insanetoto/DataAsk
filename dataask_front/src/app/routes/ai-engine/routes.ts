import { Routes } from '@angular/router';

import { AiEngineAskDataComponent } from './ask-data/ask-data.component';
import { AiEngineDatasourceComponent } from './datasource/datasource.component';
import { AiEngineKnowledgeBaseComponent } from './knowledge-base/knowledge-base.component';
import { AiEngineLlmmanageComponent } from './llmmanage/llmmanage.component';

export const routes: Routes = [
  { path: 'ask-data', component: AiEngineAskDataComponent, data: { title: 'AI问答' } },
  { path: 'knowledge-base', component: AiEngineKnowledgeBaseComponent, data: { title: '知识库' } },
  { path: 'datasource', component: AiEngineDatasourceComponent, data: { title: '数据源管理' } },
  { path: 'llmmanage', component: AiEngineLlmmanageComponent, data: { title: '大模型管理' } }
];
