import { waitForAsync, ComponentFixture, TestBed } from '@angular/core/testing';

import { SysUserViewComponent } from './user-view.component';

describe('SysUserViewComponent', () => {
  let component: SysUserViewComponent;
  let fixture: ComponentFixture<SysUserViewComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [SysUserViewComponent]
    }).compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(SysUserViewComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
