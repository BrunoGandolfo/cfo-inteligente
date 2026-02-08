import { exec } from 'child_process';
import { promisify } from 'util';

const execAsync = promisify(exec);

export interface DetectionResult {
  id: string;
  name: string;
  status: 'ok' | 'warning' | 'error' | 'not_installed';
  version?: string;
  details?: string;
  message: string;
}

async function run(cmd: string, timeout = 10000): Promise<string> {
  try {
    const { stdout } = await execAsync(cmd, { timeout });
    return stdout.trim();
  } catch {
    return '';
  }
}

async function detectWSL(): Promise<DetectionResult> {
  const version = await run('cat /proc/version');
  if (version.includes('microsoft') || version.includes('WSL')) {
    const kernel = await run('uname -r');
    const parts = kernel.split('.');
    const major = parseInt(parts[0] || '0');
    const minor = parseInt(parts[1] || '0');
    const ok = major > 5 || (major === 5 && minor >= 10);
    return {
      id: 'wsl', name: 'WSL2',
      status: ok ? 'ok' : 'warning',
      version: kernel,
      message: ok ? `Kernel ${kernel}` : `Kernel ${kernel} — se recomienda 5.10+`,
    };
  }
  return { id: 'wsl', name: 'WSL2', status: 'error', message: 'No detectado como WSL' };
}

async function detectGPU(): Promise<DetectionResult> {
  const out = await run('nvidia-smi --query-gpu=name,memory.total,driver_version,compute_cap --format=csv,noheader');
  if (!out) {
    return { id: 'gpu', name: 'GPU NVIDIA', status: 'error', message: 'nvidia-smi no disponible' };
  }
  const gpus = out.split('\n').filter(Boolean);
  const details = gpus.map((line, i) => {
    const [name, mem, driver, compute] = line.split(',').map(s => s.trim());
    return `GPU ${i}: ${name} | ${mem} | Driver ${driver} | Compute ${compute}`;
  }).join('\n');
  return {
    id: 'gpu', name: 'GPU NVIDIA',
    status: 'ok',
    version: `${gpus.length} GPU(s)`,
    details,
    message: `${gpus.length} GPU(s) detectada(s)`,
  };
}

async function detectCUDA(): Promise<DetectionResult> {
  const out = await run('nvcc --version 2>/dev/null');
  if (!out) {
    return { id: 'cuda', name: 'CUDA Toolkit', status: 'not_installed', message: 'No instalado' };
  }
  const match = out.match(/release ([\d.]+)/);
  const ver = match ? match[1] : 'desconocida';
  const major = parseFloat(ver);
  return {
    id: 'cuda', name: 'CUDA Toolkit',
    status: major >= 12.8 ? 'ok' : 'warning',
    version: ver,
    message: major >= 12.8 ? `v${ver}` : `v${ver} — RTX 5090 necesita 12.8+`,
  };
}

async function detectPython(): Promise<DetectionResult> {
  const out = await run('python3 --version 2>/dev/null');
  if (!out) {
    return { id: 'python', name: 'Python', status: 'not_installed', message: 'No instalado' };
  }
  const ver = out.replace('Python ', '');
  return { id: 'python', name: 'Python', status: 'ok', version: ver, message: `v${ver}` };
}

async function detectOllama(): Promise<DetectionResult> {
  const ver = await run('ollama --version 2>/dev/null');
  if (!ver) {
    return { id: 'ollama', name: 'Ollama', status: 'not_installed', message: 'No instalado' };
  }
  const version = ver.replace(/.*version\s*/i, '').trim();
  // Check if running
  const api = await run('curl -s --max-time 3 http://localhost:11434/api/tags 2>/dev/null');
  const running = api.includes('models');
  return {
    id: 'ollama', name: 'Ollama',
    status: running ? 'ok' : 'warning',
    version,
    message: running ? `v${version} — corriendo` : `v${version} — instalado pero no corriendo`,
  };
}

async function detectDocker(): Promise<DetectionResult> {
  const ver = await run('docker --version 2>/dev/null');
  if (!ver) {
    return { id: 'docker', name: 'Docker', status: 'not_installed', message: 'No instalado' };
  }
  const match = ver.match(/([\d.]+)/);
  const version = match ? match[1] : 'desconocida';
  const running = await run('docker info 2>/dev/null');
  return {
    id: 'docker', name: 'Docker',
    status: running ? 'ok' : 'warning',
    version,
    message: running ? `v${version} — corriendo` : `v${version} — instalado pero no corriendo`,
  };
}

async function detectPyTorch(): Promise<DetectionResult> {
  const out = await run('python3 -c "import torch; print(torch.__version__, torch.version.cuda, torch.cuda.device_count())" 2>/dev/null');
  if (!out) {
    return { id: 'pytorch', name: 'PyTorch', status: 'not_installed', message: 'No instalado' };
  }
  const [ver, cuda, gpus] = out.split(' ');
  return {
    id: 'pytorch', name: 'PyTorch',
    status: 'ok',
    version: ver,
    message: `v${ver} | CUDA ${cuda} | ${gpus} GPU(s)`,
  };
}

async function detectVLLM(): Promise<DetectionResult> {
  const out = await run('python3 -c "import vllm; print(vllm.__version__)" 2>/dev/null');
  if (!out) {
    return { id: 'vllm', name: 'vLLM', status: 'not_installed', message: 'No instalado' };
  }
  return { id: 'vllm', name: 'vLLM', status: 'ok', version: out, message: `v${out}` };
}

async function detectDisk(): Promise<DetectionResult> {
  const out = await run("df -h / | tail -1 | awk '{print $4}'");
  if (!out) {
    return { id: 'disk', name: 'Disco', status: 'warning', message: 'No se pudo verificar' };
  }
  return { id: 'disk', name: 'Disco disponible', status: 'ok', version: out, message: `${out} libres` };
}

async function detectRAM(): Promise<DetectionResult> {
  const out = await run("free -h | grep Mem | awk '{print $2}'");
  if (!out) {
    return { id: 'ram', name: 'RAM', status: 'warning', message: 'No se pudo verificar' };
  }
  return { id: 'ram', name: 'RAM total', status: 'ok', version: out, message: out };
}

async function detectNode(): Promise<DetectionResult> {
  const out = await run('node --version 2>/dev/null');
  if (!out) {
    return { id: 'node', name: 'Node.js', status: 'not_installed', message: 'No instalado' };
  }
  return { id: 'node', name: 'Node.js', status: 'ok', version: out, message: out };
}

export async function detectAll(): Promise<DetectionResult[]> {
  const results = await Promise.all([
    detectWSL(),
    detectGPU(),
    detectCUDA(),
    detectPython(),
    detectPyTorch(),
    detectVLLM(),
    detectOllama(),
    detectDocker(),
    detectNode(),
    detectRAM(),
    detectDisk(),
  ]);
  return results;
}
