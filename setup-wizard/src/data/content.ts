import type { StepContent } from '../types';

export const stepContent: Record<string, StepContent> = {
  overview: {
    why: 'Esta herramienta te guía paso a paso para preparar tu entorno WSL2 para IA local con dual RTX 5090. El 80% se puede hacer ANTES de que llegue el hardware.',
    explanation:
      `Tu plan es excelente: preparar el software ahora significa que cuando conectes la segunda GPU, solo verificás que se detecta y listo.

AHORA (con tu GPU actual):
• Verificar WSL2 y drivers
• Instalar CUDA 12.8+
• Instalar Ollama + descargar modelos (~42 GB)
• Instalar vLLM para producción
• Configurar monitoreo

DESPUÉS (cuando llegue el hardware):
• Verificar detección dual GPU
• Test térmico bajo carga dual
• Integrar con CFO Inteligente`,
    commands: [],
  },

  prereqs: {
    why: 'WSL2 es tu puerta de entrada a Linux sin dejar Windows. WSL1 NO sirve — no tiene acceso directo a la GPU.',
    alternative: '¿Por qué WSL2 y no Linux nativo? Ya lo tenés funcionando, tu flujo con Cursor/Windows no se interrumpe, y la diferencia es solo 3-5%.',
    commands: [
      { command: 'wsl --version', description: 'Verificar versión (necesitás WSL2 con kernel 5.10+)' },
      { command: 'wsl --update', description: 'Actualizar WSL' },
      { command: 'cat /proc/version', description: 'Verificar kernel de Linux' },
      { command: 'uname -r', description: 'Confirmar versión del kernel (5.10+)' },
    ],
    successCriteria: "Si ves 'WSL version: 2.x.x' y kernel 5.10+, estás bien.",
  },

  'nvidia-driver': {
    why: 'El driver se instala EN WINDOWS, no en WSL. WSL2 accede a la GPU via paravirtualización (GPU-PV). NO instalar driver NVIDIA dentro de WSL.',
    alternative: '¿Por qué no en WSL? Porque GPU-PV expone la GPU automáticamente. Un driver en WSL causa conflictos.',
    commands: [
      { command: 'nvidia-smi', description: 'Verificar que WSL detecta tu GPU' },
      { command: 'nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv', description: 'Ver detalles' },
      { command: 'nvidia-smi -q -d COMPUTE', description: 'Verificar compute capability (12.0 para Blackwell)' },
    ],
    successCriteria: 'RTX 5090 con ~32 GB VRAM y driver 580+. Con la segunda GPU mostrará DOS.',
  },

  cuda: {
    why: 'CUDA es el \'idioma\' para hablar con la GPU NVIDIA. RTX 5090 (Blackwell, sm_120) necesita CUDA 12.8+. Versiones anteriores NO la reconocen.',
    alternative: '¿Por qué 12.8? Porque sm_120 solo existe desde CUDA 12.8.',
    commands: [
      { command: "nvcc --version 2>/dev/null || echo 'CUDA no instalado'", description: 'Verificar si ya está instalado' },
      { command: 'wget https://developer.download.nvidia.com/compute/cuda/repos/wsl-ubuntu/x86_64/cuda-keyring_1.1-1_all.deb', description: 'Descargar keyring' },
      { command: 'sudo dpkg -i cuda-keyring_1.1-1_all.deb', description: 'Instalar keyring' },
      { command: 'sudo apt-get update', description: 'Actualizar repos' },
      { command: 'sudo apt-get -y install cuda-toolkit-12-8', description: 'Instalar CUDA 12.8' },
      { command: "echo 'export PATH=/usr/local/cuda-12.8/bin:$PATH' >> ~/.bashrc && echo 'export LD_LIBRARY_PATH=/usr/local/cuda-12.8/lib64:$LD_LIBRARY_PATH' >> ~/.bashrc && source ~/.bashrc", description: 'Configurar PATH' },
      { command: 'nvcc --version', description: 'Verificar instalación' },
    ],
    successCriteria: "'Cuda compilation tools, release 12.8' o superior.",
  },

  ollama: {
    why: 'Ollama: punto de entrada más simple. Detecta GPUs automáticamente, distribuye entre múltiples GPUs, API compatible OpenAI.',
    alternative: 'Ollama es plug-and-play. vLLM es más potente pero más complejo. Estrategia: validar con Ollama, optimizar con vLLM.',
    commands: [
      { command: 'curl -fsSL https://ollama.com/install.sh | sh', description: 'Instalar Ollama' },
      { command: 'ollama --version', description: 'Verificar instalación' },
      { command: 'ollama serve &', description: 'Iniciar servicio' },
      { command: 'curl http://localhost:11434/api/tags', description: 'Verificar API' },
    ],
    successCriteria: 'Ollama respondiendo en localhost:11434.',
  },

  'model-download': {
    why: 'Modelos de 20-45 GB. Descargarlos ahora = no esperar horas cuando llegue el hardware.',
    alternative: 'Qwen 2.5 72B: mejor modelo open-source para SQL y análisis de datos. DeepSeek-R1 para razonamiento. Con 64 GB VRAM el 72B Q4_K_M cabe completo.',
    commands: [
      { command: 'ollama pull qwen2.5:72b-instruct-q4_K_M', description: 'Qwen 2.5 72B (~42 GB) — MODELO PRINCIPAL' },
      { command: 'ollama pull deepseek-r1:70b', description: 'DeepSeek-R1 70B (~42 GB) — Razonamiento' },
      { command: 'ollama pull qwen2.5-coder:32b-instruct-q8_0', description: 'Qwen Coder 32B (~34 GB) — Código/SQL' },
      { command: 'ollama list', description: 'Verificar modelos' },
      { command: 'ollama run qwen2.5:72b-instruct-q4_K_M "Hola, ¿cuánto es 2+2?"', description: 'Test rápido' },
    ],
    successCriteria: 'Modelos en \'ollama list\'. 1 GPU: ~12-15 t/s. 2 GPUs: ~25-30 t/s.',
  },

  vllm: {
    why: 'vLLM: framework de producción con tensor parallelism nativo. Hasta 35x más throughput que llama.cpp bajo carga concurrente.',
    alternative: 'vLLM vs TensorRT-LLM: más fácil, API OpenAI lista, diferencia <15%. TensorRT solo vale para enterprise.',
    commands: [
      { command: 'pip install --pre torch torchvision torchaudio --index-url https://download.pytorch.org/whl/nightly/cu128', description: 'PyTorch nightly (OBLIGATORIO para sm_120)' },
      { command: `python -c "import torch; print(f'PyTorch: {torch.__version__}'); print(f'CUDA: {torch.version.cuda}'); print(f'GPUs: {torch.cuda.device_count()}')"`, description: 'Verificar PyTorch' },
      { command: 'pip install vllm', description: 'Instalar vLLM (v0.11.0+)' },
      { command: `python -c "import vllm; print(f'vLLM: {vllm.__version__}')"`, description: 'Verificar vLLM' },
    ],
    successCriteria: 'PyTorch detecta GPU, CUDA 12.8+, vLLM sin errores.',
  },

  openwebui: {
    why: 'Interfaz tipo ChatGPT para tus modelos locales. Los socios pueden usar IA sin interfaz técnica.',
    alternative: 'Open WebUI es web, multi-usuario, se conecta a Ollama nativamente. LM Studio es desktop mono-usuario.',
    commands: [
      { command: 'sudo apt-get install -y docker.io', description: 'Instalar Docker' },
      { command: 'sudo usermod -aG docker $USER && newgrp docker', description: 'Permisos Docker' },
      { command: 'docker run -d -p 3000:8080 --add-host=host.docker.internal:host-gateway -v open-webui:/app/backend/data --name open-webui --restart always ghcr.io/open-webui/open-webui:main', description: 'Lanzar Open WebUI' },
      { command: 'docker ps | grep open-webui', description: 'Verificar' },
    ],
    successCriteria: 'http://localhost:3000 muestra la interfaz.',
  },

  monitoring: {
    why: 'Dos GPUs = ~1,300W de calor. Monitoreo = supervivencia. Temperatura, VRAM, energía, throttling.',
    alternative: 'nvidia-smi es oficial, ya instalada. nvtop es el complemento visual.',
    commands: [
      { command: 'sudo apt-get install -y nvtop htop', description: 'Instalar monitoreo' },
      { command: 'watch -n 1 nvidia-smi', description: 'Monitoreo tiempo real' },
      { command: 'nvidia-smi --query-gpu=index,name,temperature.gpu,utilization.gpu,memory.used,memory.total,power.draw --format=csv -l 5', description: 'CSV detallado cada 5 seg' },
      { command: 'nvtop', description: 'Monitor visual (htop para GPUs)' },
    ],
    successCriteria: 'Temperatura, VRAM y consumo visibles. Con 2 GPUs mostrará ambas.',
  },

  'dual-gpu': {
    why: 'Momento de la verdad. Verificar que el sistema reconoce ambas GPUs y pueden comunicarse.',
    alternative: 'Verificación por capas: hardware (nvidia-smi) → CUDA (torch) → framework (Ollama).',
    commands: [
      { command: 'nvidia-smi', description: 'PRIMER TEST: Debe mostrar DOS GPUs' },
      { command: 'nvidia-smi topo -m', description: 'Topología de conexión PCIe' },
      { command: `python -c "import torch; print(f'GPUs: {torch.cuda.device_count()}'); [print(f'  GPU {i}: {torch.cuda.get_device_name(i)}') for i in range(torch.cuda.device_count())]"`, description: 'Detección en PyTorch' },
      { command: 'OLLAMA_NUM_GPU=999 ollama run qwen2.5:72b-instruct-q4_K_M "Describí brevemente qué es Uruguay"', description: 'Test con ambas GPUs' },
      { command: 'nvidia-smi', description: 'Verificar VRAM en AMBAS GPUs' },
    ],
    successCriteria: '2x RTX 5090 detectadas. PyTorch ve 2 GPUs. Ollama usa VRAM de ambas.',
  },

  thermal: {
    why: '~1,150-1,300W de calor. Sin test térmico arriesgás throttling o daño al hardware.',
    alternative: '30 minutos porque los problemas térmicos no aparecen en 5 min. Si sobrevive 30 min, sobrevive producción.',
    commands: [
      { command: '# Terminal 1: Monitoreo', description: 'Abrir terminal de monitoreo' },
      { command: "watch -n 2 'nvidia-smi --query-gpu=index,temperature.gpu,power.draw,clocks.sm --format=csv,noheader'", description: 'Temperatura en tiempo real' },
      { command: '# Terminal 2: Carga sostenida', description: 'Abrir segunda terminal' },
      { command: 'ollama run qwen2.5:72b-instruct-q4_K_M "Escribí un análisis de 2000 palabras sobre la economía uruguaya, sectores productivos, sistema financiero, Mercosur y perspectivas 2026"', description: 'Generar texto largo' },
      { command: '# Verificar después de 30 min:', description: 'Verificación final' },
      { command: 'nvidia-smi -q -d TEMPERATURE,PERFORMANCE', description: 'Estado térmico final' },
    ],
    successCriteria: '<83°C estable = OK. >85°C = mejorar refrigeración. P0 = máximo rendimiento. P2+ = throttling.',
  },

  integration: {
    why: 'Objetivo final: CFO Inteligente con IA local. Ollama expone API compatible OpenAI, cambio mínimo.',
    alternative: 'Tu sistema ya usa estructura API. Solo redirigir las llamadas.',
    commands: [
      { command: '# Verificar API Ollama:', description: 'Pre-verificación' },
      { command: `curl http://localhost:11434/v1/chat/completions -H 'Content-Type: application/json' -d '{"model": "qwen2.5:72b-instruct-q4_K_M", "messages": [{"role": "user", "content": "¿Cuánto es 2+2?"}]}'`, description: 'Test API compatible OpenAI' },
      { command: '# Cambiar en configuración de CFO Inteligente:', description: 'Integración' },
      { command: '# ANTHROPIC_API_KEY → ya no se usa\n# OLLAMA_BASE_URL=http://localhost:11434\n# OLLAMA_MODEL=qwen2.5:72b-instruct-q4_K_M', description: 'Variables de entorno nuevas' },
    ],
    successCriteria: 'CFO Inteligente responde con modelo local. Latencia <3 seg.',
  },
};
