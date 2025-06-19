import { waitForAsync, ComponentFixture, TestBed } from '@angular/core/testing';
import { SysOrgComponent } from './org.component';

describe('SysOrgComponent', () => {
  let component: SysOrgComponent;
  let fixture: ComponentFixture<SysOrgComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [ SysOrgComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(SysOrgComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
