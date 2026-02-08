export interface Step {
  id: string;
  phase: number;
  title: string;
  icon: string;
}

export interface Phase {
  name: string;
  color: string;
}

export interface Command {
  command: string;
  description: string;
}

export interface StepContent {
  why: string;
  alternative?: string;
  explanation?: string;
  commands: Command[];
  successCriteria?: string;
}

export interface KnownError {
  patterns: string[];
  title: string;
  cause: string;
  solutions: string[];
}

export interface ProgressState {
  completed: Record<number, boolean>;
  timestamps: Record<number, string>;
  currentStep: number;
}

// System detection
export interface DetectionResult {
  id: string;
  name: string;
  status: 'ok' | 'warning' | 'error' | 'not_installed';
  version?: string;
  details?: string;
  message: string;
}

export interface SystemDetection {
  timestamp: string;
  results: DetectionResult[];
}

// Hardware inventory
export interface HardwareItem {
  id: string;
  category: string;
  model: string;
  specs: string;
  status: 'installed' | 'pending' | 'ordered';
  price?: number;
  notes?: string;
}

// App views
export type AppView = 'setup' | 'hardware' | 'sistema';
