import { ChangeDetectionStrategy, ChangeDetectorRef, Component, inject } from '@angular/core';
import { NoticeIconList, NoticeIconModule, NoticeIconSelect, NoticeItem } from '@delon/abc/notice-icon';
import { _HttpClient } from '@delon/theme';
import { formatDistanceToNow } from 'date-fns';
import { zhCN } from 'date-fns/locale';
import { NzI18nService } from 'ng-zorro-antd/i18n';
import { NzMessageService } from 'ng-zorro-antd/message';

@Component({
  selector: 'header-notify',
  template: `
    <notice-icon
      [data]="data"
      [count]="count"
      [loading]="loading"
      btnClass="alain-default__nav-item"
      btnIconClass="alain-default__nav-item-icon"
      (select)="select($event)"
      (clear)="clear($event)"
      (popoverVisibleChange)="loadData()"
    />
  `,
  changeDetection: ChangeDetectionStrategy.OnPush,
  standalone: true,
  imports: [NoticeIconModule]
})
export class HeaderNotifyComponent {
  private readonly msg = inject(NzMessageService);
  private readonly nzI18n = inject(NzI18nService);
  private readonly cdr = inject(ChangeDetectorRef);
  private readonly http = inject(_HttpClient);

  data: NoticeItem[] = [
    {
      title: '通知',
      list: [],
      emptyText: '你已查看所有通知',
      emptyImage: 'https://gw.alipayobjects.com/zos/rmsportal/wAhyIChODzsoKIOBHcBk.svg',
      clearText: '清空通知'
    },
    {
      title: '消息',
      list: [],
      emptyText: '您已读完所有消息',
      emptyImage: 'https://gw.alipayobjects.com/zos/rmsportal/sAuJeJzSKbUmHfBQRzmZ.svg',
      clearText: '清空消息'
    },
    {
      title: '事件',
      list: [],
      emptyText: '暂无系统事件',
      emptyImage: 'https://gw.alipayobjects.com/zos/rmsportal/HsIsxMZiWKrNUavQUXqx.svg',
      clearText: '清空事件'
    }
  ];
  count = 0;
  loading = false;

  private formatNoticeDate(date: string | number | Date | undefined): string {
    if (!date) return '未知时间';
    try {
      const dateObj = typeof date === 'string' || typeof date === 'number' ? new Date(date) : date;
      if (isNaN(dateObj.getTime())) return '未知时间';
      return formatDistanceToNow(dateObj, { locale: zhCN, addSuffix: true });
    } catch (error) {
      console.error('日期格式化错误:', error);
      return '未知时间';
    }
  }

  private updateNoticeData(notices: NoticeIconList[]): NoticeItem[] {
    const data = this.data.slice();
    data.forEach(i => (i.list = []));
    notices.forEach(item => {
      const newItem = { ...item } as NoticeIconList;
      if (newItem.datetime) {
        newItem.datetime = this.formatNoticeDate(newItem.datetime);
      }
      if (newItem.extra && newItem['status']) {
        newItem['color'] = ({
          normal: undefined,
          processing: 'blue',
          error: 'red',
          warning: 'gold'
        } as Record<string, string | undefined>)[newItem['status']];
      }
      data.find(w => w.title === newItem['type'])!.list.push(newItem);
    });
    return data;
  }

  loadData(): void {
    if (this.loading) return;
    this.loading = true;
    
    this.http.get('/api/notice').subscribe({
      next: (res: any) => {
        const notices = res.map((item: any) => ({
          ...item,
          datetime: item.updatedAt || new Date().toISOString(),
          type: '通知'
        }));
        
        this.http.get('/api/activities').subscribe({
          next: (activities: any) => {
            const messages = activities.map((item: any) => ({
              id: item['id'],
              avatar: item.user.avatar,
              title: item.template,
              description: `${item.group.name} - ${item.project.name}`,
              datetime: item.updatedAt || new Date().toISOString(),
              type: '消息'
            }));
            
            const allNotices = [...notices, ...messages];
            this.data = this.updateNoticeData(allNotices);
            this.count = allNotices.filter(item => !item['read']).length;
            this.loading = false;
            this.cdr.detectChanges();
          },
          error: () => {
            this.loading = false;
            this.msg.error('获取消息列表失败');
            this.cdr.detectChanges();
          }
        });
      },
      error: () => {
        this.loading = false;
        this.msg.error('获取通知列表失败');
        this.cdr.detectChanges();
      }
    });
  }

  clear(type: string): void {
    this.msg.success(`清空了 ${type}`);
    const data = this.data.slice();
    const target = data.find(w => w.title === type);
    if (target) {
      target.list = [];
    }
    this.data = data;
    this.cdr.detectChanges();
  }

  select(res: NoticeIconSelect): void {
    this.msg.success(`查看了 ${res.title} 中的 ${res.item.title}`);
    const data = this.data.slice();
    const target = data.find(w => w.title === res.title);
    if (target) {
      const item = target.list.find(w => w['id'] === res.item['id']);
      if (item) {
        item['read'] = true;
        this.count -= 1;
      }
    }
    this.data = data;
    this.cdr.detectChanges();
  }
} 