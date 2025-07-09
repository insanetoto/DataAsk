import { Routes } from '@angular/router';

import { AiAppText2sqlComponent } from './text2sql/text2sql.component';

export const routes: Routes = [{ path: 'text2sql', component: AiAppText2sqlComponent, data: { title: 'Text2SQL' } }];
