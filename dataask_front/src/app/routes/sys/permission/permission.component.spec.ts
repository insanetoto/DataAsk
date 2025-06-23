import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideAnimations } from '@angular/platform-browser/animations';
import { ALAIN_SETTING_KEYS } from '@delon/theme';

import { SysPermissionComponent } from './permission.component';

describe('SysPermissionComponent', () => {
  let component: SysPermissionComponent;
  let fixture: ComponentFixture<SysPermissionComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [SysPermissionComponent],
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        provideAnimations(),
        { provide: ALAIN_SETTING_KEYS, useValue: { layout: {}, theme: {}, app: {} } }
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(SysPermissionComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
