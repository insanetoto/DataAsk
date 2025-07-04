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
        name: '洞察魔方',
        description: '数据分析问答系统'
      },
      user: null,
      menus: [],
      permissions: []
    };

    // 获取应用数据
    return this.httpClient.get('/api/app/init').pipe(
      catchError(error => {
        return of({ code: 200, data: defaultData });
      }),
      map((appData: NzSafeAny) => {
        // 设置应用数据
        const res = appData.data;

        // Application information: including site name, description, year
        this.settingService.setApp(res.app);

        // User information: including name, avatar, email address
        this.settingService.setUser(res.user);

        // ACL: 根据用户角色和权限配置访问控制
        this.configureACL(res.user, res.permissions);

        // Menu data, https://ng-alain.com/theme/menu
        this.menuService.add(res.menus);

        // Can be set page suffix title, https://ng-alain.com/theme/title
        this.titleService.suffix = res.app.name;
      })
    );
  }

  /**
   * 配置ACL权限控制
   */
  private configureACL(user: any, permissions: any[]): void {
    if (!user) {
      // 未登录用户，清除所有权限
      this.aclService.set({});
      return;
    }

    // 获取用户角色信息 - 修复字段名匹配问题
    const roleCode = user.roleCode || user.role_code || user.role?.role_code;
    const roles: string[] = roleCode ? [roleCode] : [];

    // 获取用户权限点
    const abilities: string[] = [];

    // 基于角色添加基础权限
    if (roleCode === 'SUPER_ADMIN') {
      // 超级管理员拥有所有权限
      abilities.push(
        'user.reset.password',
        'user.manage.org',
        'user.create',
        'user.edit',
        'user.delete',
        'user.view',
        'role.manage',
        'permission.manage',
        'org.manage',
        'workflow.manage',
        'message.manage'
      );
    } else if (roleCode === 'ORG_ADMIN') {
      // 机构管理员权限 - 与超级管理员相同的操作权限，但数据范围限制在本机构
      abilities.push(
        'user.reset.password',
        'user.manage.org',
        'user.create',
        'user.edit',
        'user.delete',
        'user.view',
        'role.manage',
        'permission.manage',
        'org.manage',
        'workflow.manage',
        'message.manage'
      );
    } else if (roleCode === 'NORMAL_USER') {
      // 普通用户权限
      abilities.push('user.view');
    }

    // 添加从后端获取的权限点
    if (permissions && permissions.length > 0) {
      permissions.forEach(permission => {
        if (permission.permission_code) {
          abilities.push(permission.permission_code);
        }
      });
    }

    // 设置ACL权限
    const aclConfig = {
      role: roles,
      ability: abilities,
      mode: 'oneOf' as const
    };
    this.aclService.set(aclConfig);
  }
}
