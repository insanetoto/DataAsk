import { HttpClient, HttpClientJsonpModule } from '@angular/common/http';
import { ChangeDetectionStrategy, ChangeDetectorRef, Component, OnDestroy, OnInit, inject } from '@angular/core';
import { CountDownModule } from '@delon/abc/count-down';
import { ChartEChartsModule, ChartEChartsOption } from '@delon/chart/chart-echarts';
import { G2GaugeModule } from '@delon/chart/gauge';
import { G2MiniAreaModule } from '@delon/chart/mini-area';
import { NumberInfoModule } from '@delon/chart/number-info';
import { G2PieModule } from '@delon/chart/pie';
import { G2TagCloudModule } from '@delon/chart/tag-cloud';
import { G2WaterWaveModule } from '@delon/chart/water-wave';
import { NzCardModule } from 'ng-zorro-antd/card';
import { NzGridModule } from 'ng-zorro-antd/grid';
import { NzIconModule } from 'ng-zorro-antd/icon';
import { NzToolTipModule } from 'ng-zorro-antd/tooltip';
import type { CountdownConfig } from 'ngx-countdown';

@Component({
  selector: 'app-dashboard',
  templateUrl: './dashboard.component.html',
  styleUrls: ['./dashboard.component.less'],
  changeDetection: ChangeDetectionStrategy.OnPush,
  standalone: true,
  imports: [
    HttpClientJsonpModule,
    NzCardModule,
    NzGridModule,
    NzIconModule,
    NzToolTipModule,
    G2WaterWaveModule,
    G2TagCloudModule,
    G2PieModule,
    G2GaugeModule,
    G2MiniAreaModule,
    NumberInfoModule,
    CountDownModule,
    ChartEChartsModule
  ]
})
export class DashboardComponent implements OnInit, OnDestroy {
  private readonly http = inject(HttpClient);
  private readonly cdr = inject(ChangeDetectorRef);

  data: any = {};
  tags = [
    { text: '用户管理', value: 95 },
    { text: '数据查询', value: 88 },
    { text: '销售报表', value: 76 },
    { text: '订单分析', value: 65 },
    { text: '客户画像', value: 58 },
    { text: '库存统计', value: 45 },
    { text: '财务汇总', value: 38 },
    { text: '产品分析', value: 32 },
    { text: '趋势预测', value: 28 },
    { text: '风险评估', value: 25 }
  ];
  loading = false;
  percent: number | null = null;
  
  // AI运行实况倒计时配置（知识库文档数量显示）
  cd: CountdownConfig = {
    format: `HH:mm:ss`,
    leftTime: 86400000 // 24小时
  };

  // 重点省份列表
  keyProvinces = ['广东', '广西', '贵州', '云南', '海南'];

  // 中国地图配置 - 待实现
  mapOption: any = {
    backgroundColor: '#ffffff'
  };

  // region: AI活动预测图表
  activeTime$: any;
  activeData!: any[];
  activeStat = {
    max: 0,
    min: 0,
    t1: '',
    t2: ''
  };

  ngOnInit(): void {
    // 加载中国地图
    this.loadCharts();
    
    // 模拟加载AI运行数据
    this.loadAIData();
    
    // 活动预测图表
    this.refData();
    this.activeTime$ = setInterval(() => this.refData(), 1000 * 5);
  }

  loadCharts(): void {
    // 地图组件待实现
  }

  loadAIData(): void {
    // 模拟AI运行数据
    this.data = {
      todayQuestions: 1247, // 今日问答次数
      totalQuestions: 89432, // 累计问答次数
      knowledgeDocs: 156, // 知识库文档数量
      totalTraining: 892 // 累积训练次数
    };
    this.loading = false;
    this.cdr.detectChanges();
  }

  refData(): void {
    const activeData: any[] = [];
    for (let i = 0; i < 24; i += 1) {
      activeData.push({
        x: `${i.toString().padStart(2, '0')}:00`,
        y: i * 10 + Math.floor(Math.random() * 50)
      });
    }
    this.activeData = activeData;
    
    // 统计数据
    this.activeStat.max = [...activeData].sort((a, b) => b.y - a.y)[0].y + 50;
    this.activeStat.min = [...activeData].sort((a, b) => a.y - b.y)[0].y;
    this.activeStat.t1 = activeData[Math.floor(activeData.length / 2)].x;
    this.activeStat.t2 = activeData[activeData.length - 1].x;
    
    // 效率百分比
    this.percent = Math.floor(Math.random() * 40) + 60; // 60-100之间
    this.cdr.detectChanges();
  }

  // AI效率格式化
  aiEfficiencyFormat(val: any): string {
    switch (Math.floor(parseInt(val, 10) / 20)) {
      case 3:
        return '良好';
      case 4:
        return '优秀';
      case 5:
        return '卓越';
      default:
        return '一般';
    }
  }

  ngOnDestroy(): void {
    if (this.activeTime$) {
      clearInterval(this.activeTime$);
    }
  }
}
