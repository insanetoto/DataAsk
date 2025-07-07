import { waitForAsync, ComponentFixture, TestBed } from '@angular/core/testing';
import { SysRoleViewComponent } from './role-view.component';

describe('SysRoleViewComponent', () => {
  let component: SysRoleViewComponent;
  let fixture: ComponentFixture<SysRoleViewComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [ SysRoleViewComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(SysRoleViewComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
