import { Component, OnInit, ViewChild, inject } from '@angular/core';
import { STColumn, STComponent } from '@delon/abc/st';
import { SFSchema } from '@delon/form';
import { ModalHelper, _HttpClient } from '@delon/theme';
import { SHARED_IMPORTS } from '@shared';

@Component({
  selector: 'app-sys-message',
  imports: [...SHARED_IMPORTS],
  templateUrl: './message.component.html',
})
export class SysMessageComponent implements OnInit {
  private readonly http = inject(_HttpClient);
  private readonly modal = inject(ModalHelper);

  url = `/message`;
  searchSchema: SFSchema = {
    properties: {
      title: {
        type: 'string',
        title: '消息标题'
      },
      type: {
        type: 'string',
        title: '消息类型',
        enum: [
          { label: '系统通知', value: 'system' },
          { label: '业务消息', value: 'business' },
          { label: '告警消息', value: 'alert' }
        ],
        ui: {
          widget: 'select'
        }
      },
      status: {
        type: 'string',
        title: '状态',
        enum: [
          { label: '已发送', value: 'sent' },
          { label: '草稿', value: 'draft' },
          { label: '已读', value: 'read' }
        ],
        ui: {
          widget: 'select'
        }
      }
    }
  };
  @ViewChild('st') private readonly st!: STComponent;
  columns: STColumn[] = [
    { title: '消息ID', index: 'id', width: '80px' },
    { title: '标题', index: 'title', width: '200px' },
    { 
      title: '类型', 
      index: 'type', 
      width: '100px',
      type: 'tag',
      tag: {
        system: { text: '系统通知', color: 'blue' },
        business: { text: '业务消息', color: 'green' },
        alert: { text: '告警消息', color: 'red' }
      }
    },
    { title: '内容', index: 'content', width: '300px' },
    { title: '接收人', index: 'recipient', width: '120px' },
    { 
      title: '状态', 
      index: 'status', 
      width: '80px',
      type: 'tag',
      tag: {
        sent: { text: '已发送', color: 'green' },
        draft: { text: '草稿', color: 'orange' },
        read: { text: '已读', color: 'blue' }
      }
    },
    { title: '发送时间', type: 'date', index: 'sent_at', width: '150px' },
    { title: '创建时间', type: 'date', index: 'created_at', width: '150px' },
    {
      title: '操作',
      buttons: [
        { text: '查看', icon: 'eye', click: (item: any) => this.viewMessage(item) },
        { text: '编辑', icon: 'edit', iif: (item: any) => item.status === 'draft', click: (item: any) => this.editMessage(item) },
        { text: '删除', icon: 'delete', type: 'del', click: (item: any) => this.deleteMessage(item) }
      ]
    }
  ];

  ngOnInit(): void { }

  add(): void {
    // TODO: 实现添加消息功能
    console.log('添加新消息');
  }

  viewMessage(item: any): void {
    console.log('查看消息:', item);
  }

  editMessage(item: any): void {
    console.log('编辑消息:', item);
  }

  deleteMessage(item: any): void {
    console.log('删除消息:', item);
    this.st.reload();
  }
}
