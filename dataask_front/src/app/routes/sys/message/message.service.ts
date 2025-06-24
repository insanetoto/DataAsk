import { Injectable, inject } from '@angular/core';
import { _HttpClient } from '@delon/theme';
import { Observable } from 'rxjs';

export interface Message {
  id?: number;
  title: string;
  content: string;
  type: 'system' | 'business' | 'alert';
  status: 'draft' | 'sent' | 'read';
  recipient: string;
  sender?: string;
  sent_at?: string;
  created_at?: string;
  updated_at?: string;
  read_count?: number;
  total_recipients?: number;
}

export interface MessageQuery {
  pi?: number;
  ps?: number;
  title?: string;
  type?: string;
  status?: string;
}

export interface MessageSubscription {
  id?: number;
  user_id: number;
  message_type: string;
  channel: 'email' | 'sms' | 'system';
  enabled: boolean;
  created_at?: string;
}

export interface MessagePublish {
  title: string;
  content: string;
  type: string;
  channels: string[];
}

@Injectable({ providedIn: 'root' })
export class SysMessageService {
  private readonly http = inject(_HttpClient);

  /**
   * 获取消息列表
   */
  getMessages(params: MessageQuery = {}): Observable<any> {
    return this.http.get('/api/message', params);
  }

  /**
   * 获取消息详情
   */
  getMessage(id: number): Observable<any> {
    return this.http.get(`/api/message/${id}`);
  }

  /**
   * 创建消息
   */
  createMessage(data: Partial<Message>): Observable<any> {
    return this.http.post('/api/message', data);
  }

  /**
   * 更新消息
   */
  updateMessage(id: number, data: Partial<Message>): Observable<any> {
    return this.http.put(`/api/message/${id}`, data);
  }

  /**
   * 删除消息
   */
  deleteMessage(id: number): Observable<any> {
    return this.http.delete(`/api/message/${id}`);
  }

  /**
   * 发送消息
   */
  sendMessage(id: number): Observable<any> {
    return this.http.post(`/api/message/${id}/send`, {});
  }

  /**
   * 批量删除消息
   */
  batchDeleteMessages(ids: number[]): Observable<any> {
    return this.http.post('/api/message/batch/delete', { ids });
  }

  /**
   * 批量发送消息
   */
  batchSendMessages(ids: number[]): Observable<any> {
    return this.http.post('/api/message/batch/send', { ids });
  }

  /**
   * 获取消息统计信息
   */
  getMessageStats(): Observable<any> {
    return this.http.get('/api/message/stats');
  }

  /**
   * 获取用户订阅列表
   */
  getUserSubscriptions(userId: number): Observable<any> {
    return this.http.get(`/api/message/subscriptions/${userId}`);
  }

  /**
   * 更新用户订阅
   */
  updateUserSubscription(userId: number, data: Partial<MessageSubscription>): Observable<any> {
    return this.http.put(`/api/message/subscriptions/${userId}`, data);
  }

  /**
   * 获取消息类型选项
   */
  getMessageTypes(): Observable<any> {
    return this.http.get('/api/message/types');
  }

  /**
   * 获取消息推送渠道
   */
  getMessageChannels(): Observable<any> {
    return this.http.get('/api/message/channels');
  }

  /**
   * 发布消息
   */
  publishMessage(data: MessagePublish): Observable<any> {
    return this.http.post('/api/message/publish', data);
  }

  /**
   * 订阅消息
   */
  subscribeMessage(data: { user_id: number; message_type: string; channel: string }): Observable<any> {
    return this.http.post('/api/message/subscribe', data);
  }

  /**
   * 取消订阅消息
   */
  unsubscribeMessage(data: { user_id: number; message_type: string }): Observable<any> {
    return this.http.post('/api/message/unsubscribe', data);
  }

  /**
   * 获取用户列表用于消息接收人选择
   */
  getUsers(): Observable<any> {
    return this.http.get('/api/users');
  }
}
