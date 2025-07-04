import { waitForAsync, ComponentFixture, TestBed } from '@angular/core/testing';
import { SysViewComponent } from './view.component';

describe('SysViewComponent', () => {
  let component: SysViewComponent;
  let fixture: ComponentFixture<SysViewComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [ SysViewComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(SysViewComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
