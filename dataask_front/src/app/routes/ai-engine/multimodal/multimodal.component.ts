import { Component, OnInit, ViewChild, inject, ChangeDetectionStrategy } from '@angular/core';
import { STColumn, STComponent } from '@delon/abc/st';
import { SFSchema } from '@delon/form';
import { ModalHelper, _HttpClient } from '@delon/theme';
import { SHARED_IMPORTS } from '@shared';

@Component({
  selector: 'app-ai-engine-multimodal',
  templateUrl: './multimodal.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [SHARED_IMPORTS]
})
export class AiEngineMultimodalComponent implements OnInit {
  private readonly http = inject(_HttpClient);
  private readonly modal = inject(ModalHelper);

  url = `/api/multimodal`;
  searchSchema: SFSchema = {
    properties: {
      name: {
        type: 'string',
        title: '配置名称',
        ui: {
          placeholder: '请输入配置名称'
        }
      },
      type: {
        type: 'string',
        title: '类型',
        enum: [
          { label: '视觉+文本', value: 'vision-text' },
          { label: '音频+文本', value: 'audio-text' },
          { label: '视频+文本', value: 'video-text' }
        ],
        ui: {
          widget: 'select',
          placeholder: '请选择类型'
        }
      }
    }
  };

  @ViewChild('st') private readonly st!: STComponent;

  columns: STColumn[] = [
    {
      title: '配置名称',
      index: 'name',
      width: 150,
      sort: true
    },
    {
      title: '类型',
      index: 'type',
      width: 120,
      format: (item: any) => {
        const typeMap: any = {
          'vision-text': '视觉+文本',
          'audio-text': '音频+文本',
          'video-text': '视频+文本'
        };
        return typeMap[item.type] || item.type;
      }
    },
    {
      title: '状态',
      index: 'status',
      render: 'status',
      width: 80,
      filter: {
        menus: [
          { text: '启用', value: 1 },
          { text: '禁用', value: 0 }
        ],
        fn: (filter: any, record: any) => record.status === filter.value
      }
    },
    {
      title: '描述',
      index: 'description',
      width: 200
    },
    {
      title: '创建时间',
      type: 'date',
      index: 'createdAt',
      width: 150,
      sort: true
    },
    {
      title: '操作',
      width: 200,
      fixed: 'right',
      buttons: [
        {
          text: '查看',
          icon: 'eye',
          click: (item: any) => this.viewConfig(item)
        },
        {
          text: '编辑',
          icon: 'edit',
          click: (item: any) => this.editConfig(item)
        },
        {
          text: '删除',
          icon: 'delete',
          type: 'del',
          click: (item: any) => this.deleteConfig(item)
        }
      ]
    }
  ];

  ngOnInit(): void {
    // 组件初始化时可以加载数据
  }

  add(): void {
    // 打开新建多模态配置的模态框
  }

  viewConfig(_item: any): void {
    // 查看配置详情
  }

  editConfig(_item: any): void {
    // 编辑配置
  }

  deleteConfig(_item: any): void {
    // 这里可以调用删除API
  }
}
