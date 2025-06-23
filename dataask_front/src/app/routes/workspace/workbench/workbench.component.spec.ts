import { waitForAsync, ComponentFixture, TestBed } from '@angular/core/testing';

import { WorkspaceWorkbenchComponent } from './workbench.component';

describe('WorkspaceWorkbenchComponent', () => {
  let component: WorkspaceWorkbenchComponent;
  let fixture: ComponentFixture<WorkspaceWorkbenchComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [WorkspaceWorkbenchComponent]
    }).compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(WorkspaceWorkbenchComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
