import { Injectable, inject } from '@angular/core';
import { _HttpClient } from '@delon/theme';

@Injectable({ providedIn: 'root' })
export class AiAppYoloService {
  private readonly http = inject(_HttpClient);
}
