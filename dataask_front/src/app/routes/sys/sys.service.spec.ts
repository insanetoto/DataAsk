import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';

import { SysService } from './sys.service';

describe('SysService', () => {
  let service: SysService;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [SysService, provideHttpClient(), provideHttpClientTesting()]
    });
    service = TestBed.inject(SysService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
