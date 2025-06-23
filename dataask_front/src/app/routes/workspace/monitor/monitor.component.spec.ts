import { waitForAsync, ComponentFixture, TestBed } from '@angular/core/testing';

import { WorkspaceMonitorComponent } from './monitor.component';

describe('WorkspaceMonitorComponent', () => {
  let component: WorkspaceMonitorComponent;
  let fixture: ComponentFixture<WorkspaceMonitorComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [WorkspaceMonitorComponent]
    }).compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(WorkspaceMonitorComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
