import { CommonModule } from '@angular/common';
import { ChangeDetectionStrategy, Component, ChangeDetectorRef, ElementRef, ViewChild, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { RouterModule, Router } from '@angular/router';
import { PageHeaderModule } from '@delon/abc/page-header';
import { NzAvatarModule } from 'ng-zorro-antd/avatar';
import { NzBreadCrumbModule } from 'ng-zorro-antd/breadcrumb';
import { NzButtonModule } from 'ng-zorro-antd/button';
import { NzCardModule } from 'ng-zorro-antd/card';
import { NzDividerModule } from 'ng-zorro-antd/divider';
import { NzFlexModule } from 'ng-zorro-antd/flex';
import { NzIconModule } from 'ng-zorro-antd/icon';
import { NzInputModule } from 'ng-zorro-antd/input';
import { NzLayoutModule } from 'ng-zorro-antd/layout';
import { NzListModule } from 'ng-zorro-antd/list';
import { NzMessageService } from 'ng-zorro-antd/message';
import { NzSpaceModule } from 'ng-zorro-antd/space';
import { NzTableModule } from 'ng-zorro-antd/table';
import { NzToolTipModule } from 'ng-zorro-antd/tooltip';
import { NzTypographyModule } from 'ng-zorro-antd/typography';

import { Text2SQLService } from './text2sql.service';

interface ChatMessage {
  id: string;
  content: string;
  type: 'user' | 'assistant';
  timestamp: Date;
  loading?: boolean;
  sqlQuery?: string;
  queryResult?: any[];
}

interface ChatSession {
  id: string;
  title: string;
  lastMessage: string;
  timestamp: Date;
  messageCount: number;
}

@Component({
  selector: 'app-ai-app-text2sql',
  templateUrl: './text2sql.component.html',
  styleUrls: ['./text2sql.component.less'],
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    CommonModule,
    FormsModule,
    RouterModule,
    PageHeaderModule,
    NzBreadCrumbModule,
    NzLayoutModule,
    NzListModule,
    NzButtonModule,
    NzInputModule,
    NzIconModule,
    NzCardModule,
    NzAvatarModule,
    NzToolTipModule,
    NzTypographyModule,
    NzSpaceModule,
    NzFlexModule,
    NzDividerModule,
    NzTableModule
  ]
})
export class AiAppText2sqlComponent {
  private readonly text2sqlService = inject(Text2SQLService);
  private readonly msgSrv = inject(NzMessageService);
  private readonly router = inject(Router);
  private cdr = inject(ChangeDetectorRef);

  @ViewChild('messageInput') messageInput!: ElementRef<HTMLTextAreaElement>;
  @ViewChild('messagesContainer') messagesContainer!: ElementRef<HTMLDivElement>;

  // 当前输入内容
  currentMessage = '';

  // 是否正在发送消息
  sending = false;

  // 当前选中的对话会话
  currentSessionId = '';

  // 对话历史会话列表
  chatSessions: ChatSession[] = [];

  // 当前对话的消息列表
  currentMessages: ChatMessage[] = [];

  constructor() {
    // 初始化组件时加载会话列表
    this.loadSessions();
  }

  /**
   * 加载用户会话列表
   */
  private loadSessions(): void {
    this.text2sqlService.getSessions().subscribe({
      next: response => {
        if (response.sessions && Array.isArray(response.sessions)) {
          this.chatSessions = response.sessions.map((session: any) => ({
            id: session.session_id,
            title: session.title || '新的对话',
            lastMessage: session.title || '',
            timestamp: new Date(session.created_at),
            messageCount: 0
          }));
        }
        this.cdr.markForCheck();
      },
      error: () => {
        // 如果加载失败，继续使用空数组
        console.warn('加载会话列表失败，将使用本地会话管理');
      }
    });
  }

  /**
   * 选择对话会话
   */
  selectSession(session: ChatSession): void {
    this.currentSessionId = session.id;

    // 模拟加载该会话的消息历史
    this.loadSessionMessages(session.id);
    this.cdr.markForCheck();
  }

  /**
   * 加载会话消息
   */
  private loadSessionMessages(sessionId: string): void {
    // TODO: 调用后端API加载会话消息
    // this.http.get(`/api/text2sql/sessions/${sessionId}/messages`).subscribe(
    //   (messages: ChatMessage[]) => {
    //     this.currentMessages = messages;
    //     this.cdr.markForCheck();
    //   },
    //   (error) => {
    //     this.msgSrv.error('加载消息失败');
    //     this.currentMessages = [];
    //   }
    // );

    // 暂时清空消息列表，忽略sessionId参数直到实现后端API
    console.log('Loading session:', sessionId);
    this.currentMessages = [];
  }

  /**
   * 发送消息
   */
  sendMessage(): void {
    if (!this.currentMessage.trim() || this.sending) {
      return;
    }

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      content: this.currentMessage.trim(),
      type: 'user',
      timestamp: new Date()
    };

    // 添加用户消息
    this.currentMessages.push(userMessage);

    // 清空输入框
    const messageText = this.currentMessage.trim();
    this.currentMessage = '';
    this.sending = true;

    // 添加加载中的助手消息
    const loadingMessage: ChatMessage = {
      id: (Date.now() + 1).toString(),
      content: '',
      type: 'assistant',
      timestamp: new Date(),
      loading: true
    };
    this.currentMessages.push(loadingMessage);

    this.cdr.markForCheck();

    // 滚动到底部
    setTimeout(() => this.scrollToBottom(), 100);

