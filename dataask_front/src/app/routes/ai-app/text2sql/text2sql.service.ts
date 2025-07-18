import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';

export interface Text2SQLRequest {
  question: string;
}

export interface Text2SQLResponse {
  success: boolean;
  sql?: string;
  confidence?: number;
  error?: string;
  timestamp?: string;
}

export interface SQLExecutionResponse {
  success: boolean;
  data?: any[];
  columns?: string[];
  row_count?: number;
  error?: string;
  execution_time?: number;
  timestamp?: string;
}

export interface TrainingSample {
  question: string;
  sql: string;
}

export interface ChatSession {
  session_id: string;
  title: string;
  created_at: string;
}

@Injectable({
  providedIn: 'root'
})
export class Text2SQLService {
  private readonly baseUrl = '/api/text2sql';

  constructor(private http: HttpClient) {}

  /**
   * 生成SQL查询
   */
  generateSQL(question: string): Observable<Text2SQLResponse> {
    return this.http.post<Text2SQLResponse>(`${this.baseUrl}/generate`, {
      question
    });
  }

  /**
   * 执行SQL查询
   */
  executeSQL(sql: string): Observable<SQLExecutionResponse> {
    return this.http.post<SQLExecutionResponse>(`${this.baseUrl}/execute`, {
      sql
    });
  }

  /**
   * 训练SQL样本
   */
  trainSQL(question: string, sql: string): Observable<any> {
    return this.http.post(`${this.baseUrl}/train`, {
      question,
      sql
    });
  }

  /**
   * 获取用户会话列表
   */
  getSessions(): Observable<any> {
    return this.http.get(`${this.baseUrl}/sessions`);
  }

  /**
   * 创建新会话
   */
  createSession(title?: string): Observable<any> {
    return this.http.post(`${this.baseUrl}/sessions`, { title });
  }

  /**
   * 删除会话
   */
  deleteSession(sessionId: string): Observable<any> {
    return this.http.delete(`${this.baseUrl}/sessions/${sessionId}`);
  }

  /**
   * 健康检查
   */
  healthCheck(): Observable<any> {
    return this.http.get(`${this.baseUrl}/health`);
  }
}
