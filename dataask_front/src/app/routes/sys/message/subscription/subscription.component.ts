import { Component, OnInit, inject } from '@angular/core';
import { SHARED_IMPORTS } from '@shared';
import { NzMessageService } from 'ng-zorro-antd/message';
import { NzModalService } from 'ng-zorro-antd/modal';

import { SysMessageService, MessageSubscription, MessagePublish } from '../message.service';

@Component({
  selector: 'app-sys-message-subscription',
  imports: [...SHARED_IMPORTS],
  templateUrl: './subscription.component.html'
})
export class SysMessageSubscriptionComponent implements OnInit {
  private readonly messageService = inject(SysMessageService);
  private readonly msg = inject(NzMessageService);
  private readonly modalSrv = inject(NzModalService);

  loading = false;
  subscriptions: MessageSubscription[] = [];
  channels: any[] = [];
  messageTypes: any[] = [];
  lastUpdateTime = '';

  // 发布消息数据
  publishData: MessagePublish = {
    title: '',
    content: '',
    type: '',
    channels: []
  };

  ngOnInit(): void {
    this.loadSubscriptions();
    this.loadChannels();
    this.loadMessageTypes();
  }

  /**
   * 加载订阅列表
   */
  loadSubscriptions(): void {
    this.loading = true;
    // 假设当前用户ID为1
    const currentUserId = 1;

    this.messageService.getUserSubscriptions(currentUserId).subscribe({
      next: res => {
        this.loading = false;
        if (res.success) {
          this.subscriptions = res.data || [];
        } else {
          this.msg.error(res.message || '获取订阅列表失败');
        }
      },
      error: err => {
        this.loading = false;
        this.msg.error('获取订阅列表失败');
        console.error(err);
      }
    });
  }

  /**
   * 加载推送渠道
   */
  loadChannels(): void {
    this.messageService.getMessageChannels().subscribe({
      next: res => {
        if (res.success) {
          this.channels = res.data || [];
        }
      },
      error: err => {
        console.error('加载推送渠道失败:', err);
      }
    });
  }

  /**
   * 加载消息类型
   */
  loadMessageTypes(): void {
    this.messageService.getMessageTypes().subscribe({
      next: res => {
        if (res.success) {
          this.messageTypes = res.data || [];
        }
      },
      error: err => {
        console.error('加载消息类型失败:', err);
      }
    });
  }

  /**
   * 更新订阅设置
   */
  updateSubscription(subscription: MessageSubscription): void {
    this.messageService.updateUserSubscription(subscription.user_id, subscription).subscribe({
      next: res => {
        if (res.success) {
          this.msg.success('订阅设置已更新');
          this.lastUpdateTime = new Date().toLocaleString();
        } else {
          this.msg.error(res.message || '更新订阅设置失败');
        }
      },
      error: err => {
        this.msg.error('更新订阅设置失败');
        console.error(err);
      }
    });
  }

  /**
   * 测试通知
   */
  testNotification(subscription: MessageSubscription): void {
    if (!subscription.enabled) {
      this.msg.warning('请先启用该订阅');
      return;
    }

    this.msg.info('正在发送测试消息...');

    // 模拟测试消息发送
    setTimeout(() => {
      this.msg.success(`测试消息已通过${this.getChannelText(subscription.channel)}发送`);
    }, 1000);
  }

  /**
   * 启用所有订阅
   */
  enableAllSubscriptions(): void {
    this.modalSrv.confirm({
      nzTitle: '确认操作',
      nzContent: '确定要启用所有消息订阅吗？',
      nzOnOk: () => {
        this.subscriptions.forEach(subscription => {
          subscription.enabled = true;
          this.updateSubscription(subscription);
        });
      }
    });
  }

  /**
   * 禁用所有订阅
   */
  disableAllSubscriptions(): void {
    this.modalSrv.confirm({
      nzTitle: '确认操作',
      nzContent: '确定要禁用所有消息订阅吗？',
      nzOnOk: () => {
        this.subscriptions.forEach(subscription => {
          subscription.enabled = false;
          this.updateSubscription(subscription);
        });
      }
    });
  }

  /**
   * 恢复默认设置
   */
  resetToDefault(): void {
    this.modalSrv.confirm({
      nzTitle: '确认操作',
      nzContent: '确定要恢复默认订阅设置吗？此操作将重置所有自定义设置。',
      nzOnOk: () => {
        // 默认设置：系统通知和告警消息启用，业务消息禁用
        this.subscriptions.forEach(subscription => {
          if (subscription.message_type === 'system' || subscription.message_type === 'alert') {
            subscription.enabled = true;
            subscription.channel = 'system';
          } else {
            subscription.enabled = false;
          }
          this.updateSubscription(subscription);
        });
        this.msg.success('已恢复默认设置');
      }
    });
  }

  /**
   * 获取已启用订阅数量
   */
  getEnabledCount(): number {
    return this.subscriptions.filter(sub => sub.enabled).length;
  }

  /**
   * 获取类型文本
   */
  getTypeText(type: string): string {
    const typeMap: Record<string, string> = {
      system: '系统通知',
      business: '业务消息',
      alert: '告警消息'
    };
    return typeMap[type] || type;
  }

  /**
   * 获取类型描述
   */
  getTypeDescription(type: string): string {
    const descMap: Record<string, string> = {
      system: '系统维护、更新等通知',
      business: '业务流程、数据处理相关消息',
      alert: '系统异常、错误告警'
    };
    return descMap[type] || type;
  }

  /**
   * 获取类型颜色
   */
  getTypeColor(type: string): string {
    const colorMap: Record<string, string> = {
      system: 'blue',
      business: 'green',
      alert: 'red'
    };
    return colorMap[type] || 'default';
  }

  /**
   * 获取类型图标
   */
  getTypeIcon(type: string): string {
    const iconMap: Record<string, string> = {
      system: 'setting',
      business: 'dollar',
      alert: 'warning'
    };
    return iconMap[type] || 'message';
  }

  /**
   * 获取渠道文本
   */
  getChannelText(channel: string): string {
    const channelMap: Record<string, string> = {
      email: '邮件',
      sms: '短信',
      system: '系统通知'
    };
    return channelMap[channel] || channel;
  }
}
