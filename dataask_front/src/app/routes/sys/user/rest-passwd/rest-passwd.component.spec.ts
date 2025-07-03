import { waitForAsync, ComponentFixture, TestBed } from '@angular/core/testing';

import { SysRestPasswdComponent } from './rest-passwd.component';

describe('SysRestPasswdComponent', () => {
  let component: SysRestPasswdComponent;
  let fixture: ComponentFixture<SysRestPasswdComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [SysRestPasswdComponent]
    }).compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(SysRestPasswdComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
