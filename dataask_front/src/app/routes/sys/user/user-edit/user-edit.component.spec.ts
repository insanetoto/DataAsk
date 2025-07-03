import { waitForAsync, ComponentFixture, TestBed } from '@angular/core/testing';

import { SysUserEditComponent } from './user-edit.component';

describe('SysUserEditComponent', () => {
  let component: SysUserEditComponent;
  let fixture: ComponentFixture<SysUserEditComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [SysUserEditComponent]
    }).compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(SysUserEditComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
