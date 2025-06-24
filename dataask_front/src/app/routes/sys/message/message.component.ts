import { Component, OnInit, ViewChild, inject, TemplateRef } from '@angular/core';
import { STColumn, STComponent, STData, STChange } from '@delon/abc/st';
import { SFSchema } from '@delon/form';
import { ModalHelper, _HttpClient } from '@delon/theme';
import { NzMessageService } from 'ng-zorro-antd/message';
import { NzModalService } from 'ng-zorro-antd/modal';
import { SHARED_IMPORTS } from '@shared';
import { SysMessageService, Message } from './message.service';

@Component({
  selector: 'app-sys-message',
  imports: [...SHARED_IMPORTS],
  templateUrl: './message.component.html',
})
export class SysMessageComponent implements OnInit {
  private readonly http = inject(_HttpClient);
  private readonly modal = inject(ModalHelper);
  private readonly messageService = inject(SysMessageService);
  private readonly msg = inject(NzMessageService);
  private readonly modalSrv = inject(NzModalService);

  loading = false;
  expandForm = false;
  selectedRows: STData[] = [];
  data: any[] = [];
  
  // 查询参数
  q: any = {
    pi: 1,
    ps: 20,
    title: '',
    type: '',
    status: '',
    sender: ''
  };

  // 编辑状态
  isEditMode = false;
  editingMessage: Partial<Message> = {};
  viewingMessage: any = {};

  // 选项数据
  typeOptions = [
    { label: '系统通知', value: 'system' },
    { label: '业务消息', value: 'business' },
    { label: '告警消息', value: 'alert' }
  ];

  statusOptions = [
    { label: '已发送', value: 'sent' },
    { label: '草稿', value: 'draft' },
    { label: '已读', value: 'read' }
  ];

  userOptions: any[] = [];

  searchSchema: SFSchema = {
    properties: {
      title: {
        type: 'string',
        title: '消息标题'
      },
      type: {
        type: 'string',
        title: '消息类型',
        enum: this.typeOptions,
        ui: {
          widget: 'select'
        }
      },
      status: {
        type: 'string',
        title: '状态',
        enum: this.statusOptions,
        ui: {
          widget: 'select'
        }
      }
    }
  };

  @ViewChild('st') private readonly st!: STComponent;
  
  columns: STColumn[] = [
    { title: '', index: 'id', type: 'checkbox' },
    { title: '消息ID', index: 'id', width: '80px' },
    { title: '标题', index: 'title', width: '200px' },
    { 
      title: '类型', 
      index: 'type', 
      width: '100px',
      render: 'type'
    },
    { title: '内容', index: 'content', width: '300px', className: 'text-truncate' },
    { title: '接收人', index: 'recipient', width: '120px' },
    { 
      title: '状态', 
      index: 'status', 
      width: '80px',
      render: 'status'
    },
    { title: '发送人', index: 'sender', width: '120px' },
    { title: '发送时间', type: 'date', index: 'sent_at', width: '150px' },
    { title: '创建时间', type: 'date', index: 'created_at', width: '150px' },
    {
      title: '操作',
      width: '200px',
      buttons: [
        { 
          text: '查看', 
          icon: 'eye', 
          click: (item: any) => this.viewMessage(item)
        },
        { 
          text: '编辑', 
          icon: 'edit', 
          iif: (item: any) => item.status === 'draft', 
          click: (item: any) => this.editMessage(item)
        },
        { 
          text: '发送', 
          icon: 'send', 
          iif: (item: any) => item.status === 'draft',
          click: (item: any) => this.sendMessage(item)
        },
        { 
          text: '删除', 
          icon: 'delete', 
          type: 'del', 
          click: (item: any) => this.deleteMessage(item)
        }
      ]
    }
  ];

  ngOnInit(): void {
    this.getData();
    this.loadUserOptions();
  }

  /**
   * 获取数据
   */
  getData(): void {
    this.loading = true;
    this.messageService.getMessages(this.q).subscribe({
      next: (res) => {
        this.loading = false;
        if (res.code === 200) {
          this.data = res.data.list || res.data || [];
        } else {
          this.msg.error(res.message || '获取消息列表失败');
        }
      },
      error: (err) => {
        this.loading = false;
        this.msg.error('获取消息列表失败');
        console.error(err);
      }
    });
  }

  /**
   * 重置搜索
   */
  reset(): void {
    this.q = {
      pi: 1,
      ps: 20,
      title: '',
      type: '',
      status: '',
      sender: ''
    };
    this.getData();
  }

  /**
   * 表格变化
   */
  stChange(e: STChange): void {
    switch (e.type) {
      case 'checkbox':
        this.selectedRows = e.checkbox!;
        break;
      case 'pi':
        this.q.pi = e.pi;
        this.getData();
        break;
      case 'ps':
        this.q.ps = e.ps;
        this.getData();
        break;
    }
  }

  /**
   * 加载用户选项
   */
  loadUserOptions(): void {
    this.messageService.getUsers().subscribe({
      next: (res) => {
        if (res.code === 200) {
          this.userOptions = res.data || [];
        }
      },
      error: (err) => {
        console.error('加载用户列表失败:', err);
      }
    });
  }

  /**
   * 新增消息
   */
  addMessage(modalContent: TemplateRef<void>): void {
    this.isEditMode = false;
    this.editingMessage = {
      title: '',
      content: '',
      type: 'system',
      status: 'draft',
      recipient: ''
    };
    
    this.modalSrv.create({
      nzTitle: '新增消息',
      nzContent: modalContent,
      nzWidth: 600,
      nzOnOk: () => this.saveMessage()
    });
  }

