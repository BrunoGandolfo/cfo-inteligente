// Videos curados por componente/categoria
// - videoId: ID de YouTube (se puede agregar despues buscando en YouTube)
// - searchQuery: busqueda en YouTube (fallback cuando no hay videoId)
// - title, channel, lang: metadatos del video

export interface VideoEntry {
  videoId?: string;
  searchQuery: string;
  title: string;
  channel?: string;
  lang: 'es' | 'en';
}

export interface ComponentVideos {
  componentPattern: string; // regex pattern to match component id or name
  videos: VideoEntry[];
}

export const videoLibrary: ComponentVideos[] = [
  // ============================================================
  //  HARDWARE
  // ============================================================
  {
    componentPattern: 'gpu|rtx|5090|nvidia|geforce',
    videos: [
      {
        searchQuery: 'RTX 5090 review español análisis rendimiento',
        title: 'RTX 5090 — Analisis y rendimiento',
        lang: 'es',
      },
      {
        searchQuery: 'RTX 5090 deep learning AI benchmark VRAM 32GB',
        title: 'RTX 5090 para IA y Deep Learning',
        lang: 'en',
      },
      {
        searchQuery: 'qué es una tarjeta gráfica GPU explicado fácil español',
        title: 'Que es una GPU — explicado facil',
        lang: 'es',
      },
      {
        searchQuery: 'NVIDIA CUDA cores tensor cores explained',
        title: 'CUDA Cores vs Tensor Cores explicado',
        lang: 'en',
      },
    ],
  },
  {
    componentPattern: 'cpu|intel|core ultra|285k|arrow lake',
    videos: [
      {
        searchQuery: 'Intel Core Ultra 9 285K review español análisis',
        title: 'Intel Core Ultra 9 285K — Review',
        lang: 'es',
      },
      {
        searchQuery: 'CPU vs GPU para inteligencia artificial deep learning explicado',
        title: 'CPU vs GPU para IA — Cual importa mas?',
        lang: 'es',
      },
      {
        searchQuery: 'PCIe lanes explained GPU CPU bandwidth',
        title: 'Lanes PCIe explicados — ancho de banda GPU',
        lang: 'en',
      },
    ],
  },
  {
    componentPattern: 'ram|ddr5|memoria',
    videos: [
      {
        searchQuery: 'DDR5 vs DDR4 diferencias explicado español',
        title: 'DDR5 vs DDR4 — Diferencias y ventajas',
        lang: 'es',
      },
      {
        searchQuery: 'cuánta RAM necesito para inteligencia artificial modelos LLM',
        title: 'Cuanta RAM necesitas para IA local?',
        lang: 'es',
      },
      {
        searchQuery: 'RAM vs VRAM difference deep learning explained',
        title: 'RAM vs VRAM — diferencia para Deep Learning',
        lang: 'en',
      },
    ],
  },
  {
    componentPattern: 'disk|nvme|ssd|m\\.2|almacenamiento',
    videos: [
      {
        searchQuery: 'NVMe SSD Gen5 vs Gen4 diferencias explicado español',
        title: 'NVMe Gen5 vs Gen4 — Diferencias reales',
        lang: 'es',
      },
      {
        searchQuery: 'SSD NVMe for AI models loading speed deep learning',
        title: 'NVMe para modelos de IA — importa la velocidad?',
        lang: 'en',
      },
    ],
  },
  {
    componentPattern: 'wsl|windows subsystem',
    videos: [
      {
        searchQuery: 'WSL2 tutorial español instalar configurar Windows',
        title: 'WSL2 — Tutorial de instalacion y configuracion',
        lang: 'es',
      },
      {
        searchQuery: 'WSL2 GPU passthrough NVIDIA CUDA setup tutorial',
        title: 'WSL2 + GPU NVIDIA — como funciona el passthrough',
        lang: 'en',
      },
    ],
  },
  {
    componentPattern: 'motherboard|z890|placa madre',
    videos: [
      {
        searchQuery: 'MSI MEG Z890 ACE review PCIe lanes dual GPU',
        title: 'MSI MEG Z890 ACE — Review',
        lang: 'en',
      },
      {
        searchQuery: 'qué es una placa madre motherboard explicado español para qué sirve',
        title: 'Que es una placa madre y por que importa',
        lang: 'es',
      },
    ],
  },
  {
    componentPattern: 'fuente|psu|seasonic|px-1600|poder',
    videos: [
      {
        searchQuery: 'fuente de poder ATX explicado español cuántos watts necesito',
        title: 'Fuentes de poder — cuantos watts necesitas?',
        lang: 'es',
      },
      {
        searchQuery: 'dual PSU setup gaming workstation how to',
        title: 'Setup dual fuente — como hacerlo',
        lang: 'en',
      },
    ],
  },
  {
    componentPattern: 'gabinete|corsair|9000d|case',
    videos: [
      {
        searchQuery: 'Corsair 9000D review español dual GPU airflow',
        title: 'Corsair 9000D — Gabinete para Dual GPU',
        lang: 'es',
      },
    ],
  },
  {
    componentPattern: 'ventilacion|cooling|ventilador',
    videos: [
      {
        searchQuery: 'refrigeración PC dual GPU airflow explicado español',
        title: 'Refrigeracion para Dual GPU — guia de airflow',
        lang: 'es',
      },
    ],
  },
  {
    componentPattern: 'add2psu|adaptador',
    videos: [
      {
        searchQuery: 'Add2PSU adapter dual power supply how to use',
        title: 'Add2PSU — Como sincronizar dos fuentes',
        lang: 'en',
      },
    ],
  },

  // ============================================================
  //  AI RUNTIME
  // ============================================================
  {
    componentPattern: 'cuda',
    videos: [
      {
        searchQuery: 'qué es CUDA NVIDIA explicado español para qué sirve',
        title: 'Que es CUDA y por que lo necesitas',
        lang: 'es',
      },
      {
        searchQuery: 'CUDA toolkit install WSL2 Ubuntu tutorial 2024 2025',
        title: 'Instalar CUDA Toolkit en WSL2/Ubuntu',
        lang: 'en',
      },
      {
        searchQuery: 'CUDA programming tutorial beginner freeCodeCamp',
        title: 'Curso completo de CUDA (freeCodeCamp)',
        lang: 'en',
      },
    ],
  },
  {
    componentPattern: 'cudnn',
    videos: [
      {
        searchQuery: 'cuDNN install tutorial CUDA deep learning what is',
        title: 'cuDNN — que es y como instalarlo',
        lang: 'en',
      },
    ],
  },
  {
    componentPattern: 'nv_container|nvidia container|container toolkit',
    videos: [
      {
        searchQuery: 'NVIDIA Container Toolkit Docker GPU tutorial setup',
        title: 'NVIDIA Container Toolkit — GPU en Docker',
        lang: 'en',
      },
    ],
  },

  // ============================================================
  //  AI FRAMEWORKS
  // ============================================================
  {
    componentPattern: 'pytorch',
    videos: [
      {
        searchQuery: 'PyTorch tutorial español introducción deep learning',
        title: 'PyTorch — Tutorial introductorio',
        lang: 'es',
      },
      {
        searchQuery: 'PyTorch GPU CUDA setup tutorial beginner 2024',
        title: 'PyTorch + CUDA GPU — setup para principiantes',
        lang: 'en',
      },
    ],
  },
  {
    componentPattern: 'tensorflow',
    videos: [
      {
        searchQuery: 'TensorFlow tutorial español introducción qué es',
        title: 'TensorFlow — Que es y para que sirve',
        lang: 'es',
      },
      {
        searchQuery: 'TensorFlow vs PyTorch comparison 2024 2025 which better',
        title: 'TensorFlow vs PyTorch — cual elegir?',
        lang: 'en',
      },
    ],
  },
  {
    componentPattern: 'transformers|hugging.?face',
    videos: [
      {
        searchQuery: 'HuggingFace Transformers tutorial español qué es',
        title: 'HuggingFace Transformers — que es y como usarlo',
        lang: 'es',
      },
      {
        searchQuery: 'Transformers library tutorial load model inference beginner',
        title: 'Transformers — cargar y usar modelos IA',
        lang: 'en',
      },
    ],
  },
  {
    componentPattern: 'vllm',
    videos: [
      {
        searchQuery: 'vLLM tutorial inference engine LLM serving explained',
        title: 'vLLM — Motor de inferencia de alto rendimiento',
        lang: 'en',
      },
      {
        searchQuery: 'vLLM vs Ollama vs llama.cpp comparison LLM inference',
        title: 'vLLM vs Ollama vs llama.cpp — comparativa',
        lang: 'en',
      },
    ],
  },
  {
    componentPattern: 'llama.?cpp',
    videos: [
      {
        searchQuery: 'llama.cpp tutorial how to use local LLM inference',
        title: 'llama.cpp — inferencia local de LLMs',
        lang: 'en',
      },
    ],
  },

  // ============================================================
  //  AI SERVERS
  // ============================================================
  {
    componentPattern: 'ollama',
    videos: [
      {
        searchQuery: 'Ollama tutorial español instalar usar modelos IA local',
        title: 'Ollama — Tu LLM privado en casa',
        lang: 'es',
      },
      {
        searchQuery: 'Ollama GPU setup multiple models tutorial',
        title: 'Ollama con GPU — configuracion y modelos',
        lang: 'en',
      },
    ],
  },
  {
    componentPattern: 'docker',
    videos: [
      {
        searchQuery: 'Docker tutorial español qué es para qué sirve introducción',
        title: 'Docker — Que es y por que lo necesitas',
        lang: 'es',
      },
      {
        searchQuery: 'Docker NVIDIA GPU container deep learning tutorial',
        title: 'Docker + GPU NVIDIA para Deep Learning',
        lang: 'en',
      },
    ],
  },

  // ============================================================
  //  DEV TOOLS
  // ============================================================
  {
    componentPattern: 'python|pip',
    videos: [
      {
        searchQuery: 'Python para inteligencia artificial tutorial español',
        title: 'Python para IA — por donde empezar',
        lang: 'es',
      },
    ],
  },
  {
    componentPattern: 'conda|mamba',
    videos: [
      {
        searchQuery: 'Conda tutorial español entornos virtuales Python',
        title: 'Conda — Manejar entornos de Python',
        lang: 'es',
      },
    ],
  },
  {
    componentPattern: 'node',
    videos: [
      {
        searchQuery: 'Node.js para qué sirve explicado español',
        title: 'Node.js — Para que sirve?',
        lang: 'es',
      },
    ],
  },
  {
    componentPattern: 'git(?!hub)',
    videos: [
      {
        searchQuery: 'Git tutorial español principiantes qué es',
        title: 'Git — Tutorial para principiantes',
        lang: 'es',
      },
    ],
  },
  {
    componentPattern: 'cmake',
    videos: [
      {
        searchQuery: 'CMake tutorial what is it for C++ build system',
        title: 'CMake — que es y para que sirve',
        lang: 'en',
      },
    ],
  },
  {
    componentPattern: 'gcc|g\\+\\+',
    videos: [
      {
        searchQuery: 'GCC compiler explained what is for Linux',
        title: 'GCC — compilador de C/C++ en Linux',
        lang: 'en',
      },
    ],
  },
  {
    componentPattern: 'hf_cli|huggingface cli',
    videos: [
      {
        searchQuery: 'HuggingFace CLI tutorial download models hub',
        title: 'HuggingFace CLI — descargar modelos de IA',
        lang: 'en',
      },
    ],
  },
  {
    componentPattern: 'jupyter',
    videos: [
      {
        searchQuery: 'Jupyter Notebook tutorial español qué es para qué sirve',
        title: 'Jupyter Notebook — Tutorial basico',
        lang: 'es',
      },
    ],
  },
];

// Find videos matching a component by id or name
export function findVideosForComponent(componentId: string, componentName: string): VideoEntry[] {
  const searchStr = `${componentId} ${componentName}`.toLowerCase();
  const matches: VideoEntry[] = [];

  for (const entry of videoLibrary) {
    const regex = new RegExp(entry.componentPattern, 'i');
    if (regex.test(searchStr)) {
      matches.push(...entry.videos);
    }
  }

  return matches;
}

// Build YouTube URL
export function getYouTubeUrl(video: VideoEntry): string {
  if (video.videoId) {
    return `https://www.youtube.com/watch?v=${video.videoId}`;
  }
  return `https://www.youtube.com/results?search_query=${encodeURIComponent(video.searchQuery)}`;
}

// Build thumbnail URL (only works with videoId)
export function getYouTubeThumbnail(video: VideoEntry): string | null {
  if (video.videoId) {
    return `https://img.youtube.com/vi/${video.videoId}/mqdefault.jpg`;
  }
  return null;
}
