import { CommonModule } from '@angular/common';
import { Component, OnInit, OnDestroy } from '@angular/core';
import { PageHeaderModule } from '@delon/abc/page-header';
import { NzCardModule } from 'ng-zorro-antd/card';

interface SystemStats {
  cpuUsage: number;
  memoryUsage: number;
  diskUsage: number;
  networkSpeed: number;
}

interface ServiceStatus {
  name: string;
  description: string;
  status: string;
}

interface SystemInfo {
  os: string;
  uptime: string;
  cpu: string;
  totalMemory: string;
  availableMemory: string;
}

@Component({
  selector: 'app-workspace-monitor',
  templateUrl: './monitor.component.html',
  standalone: true,
  imports: [CommonModule, PageHeaderModule, NzCardModule]
})
export class WorkspaceMonitorComponent implements OnInit, OnDestroy {
  systemStats: SystemStats = {
    cpuUsage: 45,
    memoryUsage: 62,
    diskUsage: 35,
    networkSpeed: 120
  };

  services: ServiceStatus[] = [
    {
      name: 'MySQL数据库',
      description: '主数据库服务',
      status: '运行中'
    },
    {
      name: 'Redis缓存',
      description: '缓存服务',
      status: '运行中'
    },
    {
      name: 'Python后端',
      description: 'Flask应用服务',
      status: '运行中'
    },
    {
      name: 'AI引擎',
      description: 'Vanna AI服务',
      status: '运行中'
    }
  ];

  systemInfo: SystemInfo = {
    os: 'Linux Ubuntu 20.04',
    uptime: '15天 8小时 32分钟',
    cpu: 'Intel Core i7-9750H',
    totalMemory: '16GB',
    availableMemory: '8.5GB'
  };

  private updateTimer: any;

  ngOnInit(): void {
    this.loadSystemStats();
    // 每10秒更新一次系统状态
    this.updateTimer = setInterval(() => {
      this.loadSystemStats();
    }, 10000);
  }

  ngOnDestroy(): void {
    if (this.updateTimer) {
      clearInterval(this.updateTimer);
    }
  }

  loadSystemStats(): void {
    // 模拟实时数据
    this.systemStats = {
      cpuUsage: Math.floor(Math.random() * 40) + 10,
      memoryUsage: Math.floor(Math.random() * 30) + 40,
      diskUsage: Math.floor(Math.random() * 20) + 30,
      networkSpeed: Math.floor(Math.random() * 100) + 50
    };
  }

  getCpuColor(): string {
    if (this.systemStats.cpuUsage > 80) return '#ff4d4f';
    if (this.systemStats.cpuUsage > 60) return '#faad14';
    return '#52c41a';
  }

  getMemoryColor(): string {
    if (this.systemStats.memoryUsage > 80) return '#ff4d4f';
    if (this.systemStats.memoryUsage > 60) return '#faad14';
    return '#52c41a';
  }

  getDiskColor(): string {
    if (this.systemStats.diskUsage > 80) return '#ff4d4f';
    if (this.systemStats.diskUsage > 60) return '#faad14';
    return '#52c41a';
  }
}
