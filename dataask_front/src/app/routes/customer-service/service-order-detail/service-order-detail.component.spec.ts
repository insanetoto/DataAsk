import { waitForAsync, ComponentFixture, TestBed } from '@angular/core/testing';
import { CustomerServiceServiceOrderDetailComponent } from './service-order-detail.component';

describe('CustomerServiceServiceOrderDetailComponent', () => {
  let component: CustomerServiceServiceOrderDetailComponent;
  let fixture: ComponentFixture<CustomerServiceServiceOrderDetailComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [ CustomerServiceServiceOrderDetailComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(CustomerServiceServiceOrderDetailComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
