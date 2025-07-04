import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ALAIN_SETTING_KEYS } from '@delon/theme';

import { AiEngineKnowledgeBaseComponent } from './knowledge-base.component';

describe('AiEngineKnowledgeBaseComponent', () => {
  let component: AiEngineKnowledgeBaseComponent;
  let fixture: ComponentFixture<AiEngineKnowledgeBaseComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [AiEngineKnowledgeBaseComponent],
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        { provide: ALAIN_SETTING_KEYS, useValue: { layout: {}, theme: {}, app: {} } }
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(AiEngineKnowledgeBaseComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
