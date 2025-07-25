import { Routes } from '@angular/router';

import { AiAppSensevoiceComponent } from './sensevoice/sensevoice.component';
import { AiAppText2sqlComponent } from './text2sql/text2sql.component';
import { AiAppTrainingComponent } from './text2sql/training/training.component';
import { AiAppYoloComponent } from './yolo/yolo.component';

export const routes: Routes = [
  { path: 'text2sql', component: AiAppText2sqlComponent, data: { title: 'Text2SQL' } },
  { path: 'training', component: AiAppTrainingComponent, data: { title: '模型训练' } },
  { path: 'sensevoice', component: AiAppSensevoiceComponent, data: { title: '语音识别' } },
  { path: 'yolo', component: AiAppYoloComponent, data: { title: '目标检测' } }
];
