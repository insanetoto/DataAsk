import { Injectable, inject } from '@angular/core';
import { _HttpClient } from '@delon/theme';

@Injectable({ providedIn: 'root' })
export class AiAppService {
  private readonly http = inject(_HttpClient);
}
