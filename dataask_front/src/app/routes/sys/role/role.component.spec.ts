import { waitForAsync, ComponentFixture, TestBed } from '@angular/core/testing';

import { SysRoleComponent } from './role.component';

describe('SysRoleComponent', () => {
  let component: SysRoleComponent;
  let fixture: ComponentFixture<SysRoleComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [SysRoleComponent]
    }).compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(SysRoleComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
