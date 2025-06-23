import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ALAIN_SETTING_KEYS } from '@delon/theme';

import { WorkspaceWorkbenchComponent } from './workbench.component';

describe('WorkspaceWorkbenchComponent', () => {
  let component: WorkspaceWorkbenchComponent;
  let fixture: ComponentFixture<WorkspaceWorkbenchComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [WorkspaceWorkbenchComponent],
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        { provide: ALAIN_SETTING_KEYS, useValue: { layout: {}, theme: {}, app: {} } }
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(WorkspaceWorkbenchComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
