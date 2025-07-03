import { DebugElement } from '@angular/core';
import { ComponentFixture } from '@angular/core/testing';
import { By } from '@angular/platform-browser';

/**
 * 测试工具类
 * 提供常用的测试辅助函数
 */
export class TestUtils {
  /**
   * 等待异步操作完成
   */
  static async waitForAsync(fixture: ComponentFixture<any>): Promise<void> {
    fixture.detectChanges();
    await fixture.whenStable();
  }

  /**
   * 根据选择器查找元素
   */
  static querySelector<T = HTMLElement>(fixture: ComponentFixture<any>, selector: string): T | null {
    const element = fixture.debugElement.query(By.css(selector));
    return element ? element.nativeElement : null;
  }

  /**
   * 根据选择器查找所有元素
   */
  static querySelectorAll<T = HTMLElement>(fixture: ComponentFixture<any>, selector: string): T[] {
    const elements = fixture.debugElement.queryAll(By.css(selector));
    return elements.map(el => el.nativeElement);
  }

  /**
   * 获取元素文本内容
   */
  static getTextContent(fixture: ComponentFixture<any>, selector: string): string {
    const element = this.querySelector(fixture, selector);
    return element ? element.textContent?.trim() || '' : '';
  }

  /**
   * 触发点击事件
   */
  static click(fixture: ComponentFixture<any>, selector: string): void {
    const element = this.querySelector(fixture, selector);
    if (element) {
      element.click();
      fixture.detectChanges();
    }
  }

  /**
   * 设置输入框值
   */
  static setInputValue(fixture: ComponentFixture<any>, selector: string, value: string): void {
    const input = this.querySelector<HTMLInputElement>(fixture, selector);
    if (input) {
      input.value = value;
      input.dispatchEvent(new Event('input'));
      fixture.detectChanges();
    }
  }

  /**
   * 触发表单提交
   */
  static submitForm(fixture: ComponentFixture<any>, selector = 'form'): void {
    const form = this.querySelector<HTMLFormElement>(fixture, selector);
    if (form) {
      form.dispatchEvent(new Event('submit'));
      fixture.detectChanges();
    }
  }

  /**
   * 检查元素是否存在
   */
  static elementExists(fixture: ComponentFixture<any>, selector: string): boolean {
    return this.querySelector(fixture, selector) !== null;
  }

  /**
   * 检查元素是否包含指定CSS类
   */
  static hasClass(fixture: ComponentFixture<any>, selector: string, className: string): boolean {
    const element = this.querySelector(fixture, selector);
    return element ? element.classList.contains(className) : false;
  }

  /**
   * 等待指定时间
   */
  static async delay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  /**
   * 模拟HTTP响应
   */
  static mockHttpResponse<T>(data: T, success = true): any {
    return {
      code: success ? 200 : 500,
      message: success ? '操作成功' : '操作失败',
      data: data,
      success: success
    };
  }
}
