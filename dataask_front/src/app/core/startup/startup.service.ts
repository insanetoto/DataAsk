import { APP_INITIALIZER, Injectable, Provider, inject } from '@angular/core';
import { ACLService } from '@delon/acl';
import { MenuService, SettingsService, TitleService, _HttpClient } from '@delon/theme';
import { NzSafeAny } from 'ng-zorro-antd/core/types';
import { Observable, catchError, map, of } from 'rxjs';

/**
 * Used for application startup
 * Generally used to get the basic data of the application, like: Menu Data, User Data, etc.
 */
export function provideStartup(): Provider[] {
  return [
    StartupService,
    {
      provide: APP_INITIALIZER,
      useFactory: (startupService: StartupService) => () => startupService.load(),
      deps: [StartupService],
      multi: true
    }
  ];
}

@Injectable()
export class StartupService {
  private menuService = inject(MenuService);
  private settingService = inject(SettingsService);
  private aclService = inject(ACLService);
  private titleService = inject(TitleService);
  private httpClient = inject(_HttpClient);

  load(): Observable<void> {
    const defaultData = {
      app: {
        name: 'DataAsk',
        description: '数据分析问答系统'
      },
      user: null,
      menus: [],
      permissions: []
    };

    // 获取应用数据
    return this.httpClient.get('/api/app/init').pipe(
      catchError(() => of({ code: 200, data: defaultData })),
      map((appData: NzSafeAny) => {
        // 设置应用数据
        const res = appData.data;
        // Application information: including site name, description, year
        this.settingService.setApp(res.app);
        // User information: including name, avatar, email address
        this.settingService.setUser(res.user);
        // ACL: Set the permissions to full, https://ng-alain.com/acl/getting-started
        this.aclService.setFull(true);
        this.aclService.setAbility(res.permissions);
        // Menu data, https://ng-alain.com/theme/menu
        this.menuService.add(res.menus);
        // Can be set page suffix title, https://ng-alain.com/theme/title
        this.titleService.suffix = res.app.name;
      })
    );
  }
}
