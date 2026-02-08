import { exec } from 'child_process';
import { promisify } from 'util';

const execAsync = promisify(exec);

export type DetectionCategory = 'hardware' | 'ai_runtime' | 'ai_frameworks' | 'ai_servers' | 'dev_tools';

export interface DetectionResult {
  id: string;
  name: string;
  category: DetectionCategory;
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

// ============================================================
//  HARDWARE
// ============================================================

async function detectCPU(): Promise<DetectionResult> {
  const model = await run("cat /proc/cpuinfo | grep 'model name' | head -1 | cut -d: -f2");
  const cores = await run("nproc");
  const threads = await run("cat /proc/cpuinfo | grep 'processor' | wc -l");
  if (!model) {
    return { id: 'cpu', name: 'CPU', category: 'hardware', status: 'warning', message: 'No se pudo detectar' };
  }
  const m = model.trim();
  return {
    id: 'cpu', name: 'CPU', category: 'hardware',
    status: 'ok',
    version: m,
    details: `Modelo: ${m}\nNucleos fisicos: ${cores}\nThreads: ${threads}`,
    message: `${m} — ${cores} nucleos, ${threads} threads`,
  };
}

async function detectGPU(): Promise<DetectionResult> {
  const out = await run('nvidia-smi --query-gpu=name,memory.total,memory.used,memory.free,driver_version,compute_cap,temperature.gpu,utilization.gpu,power.draw --format=csv,noheader,nounits');
  if (!out) {
    return { id: 'gpu', name: 'GPU NVIDIA', category: 'hardware', status: 'error', message: 'nvidia-smi no disponible — no se detecta GPU NVIDIA' };
  }
  const gpus = out.split('\n').filter(Boolean);
  const details = gpus.map((line, i) => {
    const parts = line.split(',').map(s => s.trim());
    const [name, memTotal, memUsed, memFree, driver, compute, temp, util, power] = parts;
    return [
      `GPU ${i}: ${name}`,
      `  VRAM: ${memUsed} / ${memTotal} MiB (${memFree} MiB libre)`,
      `  Driver: ${driver} | Compute: ${compute}`,
      `  Temp: ${temp}°C | Uso: ${util}% | Consumo: ${power}W`,
    ].join('\n');
  }).join('\n\n');

  const isBlackwell = gpus.some(g => g.includes('5090') || g.includes('5080') || g.includes('50'));
  const status = gpus.length >= 2 ? 'ok' : isBlackwell ? 'ok' : 'warning';
  const msg = gpus.length >= 2
    ? `${gpus.length} GPUs detectadas — Dual GPU activo`
    : `${gpus.length} GPU detectada`;

  return {
    id: 'gpu', name: 'GPU NVIDIA', category: 'hardware',
    status,
    version: `${gpus.length} GPU(s)`,
    details,
    message: msg,
  };
}

async function detectRAM(): Promise<DetectionResult> {
  const total = await run("free -h | grep Mem | awk '{print $2}'");
  const used = await run("free -h | grep Mem | awk '{print $3}'");
  const available = await run("free -h | grep Mem | awk '{print $7}'");
  const totalGB = await run("free -g | grep Mem | awk '{print $2}'");
  if (!total) {
    return { id: 'ram', name: 'RAM', category: 'hardware', status: 'warning', message: 'No se pudo detectar' };
  }
  const gb = parseInt(totalGB || '0');
  // Para modelos grandes como qwen2.5:72b necesitas bastante RAM
  const status = gb >= 128 ? 'ok' : gb >= 48 ? 'warning' : 'error';
  const hint = gb < 64 ? ' — se recomiendan 64GB+ para modelos grandes' : '';
  return {
    id: 'ram', name: 'RAM', category: 'hardware',
    status,
    version: total,
    details: `Total: ${total}\nUsada: ${used}\nDisponible: ${available}`,
    message: `${total} total, ${available} disponible${hint}`,
  };
}

async function detectDisks(): Promise<DetectionResult> {
  const out = await run("lsblk -o NAME,SIZE,TYPE,MOUNTPOINT,FSTYPE 2>/dev/null | grep -v loop");
  const dfOut = await run("df -h --output=source,size,used,avail,pcent,target 2>/dev/null | grep -E '^/dev'");
  if (!out && !dfOut) {
    return { id: 'disk', name: 'Almacenamiento', category: 'hardware', status: 'warning', message: 'No se pudo detectar' };
  }
  // Check for NVMe drives specifically
  const nvme = await run("ls /dev/nvme* 2>/dev/null | head -10");
  const hasNVMe = nvme.includes('nvme');

  const details = [
    dfOut ? `Particiones montadas:\n${dfOut}` : '',
    hasNVMe ? `\nDispositivos NVMe detectados: Si` : '',
  ].filter(Boolean).join('\n');

  return {
    id: 'disk', name: 'Almacenamiento', category: 'hardware',
    status: 'ok',
    details,
    message: hasNVMe ? 'NVMe detectado — almacenamiento rapido disponible' : 'Almacenamiento detectado',
  };
}

async function detectWSL(): Promise<DetectionResult> {
  const version = await run('cat /proc/version');
  if (version.includes('microsoft') || version.includes('WSL')) {
    const kernel = await run('uname -r');
    const wslVer = await run('cat /proc/sys/fs/binfmt_misc/WSLInterop 2>/dev/null && echo WSL2 || echo WSL');
    const parts = kernel.split('.');
    const major = parseInt(parts[0] || '0');
    const minor = parseInt(parts[1] || '0');
    const ok = major > 5 || (major === 5 && minor >= 10);
    return {
      id: 'wsl', name: 'WSL2', category: 'hardware',
      status: ok ? 'ok' : 'warning',
      version: kernel,
      details: `Kernel: ${kernel}\nVersion: WSL2\nGPU Passthrough: Soportado`,
      message: ok ? `WSL2 Kernel ${kernel} — GPU passthrough activo` : `Kernel ${kernel} — se recomienda 5.10+`,
    };
  }
  return { id: 'wsl', name: 'WSL2', category: 'hardware', status: 'error', message: 'No detectado como WSL' };
}

// ============================================================
//  AI RUNTIME (drivers, CUDA, cuDNN, containers)
// ============================================================

async function detectCUDA(): Promise<DetectionResult> {
  const out = await run('nvcc --version 2>/dev/null');
  if (!out) {
    // Check if CUDA is available via nvidia-smi even without toolkit
    const smiCuda = await run("nvidia-smi 2>/dev/null | grep 'CUDA Version' | awk '{print $9}'");
    if (smiCuda) {
      return {
        id: 'cuda', name: 'CUDA Toolkit', category: 'ai_runtime',
        status: 'warning',
        version: smiCuda,
        message: `Driver soporta CUDA ${smiCuda} pero nvcc no instalado — instalar CUDA Toolkit`,
      };
    }
    return { id: 'cuda', name: 'CUDA Toolkit', category: 'ai_runtime', status: 'not_installed', message: 'No instalado' };
  }
  const match = out.match(/release ([\d.]+)/);
  const ver = match ? match[1] : 'desconocida';
  const major = parseFloat(ver);
  return {
    id: 'cuda', name: 'CUDA Toolkit', category: 'ai_runtime',
    status: major >= 12.8 ? 'ok' : 'warning',
    version: ver,
    message: major >= 12.8 ? `v${ver} — compatible con RTX 5090` : `v${ver} — RTX 5090 (Blackwell) necesita 12.8+`,
  };
}

async function detectCuDNN(): Promise<DetectionResult> {
  // Try dpkg first
  let ver = await run("dpkg -l 2>/dev/null | grep cudnn | head -1 | awk '{print $3}'");
  if (!ver) {
    // Try checking header file
    ver = await run("cat /usr/include/cudnn_version.h 2>/dev/null | grep CUDNN_MAJOR -A2 | head -3");
    if (ver) {
      const major = ver.match(/CUDNN_MAJOR\s+(\d+)/)?.[1] || '';
      const minor = ver.match(/CUDNN_MINOR\s+(\d+)/)?.[1] || '';
      const patch = ver.match(/CUDNN_PATCHLEVEL\s+(\d+)/)?.[1] || '';
      ver = `${major}.${minor}.${patch}`;
    }
  }
  if (!ver) {
    // Try finding the library
    const lib = await run("find /usr/lib /usr/local/lib -name 'libcudnn*.so*' 2>/dev/null | head -1");
    if (lib) {
      return {
        id: 'cudnn', name: 'cuDNN', category: 'ai_runtime',
        status: 'ok', message: 'Libreria detectada (version no determinada)',
      };
    }
    return { id: 'cudnn', name: 'cuDNN', category: 'ai_runtime', status: 'not_installed', message: 'No instalado — necesario para deep learning' };
  }
  return {
    id: 'cudnn', name: 'cuDNN', category: 'ai_runtime',
    status: 'ok', version: ver, message: `v${ver}`,
  };
}

async function detectNVContainerToolkit(): Promise<DetectionResult> {
  const ver = await run('nvidia-ctk --version 2>/dev/null');
  if (!ver) {
    const pkg = await run("dpkg -l 2>/dev/null | grep nvidia-container-toolkit | head -1 | awk '{print $3}'");
    if (pkg) {
      return {
        id: 'nv_container', name: 'NVIDIA Container Toolkit', category: 'ai_runtime',
        status: 'ok', version: pkg, message: `v${pkg}`,
      };
    }
    return { id: 'nv_container', name: 'NVIDIA Container Toolkit', category: 'ai_runtime', status: 'not_installed', message: 'No instalado — necesario para GPU en Docker' };
  }
  const version = ver.match(/version\s+([\d.]+)/i)?.[1] || ver;
  return {
    id: 'nv_container', name: 'NVIDIA Container Toolkit', category: 'ai_runtime',
    status: 'ok', version, message: `v${version}`,
  };
}

// ============================================================
//  AI FRAMEWORKS (PyTorch, TensorFlow, Transformers, etc.)
// ============================================================

async function detectPyTorch(): Promise<DetectionResult> {
  const out = await run('python3 -c "import torch; print(torch.__version__, torch.version.cuda or \'no-cuda\', torch.cuda.device_count(), torch.cuda.is_available())" 2>/dev/null');
  if (!out) {
    return { id: 'pytorch', name: 'PyTorch', category: 'ai_frameworks', status: 'not_installed', message: 'No instalado' };
  }
  const parts = out.split(' ');
  const [ver, cuda, gpuCount, cudaAvail] = parts;
  const hasCuda = cudaAvail === 'True';
  return {
    id: 'pytorch', name: 'PyTorch', category: 'ai_frameworks',
    status: hasCuda ? 'ok' : 'warning',
    version: ver,
    details: `Version: ${ver}\nCUDA: ${cuda}\nGPUs visibles: ${gpuCount}\nCUDA disponible: ${hasCuda ? 'Si' : 'No'}`,
    message: hasCuda ? `v${ver} | CUDA ${cuda} | ${gpuCount} GPU(s)` : `v${ver} — CUDA no disponible`,
  };
}

async function detectTensorFlow(): Promise<DetectionResult> {
  const out = await run('python3 -c "import tensorflow as tf; print(tf.__version__, len(tf.config.list_physical_devices(\'GPU\')))" 2>/dev/null');
  if (!out) {
    return { id: 'tensorflow', name: 'TensorFlow', category: 'ai_frameworks', status: 'not_installed', message: 'No instalado' };
  }
  const [ver, gpus] = out.split(' ');
  const hasGPU = parseInt(gpus || '0') > 0;
  return {
    id: 'tensorflow', name: 'TensorFlow', category: 'ai_frameworks',
    status: hasGPU ? 'ok' : 'warning',
    version: ver,
    message: hasGPU ? `v${ver} | ${gpus} GPU(s)` : `v${ver} — sin GPU`,
  };
}

async function detectTransformers(): Promise<DetectionResult> {
  const out = await run('python3 -c "import transformers; print(transformers.__version__)" 2>/dev/null');
  if (!out) {
    return { id: 'transformers', name: 'HuggingFace Transformers', category: 'ai_frameworks', status: 'not_installed', message: 'No instalado' };
  }
  return {
    id: 'transformers', name: 'HuggingFace Transformers', category: 'ai_frameworks',
    status: 'ok', version: out, message: `v${out}`,
  };
}

async function detectVLLM(): Promise<DetectionResult> {
  const out = await run('python3 -c "import vllm; print(vllm.__version__)" 2>/dev/null');
  if (!out) {
    return { id: 'vllm', name: 'vLLM', category: 'ai_frameworks', status: 'not_installed', message: 'No instalado — motor de inferencia de alto rendimiento' };
  }
  return { id: 'vllm', name: 'vLLM', category: 'ai_frameworks', status: 'ok', version: out, message: `v${out}` };
}

async function detectLlamaCpp(): Promise<DetectionResult> {
  // Check for llama-cpp-python binding
  const pyOut = await run('python3 -c "import llama_cpp; print(llama_cpp.__version__)" 2>/dev/null');
  if (pyOut) {
    return {
      id: 'llama_cpp', name: 'llama.cpp (Python)', category: 'ai_frameworks',
      status: 'ok', version: pyOut, message: `v${pyOut}`,
    };
  }
  // Check for llama.cpp binary
  const bin = await run('which llama-server 2>/dev/null || which llama-cli 2>/dev/null || which main 2>/dev/null');
  if (bin) {
    return {
      id: 'llama_cpp', name: 'llama.cpp', category: 'ai_frameworks',
      status: 'ok', message: `Binario en ${bin}`,
    };
  }
  return { id: 'llama_cpp', name: 'llama.cpp', category: 'ai_frameworks', status: 'not_installed', message: 'No instalado' };
}

// ============================================================
//  AI SERVERS (Ollama, TGI, etc.)
// ============================================================

async function detectOllama(): Promise<DetectionResult> {
  const ver = await run('ollama --version 2>/dev/null');
  if (!ver) {
    return { id: 'ollama', name: 'Ollama', category: 'ai_servers', status: 'not_installed', message: 'No instalado — servidor local de modelos LLM' };
  }
  const version = ver.replace(/.*version\s*/i, '').trim();
  const api = await run('curl -s --max-time 3 http://localhost:11434/api/tags 2>/dev/null');
  const running = api.includes('models');
  let models = '';
  if (running) {
    try {
      const parsed = JSON.parse(api);
      if (parsed.models && Array.isArray(parsed.models)) {
        models = parsed.models.map((m: { name: string; size?: number }) => {
          const sizeGB = m.size ? (m.size / 1e9).toFixed(1) + 'GB' : '';
          return `  ${m.name} ${sizeGB}`;
        }).join('\n');
      }
    } catch { /* ignore parse error */ }
  }
  return {
    id: 'ollama', name: 'Ollama', category: 'ai_servers',
    status: running ? 'ok' : 'warning',
    version,
    details: models ? `Modelos descargados:\n${models}` : undefined,
    message: running
      ? `v${version} — corriendo`
      : `v${version} — instalado pero no corriendo (ollama serve)`,
  };
}

async function detectDocker(): Promise<DetectionResult> {
  const ver = await run('docker --version 2>/dev/null');
  if (!ver) {
    return { id: 'docker', name: 'Docker', category: 'ai_servers', status: 'not_installed', message: 'No instalado — necesario para algunos servicios IA' };
  }
  const match = ver.match(/([\d.]+)/);
  const version = match ? match[1] : 'desconocida';
  const running = await run('docker info 2>/dev/null');
  // Check for AI-related containers
  let aiContainers = '';
  if (running) {
    aiContainers = await run("docker ps --format '{{.Names}} ({{.Image}})' 2>/dev/null | grep -iE 'ollama|vllm|tgi|llama|gpu|cuda|ai|ml' | head -5");
  }
  return {
    id: 'docker', name: 'Docker', category: 'ai_servers',
    status: running ? 'ok' : 'warning',
    version,
    details: aiContainers ? `Contenedores IA activos:\n${aiContainers}` : undefined,
    message: running
      ? `v${version} — corriendo${aiContainers ? ' (contenedores IA activos)' : ''}`
      : `v${version} — instalado pero no corriendo`,
  };
}

// ============================================================
//  DEVELOPMENT TOOLS
// ============================================================

async function detectPython(): Promise<DetectionResult> {
  const out = await run('python3 --version 2>/dev/null');
  if (!out) {
    return { id: 'python', name: 'Python', category: 'dev_tools', status: 'not_installed', message: 'No instalado' };
  }
  const ver = out.replace('Python ', '');
  const pip = await run('pip3 --version 2>/dev/null');
  const pipVer = pip ? pip.match(/pip ([\d.]+)/)?.[1] || '' : '';
  return {
    id: 'python', name: 'Python', category: 'dev_tools',
    status: 'ok', version: ver,
    details: pipVer ? `Python: ${ver}\npip: ${pipVer}` : undefined,
    message: pipVer ? `v${ver} | pip ${pipVer}` : `v${ver}`,
  };
}

async function detectConda(): Promise<DetectionResult> {
  const conda = await run('conda --version 2>/dev/null');
  const mamba = await run('mamba --version 2>/dev/null | head -1');
  if (!conda && !mamba) {
    return { id: 'conda', name: 'Conda/Mamba', category: 'dev_tools', status: 'not_installed', message: 'No instalado' };
  }
  const mgr = mamba ? 'Mamba' : 'Conda';
  const ver = mamba ? mamba.replace(/.*mamba\s*/i, '').trim() : conda!.replace(/.*conda\s*/i, '').trim();
  // List environments
  const envs = await run('conda env list 2>/dev/null | grep -v "^#" | grep -v "^$"');
  return {
    id: 'conda', name: mgr, category: 'dev_tools',
    status: 'ok', version: ver,
    details: envs ? `Entornos:\n${envs}` : undefined,
    message: `${mgr} v${ver}`,
  };
}

async function detectNode(): Promise<DetectionResult> {
  const out = await run('node --version 2>/dev/null');
  if (!out) {
    return { id: 'node', name: 'Node.js', category: 'dev_tools', status: 'not_installed', message: 'No instalado' };
  }
  return { id: 'node', name: 'Node.js', category: 'dev_tools', status: 'ok', version: out, message: out };
}

async function detectGit(): Promise<DetectionResult> {
  const out = await run('git --version 2>/dev/null');
  if (!out) {
    return { id: 'git', name: 'Git', category: 'dev_tools', status: 'not_installed', message: 'No instalado' };
  }
  const ver = out.replace('git version ', '');
  return { id: 'git', name: 'Git', category: 'dev_tools', status: 'ok', version: ver, message: `v${ver}` };
}

async function detectCMake(): Promise<DetectionResult> {
  const out = await run('cmake --version 2>/dev/null | head -1');
  if (!out) {
    return { id: 'cmake', name: 'CMake', category: 'dev_tools', status: 'not_installed', message: 'No instalado — necesario para compilar llama.cpp, etc.' };
  }
  const ver = out.match(/([\d.]+)/)?.[1] || out;
  return { id: 'cmake', name: 'CMake', category: 'dev_tools', status: 'ok', version: ver, message: `v${ver}` };
}

async function detectGCC(): Promise<DetectionResult> {
  const out = await run('gcc --version 2>/dev/null | head -1');
  if (!out) {
    return { id: 'gcc', name: 'GCC/G++', category: 'dev_tools', status: 'not_installed', message: 'No instalado — necesario para compilar extensiones C++' };
  }
  const ver = out.match(/([\d.]+)/)?.[1] || out;
  return { id: 'gcc', name: 'GCC/G++', category: 'dev_tools', status: 'ok', version: ver, message: `v${ver}` };
}

async function detectHuggingFaceCLI(): Promise<DetectionResult> {
  const out = await run('huggingface-cli version 2>/dev/null');
  if (!out) {
    return { id: 'hf_cli', name: 'HuggingFace CLI', category: 'dev_tools', status: 'not_installed', message: 'No instalado — util para descargar modelos' };
  }
  const ver = out.match(/([\d.]+)/)?.[1] || out;
  return { id: 'hf_cli', name: 'HuggingFace CLI', category: 'dev_tools', status: 'ok', version: ver, message: `v${ver}` };
}

async function detectJupyter(): Promise<DetectionResult> {
  const out = await run('jupyter --version 2>/dev/null | head -1');
  if (!out) {
    return { id: 'jupyter', name: 'Jupyter', category: 'dev_tools', status: 'not_installed', message: 'No instalado' };
  }
  return { id: 'jupyter', name: 'Jupyter', category: 'dev_tools', status: 'ok', version: out.trim(), message: `Instalado` };
}

// ============================================================
//  DETECT ALL
// ============================================================

export const CATEGORY_LABELS: Record<DetectionCategory, string> = {
  hardware: 'Hardware',
  ai_runtime: 'Runtime IA (CUDA, Drivers)',
  ai_frameworks: 'Frameworks IA',
  ai_servers: 'Servidores IA',
  dev_tools: 'Herramientas de Desarrollo',
};

export const CATEGORY_ORDER: DetectionCategory[] = [
  'hardware', 'ai_runtime', 'ai_frameworks', 'ai_servers', 'dev_tools',
];

export async function detectAll(): Promise<DetectionResult[]> {
  const results = await Promise.all([
    // Hardware
    detectCPU(),
    detectGPU(),
    detectRAM(),
    detectDisks(),
    detectWSL(),
    // AI Runtime
    detectCUDA(),
    detectCuDNN(),
    detectNVContainerToolkit(),
    // AI Frameworks
    detectPyTorch(),
    detectTensorFlow(),
    detectTransformers(),
    detectVLLM(),
    detectLlamaCpp(),
    // AI Servers
    detectOllama(),
    detectDocker(),
    // Dev Tools
    detectPython(),
    detectConda(),
    detectNode(),
    detectGit(),
    detectCMake(),
    detectGCC(),
    detectHuggingFaceCLI(),
    detectJupyter(),
  ]);
  return results;
}
