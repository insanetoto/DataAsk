import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideAnimations } from '@angular/platform-browser/animations';
import { ALAIN_SETTING_KEYS } from '@delon/theme';

import { SysRoleComponent } from './role.component';

describe('SysRoleComponent', () => {
  let component: SysRoleComponent;
  let fixture: ComponentFixture<SysRoleComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [SysRoleComponent],
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        provideAnimations(),
        { provide: ALAIN_SETTING_KEYS, useValue: { layout: {}, theme: {}, app: {} } }
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(SysRoleComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
