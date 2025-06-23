import { waitForAsync, ComponentFixture, TestBed } from '@angular/core/testing';
import { AiEngineDatasourceComponent } from './datasource.component';

describe('AiEngineDatasourceComponent', () => {
  let component: AiEngineDatasourceComponent;
  let fixture: ComponentFixture<AiEngineDatasourceComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [ AiEngineDatasourceComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(AiEngineDatasourceComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
