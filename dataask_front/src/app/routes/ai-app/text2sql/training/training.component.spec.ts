import { waitForAsync, ComponentFixture, TestBed } from '@angular/core/testing';
import { AiAppTrainingComponent } from './training.component';

describe('AiAppTrainingComponent', () => {
  let component: AiAppTrainingComponent;
  let fixture: ComponentFixture<AiAppTrainingComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [ AiAppTrainingComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(AiAppTrainingComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
