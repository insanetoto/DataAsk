import { Injectable, inject } from '@angular/core';
import { _HttpClient } from '@delon/theme';
import { Observable } from 'rxjs';

export interface ReportData {
  id: number;
  name: string;
  type: string;
  created_at: string;
  status: number;
}

export interface ReportQuery {
  pi: number;
  ps: number;
  keyword?: string;
  type?: string;
  status?: number;
}

export interface ReportStatistics {
  total_users: number;
  total_organizations: number;
  total_queries: number;
  system_availability: number;
}

@Injectable({ providedIn: 'root' })
export class WorkspaceReportService {
  private readonly http = inject(_HttpClient);

  /**
   * 获取报表列表
   */
  getReports(params: ReportQuery): Observable<any> {
    return this.http.get('/reports', params);
  }

  /**
   * 获取报表统计数据
   */
  getReportStatistics(): Observable<any> {
    return this.http.get('/reports/statistics');
  }

  /**
   * 导出报表
   */
  exportReport(reportId: number): Observable<any> {
    return this.http.get(`/reports/${reportId}/export`);
  }

  /**
   * 创建报表
   */
  createReport(data: Partial<ReportData>): Observable<any> {
    return this.http.post('/reports', data);
  }

  /**
   * 更新报表
   */
  updateReport(id: number, data: Partial<ReportData>): Observable<any> {
    return this.http.put(`/reports/${id}`, data);
  }

  /**
   * 删除报表
   */
  deleteReport(id: number): Observable<any> {
    return this.http.delete(`/reports/${id}`);
  }
} 