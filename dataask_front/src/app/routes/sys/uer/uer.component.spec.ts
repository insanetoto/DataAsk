import { waitForAsync, ComponentFixture, TestBed } from '@angular/core/testing';
import { SysUerComponent } from './uer.component';

describe('SysUerComponent', () => {
  let component: SysUerComponent;
  let fixture: ComponentFixture<SysUerComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [ SysUerComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(SysUerComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
