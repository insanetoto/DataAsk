import { waitForAsync, ComponentFixture, TestBed } from '@angular/core/testing';
import { SysWorkflowComponent } from './workflow.component';

describe('SysWorkflowComponent', () => {
  let component: SysWorkflowComponent;
  let fixture: ComponentFixture<SysWorkflowComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [ SysWorkflowComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(SysWorkflowComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
