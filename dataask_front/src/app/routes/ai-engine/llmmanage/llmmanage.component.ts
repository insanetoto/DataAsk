import { Component, OnInit, ViewChild, inject } from '@angular/core';
import { STColumn, STComponent } from '@delon/abc/st';
import { SFSchema } from '@delon/form';
import { ModalHelper, _HttpClient } from '@delon/theme';
import { SHARED_IMPORTS } from '@shared';

interface LLMModel {
  id: number;
  name: string;
  provider: string;
  modelType: string;
  apiUrl: string;
  apiKey: string;
  status: string;
  maxTokens: number;
  temperature: number;
  description: string;
  createdAt: string;
  updatedAt: string;
  usageCount: number;
  lastUsed: string;
}

@Component({
  selector: 'app-ai-engine-llmmanage',
  imports: [...SHARED_IMPORTS],
  templateUrl: './llmmanage.component.html',
})
export class AiEngineLlmmanageComponent implements OnInit {
  private readonly http = inject(_HttpClient);
  private readonly modal = inject(ModalHelper);

  url = `/api/llm-models`;
  
  searchSchema: SFSchema = {
    properties: {
      name: {
        type: 'string',
        title: '模型名称',
        ui: {
          placeholder: '请输入模型名称'
        }
      },
      provider: {
        type: 'string',
        title: '模型提供商',
        enum: [
          { label: '全部', value: '' },
          { label: 'OpenAI', value: 'openai' },
          { label: 'Anthropic', value: 'anthropic' },
          { label: '智谱AI', value: 'zhipu' },
          { label: '百度文心', value: 'baidu' },
          { label: '阿里通义', value: 'alibaba' },
          { label: '腾讯混元', value: 'tencent' },
          { label: '本地部署', value: 'local' }
        ],
        default: ''
      },
      modelType: {
        type: 'string',
        title: '模型类型',
        enum: [
          { label: '全部', value: '' },
          { label: '文本生成', value: 'text-generation' },
          { label: '对话模型', value: 'chat' },
          { label: '代码生成', value: 'code-generation' },
          { label: '嵌入模型', value: 'embedding' },
          { label: '图像理解', value: 'vision' }
        ],
        default: ''
      },
      status: {
        type: 'string',
        title: '状态',
        enum: [
          { label: '全部', value: '' },
          { label: '可用', value: 'active' },
          { label: '不可用', value: 'inactive' },
          { label: '测试中', value: 'testing' }
        ],
        default: ''
      }
    }
  };

  @ViewChild('st') private readonly st!: STComponent;
  
