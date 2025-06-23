import { waitForAsync, ComponentFixture, TestBed } from '@angular/core/testing';

import { SysPermissionComponent } from './permission.component';

describe('SysPermissionComponent', () => {
  let component: SysPermissionComponent;
  let fixture: ComponentFixture<SysPermissionComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [SysPermissionComponent]
    }).compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(SysPermissionComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
