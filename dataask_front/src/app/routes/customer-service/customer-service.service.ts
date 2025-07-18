import { Injectable, inject } from '@angular/core';
import { _HttpClient } from '@delon/theme';

@Injectable({ providedIn: 'root' })
export class CustomerServiceService {
  private readonly http = inject(_HttpClient);
}
