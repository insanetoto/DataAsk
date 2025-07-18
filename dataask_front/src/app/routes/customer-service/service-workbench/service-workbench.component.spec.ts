import { waitForAsync, ComponentFixture, TestBed } from '@angular/core/testing';
import { CustomerServiceServiceWorkbenchComponent } from './service-workbench.component';

describe('CustomerServiceServiceWorkbenchComponent', () => {
  let component: CustomerServiceServiceWorkbenchComponent;
  let fixture: ComponentFixture<CustomerServiceServiceWorkbenchComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [ CustomerServiceServiceWorkbenchComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(CustomerServiceServiceWorkbenchComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
