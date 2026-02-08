import type { Step } from '../types';

export const steps: Step[] = [
  { id: 'overview',       phase: 0, title: 'Bienvenida',          icon: '📋' },
  { id: 'prereqs',        phase: 1, title: 'Verificar WSL2',      icon: '🖥️' },
  { id: 'nvidia-driver',  phase: 1, title: 'Driver NVIDIA',       icon: '🔧' },
  { id: 'cuda',           phase: 1, title: 'CUDA Toolkit 12.8',   icon: '⚡' },
  { id: 'ollama',         phase: 2, title: 'Instalar Ollama',     icon: '🤖' },
  { id: 'model-download', phase: 2, title: 'Descargar Modelos',   icon: '📥' },
  { id: 'vllm',           phase: 2, title: 'Instalar vLLM',       icon: '⚙️' },
  { id: 'openwebui',      phase: 2, title: 'Open WebUI',          icon: '🌐' },
  { id: 'monitoring',     phase: 2, title: 'Monitoreo',           icon: '📊' },
  { id: 'dual-gpu',       phase: 3, title: 'Verificar Dual GPU',  icon: '🔄' },
  { id: 'thermal',        phase: 3, title: 'Test Termico',        icon: '🌡️' },
  { id: 'integration',    phase: 3, title: 'Integrar con CFO',    icon: '🔗' },
];
