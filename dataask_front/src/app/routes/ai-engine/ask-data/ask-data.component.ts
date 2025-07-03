import { CommonModule } from '@angular/common';
import { ChangeDetectionStrategy, Component, ChangeDetectorRef, ElementRef, ViewChild, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { PageHeaderModule } from '@delon/abc/page-header';
import { NzAvatarModule } from 'ng-zorro-antd/avatar';
import { NzButtonModule } from 'ng-zorro-antd/button';
import { NzCardModule } from 'ng-zorro-antd/card';
import { NzDividerModule } from 'ng-zorro-antd/divider';
import { NzFlexModule } from 'ng-zorro-antd/flex';
import { NzIconModule } from 'ng-zorro-antd/icon';
import { NzInputModule } from 'ng-zorro-antd/input';
import { NzLayoutModule } from 'ng-zorro-antd/layout';
import { NzListModule } from 'ng-zorro-antd/list';
import { NzSpaceModule } from 'ng-zorro-antd/space';
import { NzToolTipModule } from 'ng-zorro-antd/tooltip';
import { NzTypographyModule } from 'ng-zorro-antd/typography';

interface ChatMessage {
  id: string;
  content: string;
  type: 'user' | 'assistant';
  timestamp: Date;
  loading?: boolean;
}

interface ChatSession {
  id: string;
  title: string;
  lastMessage: string;
  timestamp: Date;
  messageCount: number;
}

@Component({
  selector: 'app-ai-engine-ask-data',
  templateUrl: './ask-data.component.html',
  styleUrls: ['./ask-data.component.less'],
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    CommonModule,
    FormsModule,
    PageHeaderModule,
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
    NzDividerModule
  ]
})
export class AiEngineAskDataComponent {
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
  chatSessions: ChatSession[] = [
    {
      id: '1',
      title: '昆明小微企业季度免税政策解析',
      lastMessage: '帮我分析一个会议议程，今天我代...',
      timestamp: new Date(),
      messageCount: 8
    },
    {
      id: '2',
      title: '免费SVG图片资源网站推荐',
      lastMessage: '推荐几个免费的SVG图片网站',
      timestamp: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000),
      messageCount: 5
    },
    {
      id: '3',
      title: 'JPG转SVG方法及工具推荐',
      lastMessage: '如何将JPG格式转换为SVG',
      timestamp: new Date(Date.now() - 14 * 24 * 60 * 60 * 1000),
      messageCount: 12
    }
  ];

  // 当前对话的消息列表
  currentMessages: ChatMessage[] = [];

  constructor() {
    // 默认选中第一个会话
    if (this.chatSessions.length > 0) {
      this.selectSession(this.chatSessions[0]);
    }
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
   * 加载会话消息（模拟数据）
   */
  private loadSessionMessages(sessionId: string): void {
    // 根据不同会话ID加载不同的模拟对话
    if (sessionId === '1') {
      this.currentMessages = [
        {
          id: '1',
          content: '帮我分析一个会议议程，今天我代表公司参加昆明小微企业季度免税政策解析会议',
          type: 'user',
          timestamp: new Date(Date.now() - 60 * 60 * 1000)
        },
        {
          id: '2',
          content:
            '我来帮您分析这个会议议程。昆明小微企业季度免税政策解析会议是一个非常重要的政策宣讲会，主要内容可能包括：\n\n1. **最新免税政策解读**\n   - 小微企业所得税优惠政策\n   - 增值税减免措施\n   - 相关申报流程\n\n2. **政策适用范围**\n   - 小微企业认定标准\n   - 享受优惠的具体条件\n\n3. **实务操作指导**\n   - 如何正确申报\n   - 需要准备的材料\n   - 常见问题解答\n\n建议您准备以下问题：\n- 公司是否符合小微企业认定标准\n- 具体的税收优惠幅度\n- 申报的时间节点和流程\n\n需要我帮您准备更具体的问题清单吗？',
          type: 'assistant',
          timestamp: new Date(Date.now() - 59 * 60 * 1000)
        }
      ];
    } else {
      this.currentMessages = [
        {
          id: '1',
          content: '推荐几个免费的SVG图片网站',
          type: 'user',
          timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000)
        },
        {
          id: '2',
          content:
            '为您推荐几个优质的免费SVG图片资源网站：\n\n**1. Heroicons**\n- 网址：heroicons.com\n- 特色：现代、简洁的图标库\n- 适用：Web界面设计\n\n**2. Feather Icons**\n- 网址：feathericons.com\n- 特色：轻量级、美观的图标\n- 适用：移动应用和网页\n\n**3. Lucide**\n- 网址：lucide.dev\n- 特色：开源、可定制\n- 适用：各类项目\n\n这些网站都提供高质量的SVG图标，您可以根据项目需求选择合适的风格。',
          type: 'assistant',
          timestamp: new Date(Date.now() - 119 * 60 * 1000)
        }
      ];
    }
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

    // 模拟AI回复（2秒后）
    setTimeout(() => {
      this.simulateAIResponse(messageText, loadingMessage);
    }, 2000);
  }

  /**
   * 模拟AI回复
   */
  private simulateAIResponse(userMessage: string, loadingMessage: ChatMessage): void {
    // 移除加载消息
    const loadingIndex = this.currentMessages.findIndex(msg => msg.id === loadingMessage.id);
    if (loadingIndex > -1) {
      this.currentMessages.splice(loadingIndex, 1);
    }

    // 生成模拟回复
    const response = this.generateMockResponse(userMessage);

    const assistantMessage: ChatMessage = {
      id: Date.now().toString(),
      content: response,
      type: 'assistant',
      timestamp: new Date()
    };

    this.currentMessages.push(assistantMessage);
    this.sending = false;
    this.cdr.markForCheck();

    // 滚动到底部
    setTimeout(() => this.scrollToBottom(), 100);
  }

  /**
   * 生成模拟回复内容
   */
  private generateMockResponse(userMessage: string): string {
    const responses = [
      '我理解您的问题。基于我的分析，这个问题可以从以下几个角度来看：\n\n1. **首先**，需要考虑当前的具体情况\n2. **其次**，要分析可能的解决方案\n3. **最后**，制定具体的行动计划\n\n您还有其他相关的问题需要探讨吗？',
      '这是一个很好的问题！让我为您详细分析：\n\n**关键要点：**\n- 数据分析需要明确目标\n- 选择合适的分析方法\n- 确保数据质量和准确性\n\n**建议步骤：**\n1. 数据收集和清理\n2. 探索性数据分析\n3. 建立分析模型\n4. 结果验证和解释\n\n需要我深入解释某个具体步骤吗？',
      '根据您提供的信息，我建议采用以下方法：\n\n**方案A：快速解决**\n- 优点：实施简单，见效快\n- 缺点：可能不够全面\n\n**方案B：系统性解决**\n- 优点：解决根本问题\n- 缺点：需要更多时间和资源\n\n您倾向于选择哪种方案？我可以为您提供更详细的实施指导。'
    ];

    return responses[Math.floor(Math.random() * responses.length)];
  }

  /**
   * 创建新对话
   */
  startNewChat(): void {
    const newSession: ChatSession = {
      id: Date.now().toString(),
      title: '新对话',
      lastMessage: '',
      timestamp: new Date(),
      messageCount: 0
    };

    this.chatSessions.unshift(newSession);
    this.selectSession(newSession);
  }

  /**
   * 处理输入框回车事件
   */
  handleKeyDown(event: KeyboardEvent): void {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      this.sendMessage();
    }
  }

  /**
   * 滚动到消息底部
   */
  private scrollToBottom(): void {
    if (this.messagesContainer) {
      const element = this.messagesContainer.nativeElement;
      element.scrollTop = element.scrollHeight;
    }
  }

  /**
   * 格式化时间显示
   */
  formatTime(date: Date): string {
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

    if (diffDays === 0) {
      return '今天';
    } else if (diffDays < 7) {
      return `${diffDays}天前`;
    } else {
      return date.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' });
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
    return session?.title || '数据问答';
  }
}
