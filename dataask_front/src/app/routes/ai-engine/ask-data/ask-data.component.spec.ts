import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ALAIN_SETTING_KEYS } from '@delon/theme';

import { AiEngineAskDataComponent } from './ask-data.component';

describe('AiEngineAskDataComponent', () => {
  let component: AiEngineAskDataComponent;
  let fixture: ComponentFixture<AiEngineAskDataComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [AiEngineAskDataComponent],
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        { provide: ALAIN_SETTING_KEYS, useValue: { layout: {}, theme: {}, app: {} } }
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(AiEngineAskDataComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
