import { ChangeDetectionStrategy, ChangeDetectorRef, Component, inject } from '@angular/core';
import { NoticeIconList, NoticeIconModule, NoticeIconSelect, NoticeItem } from '@delon/abc/notice-icon';
import { add, formatDistanceToNow, parse } from 'date-fns';
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
  imports: [NoticeIconModule]
})
export class HeaderNotifyComponent {
  private readonly msg = inject(NzMessageService);

  private readonly cdr = inject(ChangeDetectorRef);

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
      title: '待办',
      list: [],
      emptyText: '你已完成所有待办',
      emptyImage: 'https://gw.alipayobjects.com/zos/rmsportal/HsIsxMZiWKrNUavQUXqx.svg',
      clearText: '清空待办'
    }
  ];
  count = 5;
  loading = false;

  private updateNoticeData(notices: NoticeIconList[]): NoticeItem[] {
    const data = this.data.slice();
    data.forEach(i => (i.list = []));

    notices.forEach(item => {
      const newItem = { ...item } as NoticeIconList;
      if (typeof newItem.datetime === 'string') {
        newItem.datetime = parse(newItem.datetime, 'yyyy-MM-dd', new Date());
      }
      if (newItem.datetime) {
        newItem.datetime = formatDistanceToNow(newItem.datetime as Date);
      }
      if (newItem.extra && newItem['status']) {
        newItem['color'] = (
          {
            todo: undefined,
            processing: 'blue',
            urgent: 'red',
            doing: 'gold'
          } as Record<string, string | undefined>
        )[newItem['status']];
      }
      data.find(w => w.title === newItem['type'])!.list.push(newItem);
    });
    return data;
  }

  loadData(): void {
    if (this.loading) {
      return;
    }
    this.loading = true;
    setTimeout(() => {
      const now = new Date();
      this.data = this.updateNoticeData([
        {
          id: '000000001',
          avatar: 'assets/logo.svg',
          title: '数据源连接异常提醒',
          datetime: add(now, { minutes: -30 }),
          type: '通知'
        },
        {
          id: '000000002',
          avatar: 'assets/logo.svg',
          title: '新增了5个AI查询请求',
          datetime: add(now, { hours: -2 }),
          type: '通知'
        },
        {
          id: '000000003',
          avatar: 'assets/logo.svg',
          title: '系统版本更新通知',
          datetime: add(now, { days: -1 }),
          read: true,
          type: '通知'
        },
        {
          id: '000000004',
          avatar: 'assets/logo.svg',
          title: '管理员 发布了系统公告',
          description: '洞察魔方平台功能升级，新增大模型管理功能',
          datetime: add(now, { hours: -3 }),
          type: '消息'
        },
        {
          id: '000000005',
          avatar: 'assets/logo.svg',
          title: '张三 分享了数据报告',
          description: 'Q4季度客户行为分析报告已完成，请查看',
          datetime: add(now, { hours: -5 }),
          type: '消息'
        },
        {
          id: '000000006',
          title: '完成月度数据备份',
          description: '需要在今天晚上23:59前完成数据备份任务',
          extra: '今日截止',
          status: 'urgent',
          type: '待办'
        },
        {
          id: '000000007',
          title: '更新系统文档',
          description: '更新AI引擎使用说明文档',
          extra: '进行中',
          status: 'processing',
          type: '待办'
        },
        {
          id: '000000008',
          title: '审核新用户申请',
          description: '有3个新用户申请等待审核',
          extra: '待处理',
          status: 'todo',
          type: '待办'
        }
      ]);

      this.loading = false;
      this.cdr.detectChanges();
    }, 500);
  }

  clear(type: string): void {
    this.msg.success(`清空了 ${type}`);
  }

  select(res: NoticeIconSelect): void {
    this.msg.success(`点击了 ${res.title} 的 ${res.item.title}`);
  }
}
