# Omni Electron - Self-Improving AI Assistant

A desktop application built with Electron + Vue 3 + Python that can autonomously improve its own code.

## 🚀 Quick Start

### Prerequisites

- Node.js 18+ and npm
- Python 3.11+
- Linux (primary target), also works on Windows/macOS

### Installation

1. **Clone and install dependencies:**

```bash
cd omni-electron
npm install
```

2. **Setup Python backend:**

```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. **Configure environment:**

```bash
cp .env.example .env
# Edit .env with your LLM API keys
```

4. **Run in development mode:**

```bash
npm run dev
```

This will:
- Start Vite dev server (http://localhost:5173)
- Launch Electron with hot-reload
- Spawn Python backend automatically

## 📁 Project Structure

```
omni-electron/
├── electron/
│   ├── main.js          # Main process - window management, Python spawning
│   └── preload.js       # Secure IPC bridge
├── src/
│   ├── App.vue          # Main Vue application
│   ├── components/
│   │   └── ChatPanel.vue
│   └── main.ts          # Entry point
├── backend/
│   ├── main.py          # JSON-RPC server
│   └── core/
│       ├── llm_client.py
│       ├── memory.py
│       └── embeddings.py
├── package.json
└── vite.config.js
```

## 🛠️ Development

### Running Tests

```bash
npm test
```

### Building for Production

```bash
# Build for current platform
npm run build

# Build for Linux specifically
npm run build:linux
```

Output will be in `dist-electron/`:
- `Omni-0.1.0.AppImage` - Portable Linux app
- `Omni-0.1.0.deb` - Debian/Ubuntu package

## 🧪 Week 1 Status

- [x] Electron project setup
- [x] Vue 3 + Vite frontend
- [x] Python backend with JSON-RPC
- [x] IPC communication bridge
- [x] Core modules copied from legacy Omni
- [ ] Test end-to-end chat flow
- [ ] Verify on Linux

## 🔮 Next Steps (Week 2)

- Self-modification engine
- Code AST parsing
- Hot-reload mechanism
- Multi-agent system

## 📝 License

MIT
