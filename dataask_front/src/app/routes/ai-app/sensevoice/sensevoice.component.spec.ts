import { waitForAsync, ComponentFixture, TestBed } from '@angular/core/testing';
import { AiAppSensevoiceComponent } from './sensevoice.component';

describe('AiAppSensevoiceComponent', () => {
  let component: AiAppSensevoiceComponent;
  let fixture: ComponentFixture<AiAppSensevoiceComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [ AiAppSensevoiceComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(AiAppSensevoiceComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
