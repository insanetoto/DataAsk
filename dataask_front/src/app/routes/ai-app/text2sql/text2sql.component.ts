import { Component, OnInit, inject } from '@angular/core';
import { PageHeaderModule } from '@delon/abc/page-header';
import { _HttpClient } from '@delon/theme';
import { SHARED_IMPORTS } from '@shared';
import { NzMessageService } from 'ng-zorro-antd/message';

@Component({
  selector: 'app-ai-app-text2sql',
  imports: [...SHARED_IMPORTS, PageHeaderModule],
  templateUrl: './text2sql.component.html'
})
export class AiAppText2sqlComponent implements OnInit {
  private readonly http = inject(_HttpClient);
  private readonly msgSrv = inject(NzMessageService);

  // Text2SQL相关数据
  sqlQuery = '';
  naturalLanguageInput = '';
  queryResult: any[] = [];
  loading = false;

  ngOnInit(): void {
    // 初始化Text2SQL页面数据
    this.naturalLanguageInput = '';
  }

  // 执行自然语言转SQL
  executeText2SQL(): void {
    if (!this.naturalLanguageInput.trim()) {
      this.msgSrv.warning('请输入自然语言描述');
      return;
    }

    this.loading = true;
    // TODO: 调用后端API进行Text2SQL转换
    // this.http.post('/api/text2sql', { input: this.naturalLanguageInput }).subscribe(
    //   res => {
    //     this.sqlQuery = res.sql;
    //     this.queryResult = res.result;
    //     this.loading = false;
    //   },
    //   err => {
    //     this.msgSrv.error('转换失败');
    //     this.loading = false;
    //   }
    // );

    // 临时模拟数据
    setTimeout(() => {
      this.sqlQuery = 'SELECT * FROM users WHERE age > 25';
      this.queryResult = [
        { id: 1, name: '张三', age: 28 },
        { id: 2, name: '李四', age: 30 }
      ];
      this.loading = false;
    }, 1000);
  }

  // 清空结果
  clearResults(): void {
    this.sqlQuery = '';
    this.queryResult = [];
    this.naturalLanguageInput = '';
  }
}
