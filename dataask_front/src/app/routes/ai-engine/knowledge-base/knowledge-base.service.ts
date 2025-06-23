import { Injectable, inject } from '@angular/core';
import { _HttpClient } from '@delon/theme';

@Injectable({ providedIn: 'root' })
export class AiEngineKnowledgeBaseService {
  private readonly http = inject(_HttpClient);
}
