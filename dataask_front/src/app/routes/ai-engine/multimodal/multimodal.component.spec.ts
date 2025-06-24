import { waitForAsync, ComponentFixture, TestBed } from '@angular/core/testing';
import { AiEngineMultimodalComponent } from './multimodal.component';

describe('AiEngineMultimodalComponent', () => {
  let component: AiEngineMultimodalComponent;
  let fixture: ComponentFixture<AiEngineMultimodalComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [ AiEngineMultimodalComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(AiEngineMultimodalComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
