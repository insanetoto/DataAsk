import { waitForAsync, ComponentFixture, TestBed } from '@angular/core/testing';
import { SysMessageComponent } from './message.component';

describe('SysMessageComponent', () => {
  let component: SysMessageComponent;
  let fixture: ComponentFixture<SysMessageComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [ SysMessageComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(SysMessageComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
