import { Injectable } from '@angular/core';
import { _HttpClient } from '@delon/theme';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class HealthService {
  constructor(private http: _HttpClient) {}

  /**
   * 获取健康状态
   */
  checkHealth(): Observable<any> {
    return this.http.get('/api/v1/health');
  }
} 