  columns: STColumn[] = [
    { title: 'ID', index: 'id', width: 60 },
    {
      title: '模型名称',
      index: 'name',
      width: 150,
      render: 'nameRender'
    },
    {
      title: '提供商',
      index: 'provider',
      width: 120,
      type: 'tag',
      tag: {
        openai: { text: 'OpenAI', color: 'green' },
        anthropic: { text: 'Anthropic', color: 'blue' },
        zhipu: { text: '智谱AI', color: 'purple' },
        baidu: { text: '百度文心', color: 'red' },
        alibaba: { text: '阿里通义', color: 'orange' },
        tencent: { text: '腾讯混元', color: 'cyan' },
        local: { text: '本地部署', color: 'default' }
      }
    },
    {
      title: '模型类型',
      index: 'modelType',
      width: 120,
      type: 'tag',
      tag: {
        'text-generation': { text: '文本生成', color: 'blue' },
        'chat': { text: '对话模型', color: 'green' },
        'code-generation': { text: '代码生成', color: 'purple' },
        'embedding': { text: '嵌入模型', color: 'orange' },
        'vision': { text: '图像理解', color: 'red' }
      }
    },
    {
      title: 'API地址',
      index: 'apiUrl',
      width: 200,
      render: 'apiUrlRender'
    },
    {
      title: '状态',
      index: 'status',
      width: 80,
      type: 'badge',
      badge: {
        active: { text: '正常', color: 'success' },
        inactive: { text: '停用', color: 'default' },
        testing: { text: '测试中', color: 'processing' },
        error: { text: '异常', color: 'error' }
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
      width: 150,
      type: 'date',
      dateFormat: 'yyyy-MM-dd HH:mm'
    },
    {
      title: '最后更新',
      index: 'updatedAt',
      width: 150,
      type: 'date',
      dateFormat: 'yyyy-MM-dd HH:mm'
    },
    {
      title: '操作',
      width: 200,
      fixed: 'right',
      buttons: [
        {
          text: '测试',
          icon: 'experiment',
          type: 'link',
          click: (item: LLMModel) => this.testModel(item)
        },
        {
          text: '编辑',
          icon: 'edit',
          type: 'link',
          click: (item: LLMModel) => this.edit(item)
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
          click: (item: LLMModel) => this.delete(item)
        }
      ]
    }
  ];

  // 模拟数据
  mockData: LLMModel[] = [
    {
      id: 1,
      name: 'GPT-4',
      provider: 'openai',
      modelType: 'chat',
      apiUrl: 'https://api.openai.com/v1/chat/completions',
      apiKey: 'sk-****',
      status: 'active',
      maxTokens: 4096,
      temperature: 0.7,
      description: 'OpenAI GPT-4 模型，具备强大的对话和推理能力',
      createdAt: '2024-01-10 09:00:00',
      updatedAt: '2024-01-20 10:30:00',
      usageCount: 1250,
      lastUsed: '2024-01-20 15:45:00'
    },
    {
      id: 2,
      name: 'Claude-3',
      provider: 'anthropic',
      modelType: 'chat',
      apiUrl: 'https://api.anthropic.com/v1/messages',
      apiKey: 'sk-ant-****',
      status: 'active',
      maxTokens: 4096,
      temperature: 0.5,
      description: 'Anthropic Claude-3 模型，擅长分析和写作',
      createdAt: '2024-01-12 14:20:00',
      updatedAt: '2024-01-19 16:15:00',
      usageCount: 890,
      lastUsed: '2024-01-19 20:30:00'
    },
    {
      id: 3,
      name: 'GLM-4',
      provider: 'zhipu',
      modelType: 'chat',
      apiUrl: 'https://open.bigmodel.cn/api/paas/v4/chat/completions',
      apiKey: '****',
      status: 'testing',
      maxTokens: 8192,
      temperature: 0.8,
      description: '智谱AI GLM-4 模型，支持中文对话和代码生成',
      createdAt: '2024-01-15 11:10:00',
      updatedAt: '2024-01-18 09:20:00',
      usageCount: 45,
      lastUsed: '2024-01-18 14:22:00'
    },
    {
      id: 4,
      name: 'ERNIE-Bot',
      provider: 'baidu',
      modelType: 'chat',
      apiUrl: 'https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop',
      apiKey: '****',
      status: 'inactive',
      maxTokens: 2048,
      temperature: 0.6,
      description: '百度文心一言模型，专注中文理解和生成',
      createdAt: '2024-01-16 13:30:00',
      updatedAt: '2024-01-17 08:45:00',
      usageCount: 0,
      lastUsed: ''
    },
    {
      id: 5,
      name: 'Code-Llama',
      provider: 'local',
      modelType: 'code-generation',
      apiUrl: 'http://localhost:8080/v1/completions',
      apiKey: '',
      status: 'active',
      maxTokens: 2048,
      temperature: 0.2,
      description: '本地部署的Code Llama代码生成模型',
      createdAt: '2024-01-17 16:00:00',
      updatedAt: '2024-01-20 11:15:00',
      usageCount: 320,
      lastUsed: '2024-01-20 14:50:00'
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
    console.log('添加新模型');
    // 这里应该打开添加模型的弹窗
    // this.modal.createStatic(LLMEditComponent, { i: { id: 0 } })
    //   .subscribe(() => this.st.reload());
  }

  edit(item: LLMModel): void {
    console.log('编辑模型:', item);
    // 这里应该打开编辑模型的弹窗
    // this.modal.createStatic(LLMEditComponent, { i: item })
    //   .subscribe(() => this.st.reload());
  }

  delete(item: LLMModel): void {
    console.log('删除模型:', item);
    // 这里应该调用删除API
    // this.http.delete(`/api/llm-models/${item.id}`)
    //   .subscribe(() => this.st.reload());
  }

  testModel(item: LLMModel): void {
    console.log('测试模型:', item);
    // 模拟测试模型
    const updatedItem = { ...item };
    const success = Math.random() > 0.2; // 80%成功率
    updatedItem.status = success ? 'active' : 'inactive';
    
    // 更新数据
    const index = this.mockData.findIndex(d => d.id === item.id);
    if (index > -1) {
      this.mockData[index] = updatedItem;
      this.st.reload(this.mockData);
    }

    // 显示测试结果
    const message = success ? '模型测试成功！' : '模型测试失败，请检查API配置。';
    console.log(message);
  }
}
