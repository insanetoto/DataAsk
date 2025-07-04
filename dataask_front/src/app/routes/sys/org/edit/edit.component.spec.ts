import { waitForAsync, ComponentFixture, TestBed } from '@angular/core/testing';
import { SysEditComponent } from './edit.component';

describe('SysEditComponent', () => {
  let component: SysEditComponent;
  let fixture: ComponentFixture<SysEditComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [ SysEditComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(SysEditComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
