import { ChangeDetectionStrategy, ChangeDetectorRef, Component, OnInit, ViewChild, inject } from '@angular/core';
import { Router } from '@angular/router';
import { STChange, STColumn, STComponent, STData } from '@delon/abc/st';
import { _HttpClient, SettingsService, TitleService } from '@delon/theme';
import { SHARED_IMPORTS } from '@shared';
import { NzMessageService } from 'ng-zorro-antd/message';
import { NzModalService } from 'ng-zorro-antd/modal';
import { finalize } from 'rxjs';

// 接口定义
export interface Workspace {
  id: number;
  code: string;
  name: string;
  description?: string;
  icon: string;
  color: string;
  workflow_count: number;
  active_workflow_count: number;
  status: string;
  order_num: number;
  created_at?: string;
  updated_at?: string;
}

export interface WorkflowEnhanced {
  id: number;
  name: string;
  description?: string;
  category: string;
  sub_category?: string;
  workspace: string;
  workspace_name: string;
  workspace_icon: string;
  workspace_color: string;
  status: string;
  trigger_type: string;
  priority: string;
  version: string;
  step_count: number;
  execution_count: number;
  success_rate: number;
  creator_name: string;
  last_execution_time?: string;
  created_at: string;
  updated_at: string;
  dag_id?: string;
}

export interface WorkflowQuery {
  pi: number;
  ps: number;
  keyword: string;
  status?: string;
  workspace?: string;
  category?: string;
  trigger_type?: string;
}

@Component({
  selector: 'app-sys-workflow',
  templateUrl: './workflow.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [...SHARED_IMPORTS]
})
export class SysWorkflowComponent implements OnInit {
  private readonly http = inject(_HttpClient);
  private readonly msg = inject(NzMessageService);
  private readonly modalSrv = inject(NzModalService);
  private readonly cdr = inject(ChangeDetectorRef);
  private readonly router = inject(Router);
  private readonly titleSrv = inject(TitleService);
  private readonly settings = inject(SettingsService);

  // 查询参数
  q: WorkflowQuery = {
    pi: 1,
    ps: 10,
    keyword: '',
    status: undefined,
    workspace: undefined,
    category: undefined,
    trigger_type: undefined
  };

  // 数据和状态
  data: any[] = [];
  loading = false;
  selectedRows: STData[] = [];
  expandForm = false;

  // 工作域相关
  workspaces: Workspace[] = [];
  selectedWorkspace?: Workspace;
  showWorkspaceSelector = true;

  // 表格分页总数
  total = 0;

  // 选项数据
  statusOptions = [
    { label: '全部', value: undefined },
    { label: '激活', value: 'active' },
    { label: '非激活', value: 'inactive' },
    { label: '已禁用', value: 'disabled' },
    { label: '已删除', value: 'deleted' }
  ];

  categoryOptions = [
    { label: '全部', value: undefined },
    { label: '用户管理', value: 'user_management' },
    { label: '客户服务', value: 'customer_service' },
    { label: '审批流程', value: 'approval' },
    { label: '数据处理', value: 'data_processing' },
    { label: 'ETL流程', value: 'etl_process' },
    { label: '任务调度', value: 'task_scheduling' },
    { label: '通知流程', value: 'notification' },
    { label: '模型训练', value: 'model_training' }
  ];

  triggerTypeOptions = [
    { label: '全部', value: undefined },
    { label: '手动触发', value: 'manual' },
    { label: '自动触发', value: 'automatic' },
    { label: '计划触发', value: 'scheduled' },
    { label: '事件触发', value: 'event' }
  ];

  @ViewChild('st', { static: true })
  st!: STComponent;

  // 表格列配置
  columns: STColumn[] = [
    { title: '', index: 'key', type: 'checkbox' },
    {
      title: 'ID',
      index: 'id',
      width: 80,
      type: 'number',
      sort: true
    },
    {
      title: '工作流',
      index: 'name',
      width: 250
    },
    {
      title: '工作域',
      index: 'workspace_name',
      width: 120
    },
    {
      title: '分类',
      index: 'category',
      width: 100,
      type: 'tag',
      tag: {
        user_management: { text: '用户管理', color: 'blue' },
        customer_service: { text: '客户服务', color: 'cyan' },
        approval: { text: '审批', color: 'green' },
        data_processing: { text: '数据处理', color: 'lime' },
        etl_process: { text: 'ETL', color: 'orange' },
        task_scheduling: { text: '调度', color: 'purple' },
        notification: { text: '通知', color: 'magenta' },
        model_training: { text: '模型训练', color: 'volcano' }
      }
    },
    {
      title: '状态',
      index: 'status',
      width: 80,
      type: 'tag',
      tag: {
        active: { text: '激活', color: 'green' },
        inactive: { text: '非激活', color: 'orange' },
        disabled: { text: '已禁用', color: 'red' },
        deleted: { text: '已删除', color: 'default' }
      }
    },
    {
      title: '触发方式',
      index: 'trigger_type',
      width: 100,
      type: 'tag',
      tag: {
        manual: { text: '手动', color: 'blue' },
        automatic: { text: '自动', color: 'green' },
        scheduled: { text: '计划', color: 'cyan' },
        event: { text: '事件', color: 'purple' }
      }
    },
    {
      title: '步骤统计',
      render: 'stepStatsTpl',
      width: 120
    },
    {
      title: '版本',
      index: 'version',
      width: 80
    },
    {
      title: '创建人',
      index: 'creator_name',
      width: 100
    },
    {
      title: '最后执行',
      index: 'last_execution_time',
      width: 150,
      type: 'date',
      dateFormat: 'yyyy-MM-dd HH:mm:ss'
    },
    {
      title: '创建时间',
      index: 'created_at',
      width: 150,
      type: 'date',
      dateFormat: 'yyyy-MM-dd HH:mm:ss',
      sort: true
    },
    {
      title: '操作',
      render: 'actionTpl',
      width: 200,
      fixed: 'right'
    }
  ];

