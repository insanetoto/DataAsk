import { waitForAsync, ComponentFixture, TestBed } from '@angular/core/testing';
import { CustomerServiceServiceDashboardComponent } from './service-dashboard.component';

describe('CustomerServiceServiceDashboardComponent', () => {
  let component: CustomerServiceServiceDashboardComponent;
  let fixture: ComponentFixture<CustomerServiceServiceDashboardComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [ CustomerServiceServiceDashboardComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(CustomerServiceServiceDashboardComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
