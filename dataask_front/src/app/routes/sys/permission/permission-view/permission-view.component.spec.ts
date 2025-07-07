import { waitForAsync, ComponentFixture, TestBed } from '@angular/core/testing';
import { SysPermissionViewComponent } from './permission-view.component';

describe('SysPermissionViewComponent', () => {
  let component: SysPermissionViewComponent;
  let fixture: ComponentFixture<SysPermissionViewComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [ SysPermissionViewComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(SysPermissionViewComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
