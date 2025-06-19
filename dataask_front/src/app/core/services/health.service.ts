import { Injectable, inject } from '@angular/core';
import { DA_SERVICE_TOKEN } from '@delon/auth';
import { _HttpClient } from '@delon/theme';
import { environment } from '@env/environment';
import { Observable } from 'rxjs';

export interface HealthCheckResult {
  status: 'ok' | 'error';
  timestamp: string;
  apiUrl: string;
  token?: string;
  error?: any;
}

@Injectable({ providedIn: 'root' })
export class HealthService {
  private readonly http = inject(_HttpClient);
  private readonly tokenService = inject(DA_SERVICE_TOKEN);

  checkHealth(): Observable<HealthCheckResult> {
    const apiUrl = `${environment.api.baseUrl}/api/health`;
    const token = this.tokenService.get()?.token || '未设置';
    
    return new Observable<HealthCheckResult>(observer => {
      this.http.get('/api/health').subscribe({
        next: () => {
          observer.next({
            status: 'ok',
            timestamp: new Date().toLocaleString(),
            apiUrl,
            token
          });
          observer.complete();
        },
        error: (err: any) => {
          observer.next({
            status: 'error',
            timestamp: new Date().toLocaleString(),
            apiUrl,
            token,
            error: err
          });
          observer.complete();
        }
      });
    });
  }
} 