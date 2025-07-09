import { waitForAsync, ComponentFixture, TestBed } from '@angular/core/testing';
import { AiAppText2sqlComponent } from './text2sql.component';

describe('AiAppText2sqlComponent', () => {
  let component: AiAppText2sqlComponent;
  let fixture: ComponentFixture<AiAppText2sqlComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [ AiAppText2sqlComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(AiAppText2sqlComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