  /**
   * 编辑消息
   */
  editMessage(item: any): void {
    this.isEditMode = true;
    this.editingMessage = { ...item };
    
    this.modal.create(SysMessageComponent, '这里应该是编辑消息的表单', {
      size: 'md'
    }).subscribe(() => {
      this.getData();
    });
  }

  /**
   * 查看消息
   */
  viewMessage(item: any): void {
    this.viewingMessage = item;
    this.messageService.getMessage(item.id).subscribe({
      next: (res) => {
        if (res.code === 200) {
          this.viewingMessage = res.data;
          // 这里应该打开查看详情的模态框
          this.modalSrv.create({
            nzTitle: '消息详情',
            nzContent: '这里应该是查看详情的内容',
            nzWidth: 800,
            nzFooter: null
          });
        }
      },
      error: (err) => {
        this.msg.error('获取消息详情失败');
      }
    });
  }

  /**
   * 发送消息
   */
  sendMessage(item: any): void {
    this.modalSrv.confirm({
      nzTitle: '确认发送',
      nzContent: `确定要发送消息"${item.title}"吗？`,
      nzOnOk: () => {
        this.messageService.sendMessage(item.id).subscribe({
          next: (res) => {
            if (res.code === 200) {
              this.msg.success('消息发送成功');
              this.getData();
            } else {
              this.msg.error(res.message || '消息发送失败');
            }
          },
          error: (err) => {
            this.msg.error('消息发送失败');
          }
        });
      }
    });
  }

  /**
   * 删除消息
   */
  deleteMessage(item: any): void {
    this.modalSrv.confirm({
      nzTitle: '确认删除',
      nzContent: `确定要删除消息"${item.title}"吗？`,
      nzOnOk: () => {
        this.messageService.deleteMessage(item.id).subscribe({
          next: (res) => {
            if (res.code === 200) {
              this.msg.success('删除成功');
              this.getData();
            } else {
              this.msg.error(res.message || '删除失败');
            }
          },
          error: (err) => {
            this.msg.error('删除失败');
          }
        });
      }
    });
  }

  /**
   * 保存消息
   */
  saveMessage(): void {
    if (!this.editingMessage.title || !this.editingMessage.content || !this.editingMessage.recipient) {
      this.msg.error('请填写完整的消息信息');
      return;
    }

    const request = this.isEditMode 
      ? this.messageService.updateMessage(this.editingMessage.id!, this.editingMessage)
      : this.messageService.createMessage(this.editingMessage);

    request.subscribe({
      next: (res) => {
        if (res.code === 200) {
          this.msg.success(this.isEditMode ? '更新成功' : '创建成功');
          this.getData();
        } else {
          this.msg.error(res.message || '操作失败');
        }
      },
      error: (err) => {
        this.msg.error('操作失败');
      }
    });
  }

  /**
   * 批量发送
   */
  batchSend(): void {
    if (this.selectedRows.length === 0) {
      this.msg.warning('请选择要发送的消息');
      return;
    }

    const ids = this.selectedRows.map(row => row['id']);
    this.modalSrv.confirm({
      nzTitle: '批量发送',
      nzContent: `确定要发送选中的 ${ids.length} 条消息吗？`,
      nzOnOk: () => {
        this.messageService.batchSendMessages(ids).subscribe({
          next: (res) => {
            if (res.code === 200) {
              this.msg.success('批量发送成功');
              this.getData();
              this.st.clearCheck();
            } else {
              this.msg.error(res.message || '批量发送失败');
            }
          },
          error: (err) => {
            this.msg.error('批量发送失败');
          }
        });
      }
    });
  }

  /**
   * 批量删除
   */
  batchDelete(): void {
    if (this.selectedRows.length === 0) {
      this.msg.warning('请选择要删除的消息');
      return;
    }

    const ids = this.selectedRows.map(row => row['id']);
    this.modalSrv.confirm({
      nzTitle: '批量删除',
      nzContent: `确定要删除选中的 ${ids.length} 条消息吗？`,
      nzOnOk: () => {
        this.messageService.batchDeleteMessages(ids).subscribe({
          next: (res) => {
            if (res.code === 200) {
              this.msg.success('批量删除成功');
              this.getData();
              this.st.clearCheck();
            } else {
              this.msg.error(res.message || '批量删除失败');
            }
          },
          error: (err) => {
            this.msg.error('批量删除失败');
          }
        });
      }
    });
  }

  /**
   * 刷新统计信息
   */
  refreshStats(): void {
    this.messageService.getMessageStats().subscribe({
      next: (res) => {
        if (res.code === 200) {
          this.modalSrv.info({
            nzTitle: '消息统计',
            nzContent: `总消息数: ${res.data.total}, 已发送: ${res.data.sent}, 草稿: ${res.data.draft}`
          });
        }
      },
      error: (err) => {
        this.msg.error('获取统计信息失败');
      }
    });
  }

  /**
   * 获取状态文本
   */
  getStatusText(status: string): string {
    const statusMap: { [key: string]: string } = {
      'sent': '已发送',
      'draft': '草稿',
      'read': '已读'
    };
    return statusMap[status] || status;
  }

  /**
   * 获取类型文本
   */
  getTypeText(type: string): string {
    const typeMap: { [key: string]: string } = {
      'system': '系统通知',
      'business': '业务消息',
      'alert': '告警消息'
    };
    return typeMap[type] || type;
  }

  /**
   * 获取类型颜色
   */
  getTypeColor(type: string): string {
    const colorMap: { [key: string]: string } = {
      'system': 'blue',
      'business': 'green',
      'alert': 'red'
    };
    return colorMap[type] || 'default';
  }
}