  ngOnInit(): void {
    this.titleSrv.setTitle('工作流管理');
    this.loadWorkspaces();
    this.getData();
  }

  async loadWorkspaces(): Promise<void> {
    try {
      const result = await this.http.get('/api/workflow/workspaces').toPromise();
      if (result.code === 200) {
        this.workspaces = result.data;
        this.cdr.detectChanges();
      } else {
        this.msg.error(result.message || '加载工作域失败');
      }
    } catch (error) {
      this.msg.error('加载工作域失败');
      console.error(error);
    }
  }

  getData(): void {
    this.loading = true;
    
    // 构建查询参数，过滤掉undefined和空值
    const rawParams = { ...this.q };
    
    // 如果选择了工作域，添加到查询参数
    if (this.selectedWorkspace) {
      rawParams.workspace = this.selectedWorkspace.code;
    }
    
    // 过滤掉undefined、null、空字符串的参数
    const params: any = {};
    Object.keys(rawParams).forEach(key => {
      const value = rawParams[key as keyof WorkflowQuery];
      if (value !== undefined && value !== null && value !== '') {
        params[key] = value;
      }
    });



    this.http
      .get('/api/workflow/list', params)
      .pipe(finalize(() => {
        this.loading = false;
        this.cdr.detectChanges();
      }))
      .subscribe({
        next: result => {
          if (result.code === 200) {
            const apiData = result.data;
            if (apiData && apiData.list) {
              this.data = apiData.list;
              this.total = apiData.total || 0;
            } else {
              this.data = [];
              this.total = 0;
            }
            this.cdr.detectChanges();
          } else {
            this.msg.error(result.message || '获取工作流列表失败');
          }
        },
        error: error => {
          this.msg.error('获取工作流列表失败');
          console.error(error);
        }
      });
  }

  stChange(e: STChange): void {
    switch (e.type) {
      case 'checkbox':
        this.selectedRows = e.checkbox!;
        this.cdr.detectChanges();
        break;
      case 'filter':
        this.getData();
        break;
      case 'pi':
        this.q.pi = e.pi!;
        this.getData();
        break;
      case 'ps':
        this.q.ps = e.ps!;
        this.getData();
        break;
      case 'sort':
        this.getData();
        break;
    }
  }

  reset(): void {
    this.q = {
      pi: 1,
      ps: 10,
      keyword: '',
      status: undefined,
      workspace: undefined,
      category: undefined,
      trigger_type: undefined
    };
    this.selectedWorkspace = undefined;
    this.getData();
  }

  onWorkspaceChange(workspace: Workspace | undefined): void {
    this.selectedWorkspace = workspace;
    this.q.workspace = workspace?.code;
    this.getData();
  }

  add(): void {
    this.msg.info('工作流创建功能正在开发中');
  }

  viewWorkflow(item: WorkflowEnhanced): void {
    this.msg.info(`查看工作流: ${item.name}`);
  }

  editWorkflow(item: WorkflowEnhanced): void {
    this.msg.info(`编辑工作流: ${item.name}`);
  }

  executeWorkflow(item: WorkflowEnhanced): void {
    this.modalSrv.confirm({
      nzTitle: '确认执行',
      nzContent: `确定要执行工作流 "${item.name}" 吗？`,
      nzOkText: '执行',
      nzCancelText: '取消',
      nzOkType: 'primary',
      nzOnOk: () => {
        this.performExecuteWorkflow(item);
      }
    });
  }

  activateWorkflow(item: WorkflowEnhanced): void {
    this.modalSrv.confirm({
      nzTitle: '确认激活',
      nzContent: `确定要激活工作流 "${item.name}" 吗？`,
      nzOkText: '激活',
      nzCancelText: '取消',
      nzOkType: 'primary',
      nzOnOk: () => {
        this.performActivateWorkflow(item);
      }
    });
  }

