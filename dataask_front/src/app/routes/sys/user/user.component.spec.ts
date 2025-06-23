import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideAnimations } from '@angular/platform-browser/animations';
import { ALAIN_SETTING_KEYS } from '@delon/theme';

import { SysUserComponent } from './user.component';

describe('SysUserComponent', () => {
  let component: SysUserComponent;
  let fixture: ComponentFixture<SysUserComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [SysUserComponent],
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        provideAnimations(),
        { provide: ALAIN_SETTING_KEYS, useValue: { layout: {}, theme: {}, app: {} } }
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(SysUserComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
