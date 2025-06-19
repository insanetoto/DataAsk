import { waitForAsync, ComponentFixture, TestBed } from '@angular/core/testing';
import { WorkspaceWorkplaceComponent } from './workplace.component';

describe('WorkspaceWorkplaceComponent', () => {
  let component: WorkspaceWorkplaceComponent;
  let fixture: ComponentFixture<WorkspaceWorkplaceComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [ WorkspaceWorkplaceComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(WorkspaceWorkplaceComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
