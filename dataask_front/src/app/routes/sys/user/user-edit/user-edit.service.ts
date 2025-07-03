import { Injectable, inject } from '@angular/core';
import { _HttpClient } from '@delon/theme';
import { Observable, of } from 'rxjs';
import { map, catchError } from 'rxjs/operators';

import { User } from '../user.service';

@Injectable({ providedIn: 'root' })
export class UserEditService {
  private readonly http = inject(_HttpClient);

  /**
   * 验证用户编码是否唯一
   */
  validateUserCode(userCode: string, excludeId?: number): Observable<boolean> {
    return this.http.get('/users/validate', { user_code: userCode, exclude_id: excludeId }).pipe(
      map(response => response.valid),
      catchError(() => of(false))
    );
  }

  /**
   * 验证电话号码格式
   */
  validatePhoneFormat(phone: string): boolean {
    if (!phone) return true; // 允许为空
    const phoneRegex = /^1[3-9]\d{9}$/;
    return phoneRegex.test(phone);
  }

  /**
   * 验证密码强度
   */
  validatePasswordStrength(password: string): { valid: boolean; message: string } {
    if (!password) {
      return { valid: false, message: '密码不能为空' };
    }
    if (password.length < 8) {
      return { valid: false, message: '密码长度至少8位' };
    }
    // 密码必须包含数字和字母
    const hasNumber = /\d/.test(password);
    const hasLetter = /[a-zA-Z]/.test(password);
    if (!hasNumber || !hasLetter) {
      return { valid: false, message: '密码必须包含数字和字母' };
    }
    return { valid: true, message: '密码强度符合要求' };
  }

  /**
   * 格式化用户数据用于提交
   */
  formatUserData(userData: Partial<User>): Partial<User> {
    return {
      ...userData,
      phone: userData.phone?.trim(),
      address: userData.address?.trim(),
      status: userData.status ?? 1
    };
  }

  /**
   * 保存用户数据
   */
  saveUser(userData: Partial<User>): Observable<any> {
    const formattedData = this.formatUserData(userData);
    if (userData.id) {
      return this.http.put(`/users/${userData.id}`, formattedData);
    }
    return this.http.post('/users', formattedData);
  }
}