    // 调用Text2SQL API生成SQL
    this.handleText2SQLResponse(messageText, loadingMessage);
  }

  /**
   * 处理Text2SQL AI回复
   */
  private handleText2SQLResponse(userMessage: string, loadingMessage: ChatMessage): void {
    this.text2sqlService.generateSQL(userMessage).subscribe({
      next: response => {
        if (response.success && response.sql) {
          loadingMessage.content = '我为您生成了SQL查询语句：';
          loadingMessage.sqlQuery = response.sql;
          loadingMessage.loading = false;

          // 自动执行SQL获取结果
          this.text2sqlService.executeSQL(response.sql).subscribe({
            next: execResponse => {
              if (execResponse.success) {
                loadingMessage.queryResult = execResponse.data;
              }
              this.sending = false;
              this.cdr.markForCheck();
              setTimeout(() => this.scrollToBottom(), 100);
              this.updateCurrentSession(userMessage);
            },
            error: () => {
              loadingMessage.content += '\n\n执行查询时出现错误，请检查SQL语句。';
              this.sending = false;
              this.cdr.markForCheck();
            }
          });
        } else {
          loadingMessage.content = response.error || 'SQL生成失败，请重新描述您的需求。';
          loadingMessage.loading = false;
          this.sending = false;
          this.cdr.markForCheck();
        }
      },
      error: () => {
        this.msgSrv.error('生成SQL失败，请重试');
        const index = this.currentMessages.indexOf(loadingMessage);
        if (index > -1) {
          this.currentMessages.splice(index, 1);
        }
        this.sending = false;
        this.cdr.markForCheck();
      }
    });
  }

  /**
   * 更新当前会话信息
   */
  private updateCurrentSession(lastMessage: string): void {
    const currentSession = this.chatSessions.find(s => s.id === this.currentSessionId);
    if (currentSession) {
      currentSession.lastMessage = lastMessage.length > 20 ? `${lastMessage.substring(0, 20)}...` : lastMessage;
      currentSession.timestamp = new Date();
      currentSession.messageCount += 2; // 用户消息 + AI回复
    }
  }

  /**
   * 开始新对话
   */
  startNewChat(): void {
    const title = '新的Text2SQL对话';
    
    this.text2sqlService.createSession(title).subscribe({
      next: response => {
        const newSession: ChatSession = {
          id: response.session_id || Date.now().toString(),
          title: title,
          lastMessage: '',
          timestamp: new Date(),
          messageCount: 0
        };

        this.chatSessions.unshift(newSession);
        this.selectSession(newSession);
      },
      error: () => {
        // 如果API调用失败，创建本地会话
        const newSession: ChatSession = {
          id: Date.now().toString(),
          title: title,
          lastMessage: '',
          timestamp: new Date(),
          messageCount: 0
        };

        this.chatSessions.unshift(newSession);
        this.selectSession(newSession);
      }
    });
  }

  /**
   * 清除历史对话记录
   */
  clearChatHistory(): void {
    if (this.chatSessions.length === 0) {
      return;
    }

    // TODO: 调用后端API清除历史记录
    // this.http.delete('/api/text2sql/sessions').subscribe(
    //   () => {
    //     this.chatSessions = [];
    //     this.currentMessages = [];
    //     this.currentSessionId = '';
    //     this.msgSrv.success('历史对话记录已清除');
    //     this.cdr.markForCheck();
    //   },
    //   (error) => {
    //     this.msgSrv.error('清除失败，请重试');
    //   }
    // );

    // 暂时本地清除
    this.chatSessions = [];
    this.currentMessages = [];
    this.currentSessionId = '';
    this.msgSrv.success('历史对话记录已清除');
    this.cdr.markForCheck();
  }

  /**
   * 使用示例查询
   */
  useExample(example: string): void {
    this.currentMessage = example;
    this.cdr.markForCheck();
  }

  /**
   * 复制SQL语句
   */
     copySql(sql: string): void {
     navigator.clipboard
       .writeText(sql)
       .then(() => {
         this.msgSrv.success('SQL语句已复制到剪贴板');
       })
       .catch(() => {
         this.msgSrv.error('复制失败，请手动复制');
       });
  }

  /**
   * 获取表格列名
   */
  getTableColumns(data: any[]): string[] {
    if (!data || data.length === 0) return [];
    return Object.keys(data[0]);
  }

  /**
   * 处理键盘事件
   */
  handleKeyDown(event: KeyboardEvent): void {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      this.sendMessage();
    }
  }

  /**
   * 滚动到底部
   */
  private scrollToBottom(): void {
    if (this.messagesContainer) {
      const element = this.messagesContainer.nativeElement;
      element.scrollTop = element.scrollHeight;
    }
  }

  /**
   * 格式化时间
   */
  formatTime(date: Date): string {
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const days = Math.floor(diff / (1000 * 60 * 60 * 24));
    
    if (days === 0) {
      return '今天';
    } else if (days === 1) {
      return '昨天';
    } else if (days < 7) {
      return `${days}天前`;
    } else {
      return date.toLocaleDateString();
    }
  }

  /**
   * 格式化消息时间
   */
  formatMessageTime(date: Date): string {
    return date.toLocaleTimeString('zh-CN', { 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  }

  /**
   * 获取当前会话标题
   */
  get currentSessionTitle(): string {
    const session = this.chatSessions.find(s => s.id === this.currentSessionId);
    return session ? session.title : 'Text2SQL 助手';
  }

  /**
   * 跳转到训练页面
   */
  goToTraining(): void {
    this.router.navigate(['/ai-app/training']);
  }
}
