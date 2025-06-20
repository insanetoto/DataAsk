import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { DA_SERVICE_TOKEN } from '@delon/auth';

/**
 * Dynamically load the start page
 *
 * 动态加载启动页
 */
export const startPageGuard: CanActivateFn = (): boolean => {
  const tokenService = inject(DA_SERVICE_TOKEN);
  const router = inject(Router);

  // 如果未登录，重定向到登录页
  if (!tokenService.get()?.token) {
    router.navigateByUrl('/passport/login');
    return false;
  }

  return true;
};
