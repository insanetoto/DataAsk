import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ALAIN_SETTING_KEYS } from '@delon/theme';

import { WorkspaceMonitorComponent } from './monitor.component';

describe('WorkspaceMonitorComponent', () => {
  let component: WorkspaceMonitorComponent;
  let fixture: ComponentFixture<WorkspaceMonitorComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [WorkspaceMonitorComponent],
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        { provide: ALAIN_SETTING_KEYS, useValue: { layout: {}, theme: {}, app: {} } }
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(WorkspaceMonitorComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
