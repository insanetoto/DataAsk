import { ChangeDetectionStrategy, Component, Inject } from '@angular/core';
import { DA_SERVICE_TOKEN, ITokenService } from '@delon/auth';
import { NzIconModule } from 'ng-zorro-antd/icon';
import { NzMessageService } from 'ng-zorro-antd/message';
import { NzToolTipModule } from 'ng-zorro-antd/tooltip';

@Component({
  selector: 'header-clear-storage',
  template: `<i nz-icon nzType="tool" nz-tooltip nzTooltipTitle="清除本地缓存" (click)="clear()"></i>`,
  standalone: true,
  imports: [NzIconModule, NzToolTipModule],
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class HeaderClearStorageComponent {
  constructor(
    private messageSrv: NzMessageService,
    @Inject(DA_SERVICE_TOKEN) private tokenService: ITokenService
  ) {}

  clear(): void {
    this.tokenService.clear();
    this.messageSrv.success('清除成功');
  }
}
