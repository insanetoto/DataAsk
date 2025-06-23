import { Component, OnInit, inject } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { GlobalFooterModule } from '@delon/abc/global-footer';
import { DA_SERVICE_TOKEN } from '@delon/auth';
import { NzIconModule } from 'ng-zorro-antd/icon';

@Component({
  selector: 'layout-passport',
  template: `
    <div class="container">
      <div class="wrap">
        <div class="top">
          <div class="head">
            <img class="logo" src="./assets/logo-color.svg" />
            <span class="title">洞察魔方</span>
          </div>
          <div class="desc">洞察魔方</div>
        </div>
        <router-outlet />
        <global-footer [links]="links">
          Copyright
          <nz-icon nzType="copyright"></nz-icon> 2025 <a href="" target="_blank">中科百惟</a>出品
        </global-footer>
      </div>
    </div>
  `,
  styleUrls: ['./passport.component.less'],
  imports: [RouterOutlet, GlobalFooterModule, NzIconModule],
  standalone: true
})
export class LayoutPassportComponent implements OnInit {
  private tokenService = inject(DA_SERVICE_TOKEN);

  links = [
    {
      title: '帮助',
      href: ''
    },
    {
      title: '隐私',
      href: ''
    },
    {
      title: '条款',
      href: ''
    }
  ];

  ngOnInit(): void {
    this.tokenService.clear();
  }
}
