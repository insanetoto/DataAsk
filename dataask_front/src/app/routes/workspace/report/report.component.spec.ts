import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ALAIN_SETTING_KEYS } from '@delon/theme';

import { WorkspaceReportComponent } from './report.component';

describe('WorkspaceReportComponent', () => {
  let component: WorkspaceReportComponent;
  let fixture: ComponentFixture<WorkspaceReportComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [WorkspaceReportComponent],
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        { provide: ALAIN_SETTING_KEYS, useValue: { layout: {}, theme: {}, app: {} } }
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(WorkspaceReportComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
