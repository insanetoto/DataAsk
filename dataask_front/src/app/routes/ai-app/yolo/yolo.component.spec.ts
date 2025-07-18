import { waitForAsync, ComponentFixture, TestBed } from '@angular/core/testing';
import { AiAppYoloComponent } from './yolo.component';

describe('AiAppYoloComponent', () => {
  let component: AiAppYoloComponent;
  let fixture: ComponentFixture<AiAppYoloComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [ AiAppYoloComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(AiAppYoloComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
