import { Component } from '@angular/core';
import { NzCardModule } from 'ng-zorro-antd/card';

@Component({
  selector: 'app-personal-workspace',
  imports: [NzCardModule],
  templateUrl: './personal-workspace.component.html',
  styles: [`
    .page-container {
      padding: 24px;
    }
    .page-header {
      margin-bottom: 24px;
      text-align: center;
    }
    .page-header h1 {
      font-size: 32px;
      font-weight: 600;
      color: #262626;
      margin-bottom: 8px;
    }
    .page-header p {
      font-size: 16px;
      color: #8c8c8c;
      margin: 0;
    }
    .page-content {
      max-width: 1200px;
      margin: 0 auto;
    }
  `]
})
export class PersonalWorkspaceComponent {

}
