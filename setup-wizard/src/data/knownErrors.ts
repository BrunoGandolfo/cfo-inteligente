import type { KnownError } from '../types';

export const knownErrors: KnownError[] = [
  {
    patterns: ['nvidia-smi', 'NVIDIA-SMI has failed', 'No devices were found'],
    title: 'nvidia-smi no funciona',
    cause: 'Driver NVIDIA no instalado en Windows o WSL sin acceso GPU.',
    solutions: [
      'Verificar driver NVIDIA instalado EN WINDOWS: nvidia.com/drivers',
      'Reiniciar WSL: wsl --shutdown && wsl',
      'Verificar WSL2: wsl --version',
      'Habilitar Virtual Machine Platform en Windows',
    ],
  },
  {
    patterns: ['CUDA', 'cuda', 'nvcc', 'libcuda', 'CUDA driver version'],
    title: 'Error de CUDA',
    cause: 'Versión CUDA incompatible o toolkit mal instalado.',
    solutions: [
      'nvcc --version (necesitás 12.8+)',
      'Verificar PATH: echo $PATH | grep cuda',
      'Reinstalar toolkit',
      'RTX 5090 NECESITA CUDA 12.8 mínimo',
    ],
  },
  {
    patterns: ['ollama', 'Ollama', 'connection refused', '11434'],
    title: 'Error de Ollama',
    cause: 'Ollama no está corriendo.',
    solutions: [
      'systemctl status ollama',
      'ollama serve &',
      'OLLAMA_NUM_GPU=999 ollama serve',
    ],
  },
  {
    patterns: ['vllm', 'vLLM', 'tensor_parallel', 'NCCL', 'nccl'],
    title: 'Error de vLLM / NCCL',
    cause: 'Problema comunicación entre GPUs.',
    solutions: [
      'export NCCL_P2P_DISABLE=1',
      'export NCCL_TIMEOUT=1800',
      'Verificar GPUs: python -c "import torch; print(torch.cuda.device_count())"',
    ],
  },
  {
    patterns: ['torch', 'pytorch', 'sm_120', 'compute capability'],
    title: 'Error PyTorch / Blackwell',
    cause: 'PyTorch estable no soporta sm_120. Necesitás nightly.',
    solutions: [
      'pip install --pre torch --index-url https://download.pytorch.org/whl/nightly/cu128',
      'Desinstalar primero: pip uninstall torch -y',
      'Verificar: python -c "import torch; print(torch.cuda.get_arch_list())"',
    ],
  },
  {
    patterns: ['out of memory', 'OOM', 'CUDA out of memory'],
    title: 'Sin memoria GPU (OOM)',
    cause: 'Modelo muy grande para VRAM.',
    solutions: [
      'Probar cuantización menor (q4_K_M)',
      'vLLM: --gpu-memory-utilization 0.85',
      'Cerrar apps con GPU (Chrome, etc.)',
    ],
  },
  {
    patterns: ['temperature', 'thermal', 'throttl', 'power limit'],
    title: 'Throttling térmico',
    cause: 'GPU demasiado caliente.',
    solutions: [
      'nvidia-smi -q -d TEMPERATURE',
      'Ideal <80°C, Crítico >90°C',
      'Mejorar ventilación',
      'nvidia-smi -pl [watts] para undervolt',
    ],
  },
  {
    patterns: ['permission', 'denied', 'sudo'],
    title: 'Error de permisos',
    cause: 'Permisos insuficientes.',
    solutions: [
      'Usar sudo',
      'Docker: sudo usermod -aG docker $USER',
      'Verificar: ls -la [archivo]',
    ],
  },
  {
    patterns: ['docker', 'Docker', 'daemon', 'container'],
    title: 'Error de Docker',
    cause: 'Docker no corriendo.',
    solutions: [
      'sudo systemctl start docker',
      'GPUs: instalar nvidia-container-toolkit',
      'Test: docker run --rm --gpus all nvidia/cuda:12.8.0-base-ubuntu22.04 nvidia-smi',
    ],
  },
  {
    patterns: ['wsl', 'WSL', 'WslRegisterDistribution'],
    title: 'Error de WSL',
    cause: 'WSL2 mal configurado.',
    solutions: [
      'Habilitar VT-x en BIOS',
      'wsl --update',
      'wsl --version (kernel 5.10+)',
      'Reiniciar PC',
    ],
  },
];
