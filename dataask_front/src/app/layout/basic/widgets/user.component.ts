import { ChangeDetectionStrategy, Component, inject } from '@angular/core';
import { Router, RouterLink } from '@angular/router';
import { DA_SERVICE_TOKEN } from '@delon/auth';
import { SettingsService, User } from '@delon/theme';
import { NzAvatarModule } from 'ng-zorro-antd/avatar';
import { NzDropDownModule } from 'ng-zorro-antd/dropdown';
import { NzIconModule } from 'ng-zorro-antd/icon';
import { NzMenuModule } from 'ng-zorro-antd/menu';

@Component({
  selector: 'header-user',
  template: `
    <div class="alain-default__nav-item d-flex align-items-center px-sm" nz-dropdown nzPlacement="bottomRight" [nzDropdownMenu]="userMenu">
      <nz-avatar [nzSrc]="user.avatar" nzSize="small" class="mr-sm" />
      {{ user.name }}
    </div>
    <nz-dropdown-menu #userMenu="nzDropdownMenu">
      <div nz-menu class="width-sm">
        <div nz-menu-item routerLink="/pro/account/center">
          <nz-icon nzType="user" class="mr-sm"></nz-icon>
          个人中心
        </div>
        <div nz-menu-item routerLink="/pro/account/settings">
          <nz-icon nzType="setting" class="mr-sm"></nz-icon>
          个人设置
        </div>
        <div nz-menu-item routerLink="/exception/trigger">
          <nz-icon nzType="close-circle" class="mr-sm"></nz-icon>
          触发错误
        </div>
        <li nz-menu-divider></li>
        <div nz-menu-item (click)="logout()">
          <nz-icon nzType="logout" class="mr-sm"></nz-icon>
          退出登录
        </div>
      </div>
    </nz-dropdown-menu>
  `,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [RouterLink, NzDropDownModule, NzMenuModule, NzIconModule, NzAvatarModule],
  standalone: true
})
export class HeaderUserComponent {
  private readonly settings = inject(SettingsService);
  private readonly router = inject(Router);
  private readonly tokenService = inject(DA_SERVICE_TOKEN);

  get user(): User {
    return this.settings.user;
  }

  logout(): void {
    this.tokenService.clear();
    this.router.navigateByUrl(this.tokenService.login_url!);
  }
}
