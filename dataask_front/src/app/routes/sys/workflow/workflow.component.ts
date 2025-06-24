import { Component, OnInit, ViewChild, inject } from '@angular/core';
import { STColumn, STComponent } from '@delon/abc/st';
import { SFSchema } from '@delon/form';
import { ModalHelper, _HttpClient } from '@delon/theme';
import { SHARED_IMPORTS } from '@shared';

@Component({
  selector: 'app-sys-workflow',
  imports: [...SHARED_IMPORTS],
  templateUrl: './workflow.component.html',
})
export class SysWorkflowComponent implements OnInit {
  private readonly http = inject(_HttpClient);
  private readonly modal = inject(ModalHelper);

  url = `/workflow`;
  searchSchema: SFSchema = {
    properties: {
      name: {
        type: 'string',
        title: '工作流名称'
      },
      status: {
        type: 'string',
        title: '状态',
        enum: [
          { label: '激活', value: 'active' },
          { label: '暂停', value: 'paused' },
          { label: '已禁用', value: 'disabled' }
        ],
        ui: {
          widget: 'select'
        }
      },
      category: {
        type: 'string',
        title: '分类',
        enum: [
          { label: '审批流程', value: 'approval' },
          { label: '数据处理', value: 'data_processing' },
          { label: '任务调度', value: 'task_scheduling' },
          { label: '通知流程', value: 'notification' }
        ],
        ui: {
          widget: 'select'
        }
      }
    }
  };
  @ViewChild('st') private readonly st!: STComponent;
  columns: STColumn[] = [
    { title: '工作流ID', index: 'id', width: '80px' },
    { title: '名称', index: 'name', width: '200px' },
    { title: '描述', index: 'description', width: '250px' },
    { 
      title: '分类', 
      index: 'category', 
      width: '120px',
      type: 'tag',
      tag: {
        approval: { text: '审批流程', color: 'blue' },
        data_processing: { text: '数据处理', color: 'green' },
        task_scheduling: { text: '任务调度', color: 'orange' },
        notification: { text: '通知流程', color: 'purple' }
      }
    },
    { 
      title: '状态', 
      index: 'status', 
      width: '80px',
      type: 'tag',
      tag: {
        active: { text: '激活', color: 'green' },
        paused: { text: '暂停', color: 'orange' },
        disabled: { text: '已禁用', color: 'red' }
      }
    },
    { title: '步骤数', index: 'steps_count', width: '80px', type: 'number' },
    { title: '执行次数', index: 'execution_count', width: '100px', type: 'number' },
    { title: '成功率', index: 'success_rate', width: '80px' },
    { title: '创建人', index: 'creator', width: '100px' },
    { title: '创建时间', type: 'date', index: 'created_at', width: '150px' },
    { title: '更新时间', type: 'date', index: 'updated_at', width: '150px' },
    {
      title: '操作',
      buttons: [
        { text: '查看', icon: 'eye', click: (item: any) => this.viewWorkflow(item) },
        { text: '编辑', icon: 'edit', click: (item: any) => this.editWorkflow(item) },
        { text: '执行', icon: 'play-circle', iif: (item: any) => item.status === 'active', click: (item: any) => this.executeWorkflow(item) },
        { text: '暂停', icon: 'pause-circle', iif: (item: any) => item.status === 'active', click: (item: any) => this.pauseWorkflow(item) },
        { text: '激活', icon: 'play-circle', iif: (item: any) => item.status !== 'active', click: (item: any) => this.activateWorkflow(item) },
        { text: '删除', icon: 'delete', type: 'del', click: (item: any) => this.deleteWorkflow(item) }
      ]
    }
  ];

  ngOnInit(): void { }

  add(): void {
    console.log('添加新工作流');
  }

  viewWorkflow(item: any): void {
    console.log('查看工作流:', item);
  }

  editWorkflow(item: any): void {
    console.log('编辑工作流:', item);
  }

  executeWorkflow(item: any): void {
    console.log('执行工作流:', item);
    this.st.reload();
  }

  pauseWorkflow(item: any): void {
    console.log('暂停工作流:', item);
    this.st.reload();
  }

  activateWorkflow(item: any): void {
    console.log('激活工作流:', item);
    this.st.reload();
  }

  deleteWorkflow(item: any): void {
    console.log('删除工作流:', item);
    this.st.reload();
  }
}
