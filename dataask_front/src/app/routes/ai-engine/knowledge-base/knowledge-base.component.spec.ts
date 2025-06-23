import { waitForAsync, ComponentFixture, TestBed } from '@angular/core/testing';

import { AiEngineKnowledgeBaseComponent } from './knowledge-base.component';

describe('AiEngineKnowledgeBaseComponent', () => {
  let component: AiEngineKnowledgeBaseComponent;
  let fixture: ComponentFixture<AiEngineKnowledgeBaseComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [AiEngineKnowledgeBaseComponent]
    }).compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(AiEngineKnowledgeBaseComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
