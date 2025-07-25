import { HttpErrorResponse, HttpHandlerFn, HttpRequest, HttpResponse } from '@angular/common/http';
import { inject } from '@angular/core';
import { Router } from '@angular/router';
import { DA_SERVICE_TOKEN } from '@delon/auth';
import { IGNORE_BASE_URL } from '@delon/theme';
import { NzNotificationService } from 'ng-zorro-antd/notification';
import { Observable, catchError, mergeMap, of, throwError } from 'rxjs';

interface ApiResponse<T = any> {
  code?: number;
  success?: boolean;
  message?: string;
  data?: T;
}

export function defaultInterceptor(req: HttpRequest<any>, next: HttpHandlerFn): Observable<any> {
  const router = inject(Router);
  const notification = inject(NzNotificationService);
  const tokenService = inject(DA_SERVICE_TOKEN);

  // 统一处理请求
  let url = req.url;
  if (!req.context.get(IGNORE_BASE_URL) && !url.startsWith('https://') && !url.startsWith('http://')) {
    // 移除开头的斜杠和点
    url = url.replace(/^[./]+/, '');

    // 对于assets目录下的静态资源，不添加API前缀
    if (url.startsWith('assets/')) {
      url = `/${url}`;
    } else if (url.startsWith('api/')) {
      // 已经有api前缀的不再添加
      url = `/${url}`;
    } else {
      // 其他API请求添加api前缀
      url = `/api/${url}`;
    }
  }

  // 添加认证头
  let newReq = req.clone({ url });

  // 获取token并添加到请求头
  const token = tokenService.get()?.token;
  if (token && !req.url.includes('/auth/login') && !req.url.includes('/auth/refresh')) {
    newReq = newReq.clone({
      setHeaders: {
        Authorization: `Bearer ${token}`
      }
    });
  }
  return next(newReq).pipe(
    mergeMap(event => {
      // 统一处理HTTP响应
      if (event instanceof HttpResponse) {
        const body = event.body as ApiResponse;

        // 对于静态资源文件，不进行API业务逻辑检查
        if (req.url.includes('/assets/')) {
          return of(event);
        }

        // 兼容两种响应格式：{code: 2xx, ...} 和 {success: true, ...}
        const isSuccess = (body?.code && body.code >= 200 && body.code < 300) || body?.success === true;
        const isUnauthorized = body?.code === 401;

        if (!isSuccess && body !== null) {
          if (isUnauthorized) {
            // 清除token并跳转到登录页
            tokenService.clear();
            router.navigateByUrl('/passport/login');
            return throwError(() => event);
          }
          if (body?.message) {
            notification.error('错误', body.message);
          }
          return throwError(() => event);
        }
        return of(event);
      }
      return of(event);
    }),
    catchError((err: HttpErrorResponse) => {
      // 统一处理HTTP错误
      switch (err.status) {
        case 401:
          // 清除token并跳转到登录页
          tokenService.clear();
          router.navigateByUrl('/passport/login');
          break;
        case 403:
          router.navigateByUrl('/exception/403');
          break;
        case 404:
          router.navigateByUrl('/exception/404');
          break;
        case 500:
          router.navigateByUrl('/exception/500');
          break;
        default:
          if (err.error?.message) {
            notification.error('错误', err.error.message);
          } else {
            notification.error('错误', '服务器异常，请稍后重试');
          }
          break;
      }
      return throwError(() => err);
    })
  );
}
