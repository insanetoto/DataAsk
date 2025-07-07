import { waitForAsync, ComponentFixture, TestBed } from '@angular/core/testing';
import { SysPermissionEditComponent } from './permission-edit.component';

describe('SysPermissionEditComponent', () => {
  let component: SysPermissionEditComponent;
  let fixture: ComponentFixture<SysPermissionEditComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [ SysPermissionEditComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(SysPermissionEditComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
