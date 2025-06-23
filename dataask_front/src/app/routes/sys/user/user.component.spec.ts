import { waitForAsync, ComponentFixture, TestBed } from '@angular/core/testing';

import { SysUserComponent } from './user.component';

describe('SysUserComponent', () => {
  let component: SysUserComponent;
  let fixture: ComponentFixture<SysUserComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [SysUserComponent]
    }).compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(SysUserComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
