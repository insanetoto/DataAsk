import { waitForAsync, ComponentFixture, TestBed } from '@angular/core/testing';
import { WorkspaceReportComponent } from './report.component';

describe('WorkspaceReportComponent', () => {
  let component: WorkspaceReportComponent;
  let fixture: ComponentFixture<WorkspaceReportComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [ WorkspaceReportComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(WorkspaceReportComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
