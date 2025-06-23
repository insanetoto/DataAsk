import { waitForAsync, ComponentFixture, TestBed } from '@angular/core/testing';

import { AiEngineAskDataComponent } from './ask-data.component';

describe('AiEngineAskDataComponent', () => {
  let component: AiEngineAskDataComponent;
  let fixture: ComponentFixture<AiEngineAskDataComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [AiEngineAskDataComponent]
    }).compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(AiEngineAskDataComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
