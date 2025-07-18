import { CommonModule } from '@angular/common';
import { Component, OnInit, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { PageHeaderModule } from '@delon/abc/page-header';
import { _HttpClient } from '@delon/theme';
import { SHARED_IMPORTS } from '@shared';
import { NzBreadCrumbModule } from 'ng-zorro-antd/breadcrumb';
import { NzButtonModule } from 'ng-zorro-antd/button';
import { NzCardModule } from 'ng-zorro-antd/card';
import { NzFormModule } from 'ng-zorro-antd/form';
import { NzIconModule } from 'ng-zorro-antd/icon';
import { NzInputModule } from 'ng-zorro-antd/input';
import { NzMessageService } from 'ng-zorro-antd/message';
import { NzSelectModule } from 'ng-zorro-antd/select';
import { NzAlertModule } from 'ng-zorro-antd/alert';

@Component({
  selector: 'app-ai-app-training',
  imports: [
    ...SHARED_IMPORTS,
    PageHeaderModule,
    NzBreadCrumbModule,
    NzCardModule,
    NzFormModule,
    NzInputModule,
    NzButtonModule,
    NzIconModule,
    NzSelectModule,
    NzAlertModule,
    FormsModule,
    CommonModule
  ],
  templateUrl: './training.component.html',
  styleUrls: ['./training.component.less']
})
export class AiAppTrainingComponent implements OnInit {
  private readonly http = inject(_HttpClient);
  private readonly msgSrv = inject(NzMessageService);
  private readonly router = inject(Router);

  // 训练数据表单
  trainingData = {
    question: '',
    sqlQuery: '',
    description: '',
    category: 'general'
  };

  // 提交状态
  submitting = false;

  ngOnInit(): void {
    console.log('训练页面已初始化');
  }

  /**
   * 提交训练数据
   */
  submitTrainingData(): void {
    if (!this.trainingData.question.trim() || !this.trainingData.sqlQuery.trim()) {
      this.msgSrv.warning('请填写完整的问题和SQL语句');
      return;
    }

    this.submitting = true;

    // TODO: 调用后端API提交训练数据
    // this.http.post('/api/text2sql/training', this.trainingData).subscribe({
    //   next: (response) => {
    //     this.msgSrv.success('训练数据提交成功，感谢您的反馈！');
    //     this.resetForm();
    //     this.submitting = false;
    //   },
    //   error: (error) => {
    //     this.msgSrv.error('提交失败，请重试');
    //     this.submitting = false;
    //   }
    // });

    // 模拟提交
    setTimeout(() => {
      this.msgSrv.success('训练数据提交成功，感谢您的反馈！');
      this.resetForm();
      this.submitting = false;
    }, 1000);
  }

  /**
   * 重置表单
   */
  resetForm(): void {
    this.trainingData = {
      question: '',
      sqlQuery: '',
      description: '',
      category: 'general'
    };
  }

  /**
   * 返回Text2SQL页面
   */
  goBack(): void {
    this.router.navigate(['/ai-app/text2sql']);
  }
}
