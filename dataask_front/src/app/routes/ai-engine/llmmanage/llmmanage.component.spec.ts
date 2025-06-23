import { waitForAsync, ComponentFixture, TestBed } from '@angular/core/testing';
import { AiEngineLlmmanageComponent } from './llmmanage.component';

describe('AiEngineLlmmanageComponent', () => {
  let component: AiEngineLlmmanageComponent;
  let fixture: ComponentFixture<AiEngineLlmmanageComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [ AiEngineLlmmanageComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(AiEngineLlmmanageComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