  deleteWorkflow(item: WorkflowEnhanced): void {
    this.modalSrv.confirm({
      nzTitle: '确认删除',
      nzContent: `确定要删除工作流 "${item.name}" 吗？此操作不可恢复！`,
      nzOkText: '删除',
      nzCancelText: '取消',
      nzOkType: 'primary',
      nzOnOk: () => {
        this.performDeleteWorkflow(item);
      }
    });
  }

  // 批量操作
  batchActivate(): void {
    if (this.selectedRows.length === 0) {
      this.msg.warning('请选择要激活的工作流');
      return;
    }
    
    this.modalSrv.confirm({
      nzTitle: '批量激活',
      nzContent: `确定要激活选中的 ${this.selectedRows.length} 个工作流吗？`,
      nzOkText: '激活',
      nzCancelText: '取消',
      nzOkType: 'primary',
      nzOnOk: () => {
        this.performBatchActivate();
      }
    });
  }

  batchDeactivate(): void {
    if (this.selectedRows.length === 0) {
      this.msg.warning('请选择要停用的工作流');
      return;
    }
    
    this.modalSrv.confirm({
      nzTitle: '批量停用',
      nzContent: `确定要停用选中的 ${this.selectedRows.length} 个工作流吗？`,
      nzOkText: '停用',
      nzCancelText: '取消',
      nzOkType: 'primary',
      nzOnOk: () => {
        this.performBatchDeactivate();
      }
    });
  }

  batchDelete(): void {
    if (this.selectedRows.length === 0) {
      this.msg.warning('请选择要删除的工作流');
      return;
    }
    
    this.modalSrv.confirm({
      nzTitle: '批量删除',
      nzContent: `确定要删除选中的 ${this.selectedRows.length} 个工作流吗？此操作不可恢复！`,
      nzOkText: '删除',
      nzCancelText: '取消',
      nzOkType: 'primary',
      nzOnOk: () => {
        this.performBatchDelete();
      }
    });
  }

  // 执行操作的具体实现
  private async performExecuteWorkflow(item: WorkflowEnhanced): Promise<void> {
    try {
      const result = await this.http.post(`/api/workflow/execute/${item.id}`, {}).toPromise();
      if (result.success) {
        this.msg.success(`工作流 "${item.name}" 执行已启动`);
        this.getData();
      } else {
        this.msg.error(result.message || '执行工作流失败');
      }
    } catch (error) {
      this.msg.error('执行工作流失败');
      console.error(error);
    }
  }

  private async performActivateWorkflow(item: WorkflowEnhanced): Promise<void> {
    try {
      const result = await this.http.put(`/api/workflow/${item.id}/activate`, {}).toPromise();
      if (result.success) {
        this.msg.success(`工作流 "${item.name}" 已激活`);
        this.getData();
      } else {
        this.msg.error(result.message || '激活工作流失败');
      }
    } catch (error) {
      this.msg.error('激活工作流失败');
      console.error(error);
    }
  }

  private async performDeleteWorkflow(item: WorkflowEnhanced): Promise<void> {
    try {
      const result = await this.http.delete(`/api/workflow/${item.id}`).toPromise();
      if (result.success) {
        this.msg.success(`工作流 "${item.name}" 已删除`);
        this.getData();
      } else {
        this.msg.error(result.message || '删除工作流失败');
      }
    } catch (error) {
      this.msg.error('删除工作流失败');
      console.error(error);
    }
  }

  private async performBatchActivate(): Promise<void> {
    try {
      const ids = this.selectedRows.map(row => row['id']);
      const result = await this.http.put('/api/workflow/batch/activate', { ids }).toPromise();
      if (result.success) {
        this.msg.success(`已激活 ${ids.length} 个工作流`);
        this.getData();
        this.selectedRows = [];
      } else {
        this.msg.error(result.message || '批量激活失败');
      }
    } catch (error) {
      this.msg.error('批量激活失败');
      console.error(error);
    }
  }

  private async performBatchDeactivate(): Promise<void> {
    try {
      const ids = this.selectedRows.map(row => row['id']);
      const result = await this.http.put('/api/workflow/batch/deactivate', { ids }).toPromise();
      if (result.success) {
        this.msg.success(`已停用 ${ids.length} 个工作流`);
        this.getData();
        this.selectedRows = [];
      } else {
        this.msg.error(result.message || '批量停用失败');
      }
    } catch (error) {
      this.msg.error('批量停用失败');
      console.error(error);
    }
  }

  private async performBatchDelete(): Promise<void> {
    try {
      const ids = this.selectedRows.map(row => row['id']);
      const result = await this.http.delete('/api/workflow/batch', { body: { ids } }).toPromise();
      if (result.success) {
        this.msg.success(`已删除 ${ids.length} 个工作流`);
        this.getData();
        this.selectedRows = [];
      } else {
        this.msg.error(result.message || '批量删除失败');
      }
    } catch (error) {
      this.msg.error('批量删除失败');
      console.error(error);
    }
  }
}
