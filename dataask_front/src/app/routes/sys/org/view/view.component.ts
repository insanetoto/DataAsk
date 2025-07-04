import { Component, OnInit, inject } from '@angular/core';
import { _HttpClient } from '@delon/theme';
import { NzMessageService } from 'ng-zorro-antd/message';
import { NzModalRef } from 'ng-zorro-antd/modal';
import { SHARED_IMPORTS } from '@shared';

@Component({
  selector: 'app-sys-view',
  imports: [...SHARED_IMPORTS],
  templateUrl: './view.component.html',
})
export class SysViewComponent implements OnInit {
  private readonly http = inject(_HttpClient);
  private readonly msgSrv = inject(NzMessageService);
  private readonly modal = inject(NzModalRef);

  record: any = {};
  i: any;

  ngOnInit(): void {
    this.http.get(`/user/${this.record.id}`).subscribe(res => this.i = res);
  }

  close(): void {
    this.modal.destroy();
  }
}
