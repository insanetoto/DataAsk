import { Component, OnInit, ViewChild, inject } from '@angular/core';
import { STColumn, STComponent } from '@delon/abc/st';
import { SFSchema } from '@delon/form';
import { ModalHelper, _HttpClient } from '@delon/theme';
import { SHARED_IMPORTS } from '@shared';

interface DataSource {
  id: number;
  name: string;
  type: string;
  host: string;
  port: number;
  database: string;
  username: string;
  status: string;
  description: string;
  createdAt: string;
  updatedAt: string;
}

@Component({
  selector: 'app-ai-engine-datasource',
  imports: [...SHARED_IMPORTS],
  templateUrl: './datasource.component.html',
})
export class AiEngineDatasourceComponent implements OnInit {
  private readonly http = inject(_HttpClient);
  private readonly modal = inject(ModalHelper);

  url = `/api/datasources`;
  
  searchSchema: SFSchema = {
    properties: {
      name: {
        type: 'string',
        title: '数据源名称',
        ui: {
          placeholder: '请输入数据源名称'
        }
      },
      type: {
        type: 'string',
        title: '数据源类型',
        enum: [
          { label: '全部', value: '' },
          { label: 'MySQL', value: 'mysql' },
          { label: 'PostgreSQL', value: 'postgresql' },
          { label: 'Oracle', value: 'oracle' },
          { label: 'SQL Server', value: 'sqlserver' },
          { label: 'MongoDB', value: 'mongodb' },
          { label: 'Redis', value: 'redis' },
          { label: 'Elasticsearch', value: 'elasticsearch' }
        ],
        default: ''
      },
      status: {
        type: 'string',
        title: '连接状态',
        enum: [
          { label: '全部', value: '' },
          { label: '已连接', value: 'connected' },
          { label: '连接失败', value: 'failed' },
          { label: '未测试', value: 'untested' }
        ],
        default: ''
      }
    }
  };

  @ViewChild('st') private readonly st!: STComponent;
  
  columns: STColumn[] = [
    { title: 'ID', index: 'id', width: 80 },
    { 
      title: '数据源名称', 
      index: 'name',
      render: 'nameRender'
    },
    { 
      title: '类型', 
      index: 'type',
      type: 'tag',
      tag: {
        mysql: { text: 'MySQL', color: 'blue' },
        postgresql: { text: 'PostgreSQL', color: 'cyan' },
        oracle: { text: 'Oracle', color: 'red' },
        sqlserver: { text: 'SQL Server', color: 'purple' },
        mongodb: { text: 'MongoDB', color: 'green' },
        redis: { text: 'Redis', color: 'orange' },
        elasticsearch: { text: 'Elasticsearch', color: 'gold' }
      }
    },
    { 
      title: '连接地址', 
      index: 'connection',
      format: (item: DataSource) => `${item.host}:${item.port}/${item.database || ''}`
    },
    { 
      title: '用户名', 
      index: 'username'
    },
    { 
      title: '连接状态', 
      index: 'status',
      type: 'badge',
      badge: {
        connected: { text: '已连接', color: 'success' },
        failed: { text: '连接失败', color: 'error' },
        untested: { text: '未测试', color: 'default' }
      }
    },
    { 
      title: '描述', 
      index: 'description',
      width: 200,
      render: 'descriptionRender'
    },
    { 
      title: '创建时间', 
      index: 'createdAt',
      type: 'date',
      dateFormat: 'yyyy-MM-dd HH:mm'
    },
    {
      title: '操作',
      buttons: [
        { 
          text: '测试连接', 
          icon: 'api',
          type: 'link',
          click: (item: DataSource) => this.testConnection(item) 
        },
        { 
          text: '编辑', 
          icon: 'edit',
          type: 'link',
          click: (item: DataSource) => this.edit(item) 
        },
        { 
          text: '删除', 
          icon: 'delete',
          type: 'del',
          pop: {
            title: '确认删除',
            okText: '确定',
            cancelText: '取消'
          },
          click: (item: DataSource) => this.delete(item) 
        }
      ],
      width: 180
    }
  ];

  // 模拟数据
  mockData: DataSource[] = [
    {
      id: 1,
      name: '主数据库',
      type: 'mysql',
      host: '192.168.1.100',
      port: 3306,
      database: 'dataask_main',
      username: 'root',
      status: 'connected',
      description: '系统主数据库，存储用户和业务数据',
      createdAt: '2024-01-15 10:30:00',
      updatedAt: '2024-01-20 14:20:00'
    },
    {
      id: 2,
      name: '分析数据仓库',
      type: 'postgresql',
      host: '192.168.1.101',
      port: 5432,
      database: 'analytics_dw',
      username: 'analyst',
      status: 'connected',
      description: '数据分析专用仓库，支持复杂查询和报表生成',
      createdAt: '2024-01-16 09:15:00',
      updatedAt: '2024-01-18 16:45:00'
    },
    {
      id: 3,
      name: '缓存数据库',
      type: 'redis',
      host: '192.168.1.102',
      port: 6379,
      database: '0',
      username: '',
      status: 'failed',
      description: 'Redis缓存数据库，提升系统响应速度',
      createdAt: '2024-01-17 11:20:00',
      updatedAt: '2024-01-19 08:30:00'
    },
    {
      id: 4,
      name: '日志搜索引擎',
      type: 'elasticsearch',
      host: '192.168.1.103',
      port: 9200,
      database: 'logs',
      username: 'elastic',
      status: 'untested',
      description: 'Elasticsearch集群，用于日志检索和全文搜索',
      createdAt: '2024-01-18 14:10:00',
      updatedAt: '2024-01-18 14:10:00'
    }
  ];

  ngOnInit(): void {
    // 模拟数据加载
    this.loadMockData();
  }

  private loadMockData(): void {
    // 在实际项目中，这里应该调用真实的API
    setTimeout(() => {
      if (this.st) {
        this.st.reload(this.mockData);
      }
    }, 100);
  }

  add(): void {
    console.log('添加新数据源');
    // 这里应该打开添加数据源的弹窗
    // this.modal.createStatic(DatasourceEditComponent, { i: { id: 0 } })
    //   .subscribe(() => this.st.reload());
  }

  edit(item: DataSource): void {
    console.log('编辑数据源:', item);
    // 这里应该打开编辑数据源的弹窗
    // this.modal.createStatic(DatasourceEditComponent, { i: item })
    //   .subscribe(() => this.st.reload());
  }

  delete(item: DataSource): void {
    console.log('删除数据源:', item);
    // 这里应该调用删除API
    // this.http.delete(`/api/datasources/${item.id}`)
    //   .subscribe(() => this.st.reload());
  }

  testConnection(item: DataSource): void {
    console.log('测试连接:', item);
    // 模拟测试连接
    const updatedItem = { ...item };
    const success = Math.random() > 0.3; // 70%成功率
    updatedItem.status = success ? 'connected' : 'failed';
    
    // 更新数据
    const index = this.mockData.findIndex(d => d.id === item.id);
    if (index > -1) {
      this.mockData[index] = updatedItem;
      this.st.reload(this.mockData);
    }

    // 显示测试结果
    const message = success ? '连接测试成功！' : '连接测试失败，请检查配置信息。';
    console.log(message);
  }
}
