const express = require('express');
const fs = require('fs');
const path = require('path');
const app = express();

const PORT = process.env.PORT || 3000;
const DATA_DIR = '/tmp/roblox_data';
const ACTIVITY_LOG_FILE = path.join(DATA_DIR, 'activity_log.json');
const STATE_FILE = path.join(DATA_DIR, 'state.json');

// Criar diretório de dados se não existir
if (!fs.existsSync(DATA_DIR)) {
  fs.mkdirSync(DATA_DIR, { recursive: true });
}

// Middleware
app.use(express.json());
app.use(express.static('public'));

// Função para ler o log de atividades
function readActivityLog() {
  try {
    if (fs.existsSync(ACTIVITY_LOG_FILE)) {
      const data = fs.readFileSync(ACTIVITY_LOG_FILE, 'utf-8');
      return JSON.parse(data);
    }
  } catch (error) {
    console.error('Erro ao ler log:', error);
  }
  return [];
}

// Função para salvar log de atividades
function saveActivityLog(logs) {
  try {
    fs.writeFileSync(ACTIVITY_LOG_FILE, JSON.stringify(logs, null, 2));
  } catch (error) {
    console.error('Erro ao salvar log:', error);
  }
}

// Função para ler estado atual
function readState() {
  try {
    if (fs.existsSync(STATE_FILE)) {
      const data = fs.readFileSync(STATE_FILE, 'utf-8');
      return JSON.parse(data);
    }
  } catch (error) {
    console.error('Erro ao ler estado:', error);
  }
  return { presence_type: 0, last_update: new Date().toISOString() };
}

// Função para salvar estado
function saveState(state) {
  try {
    fs.writeFileSync(STATE_FILE, JSON.stringify(state, null, 2));
  } catch (error) {
    console.error('Erro ao salvar estado:', error);
  }
}

// API: Obter status atual
app.get('/api/status', (req, res) => {
  const state = readState();
  const statusMap = {
    0: 'Offline',
    1: 'Online',
    2: 'No Jogo',
    3: 'No Studio'
  };
  
  res.json({
    status: statusMap[state.presence_type] || 'Desconhecido',
    last_update: state.last_update
  });
});

// API: Obter histórico de atividades
app.get('/api/activity-log', (req, res) => {
  const logs = readActivityLog();
  res.json(logs);
});

// API: Adicionar evento de atividade (chamado pelo script Python)
app.post('/api/activity-log', (req, res) => {
  try {
    const { data_hora, evento, status } = req.body;
    
    if (!data_hora || !evento || !status) {
      return res.status(400).json({ error: 'Dados incompletos' });
    }

    const logs = readActivityLog();
    logs.push({ data_hora, evento, status });
    saveActivityLog(logs);

    res.json({ success: true, message: 'Evento registrado' });
  } catch (error) {
    console.error('Erro ao adicionar evento:', error);
    res.status(500).json({ error: 'Erro ao registrar evento' });
  }
});

// API: Atualizar estado (chamado pelo script Python)
app.post('/api/status', (req, res) => {
  try {
    const { presence_type } = req.body;
    
    if (presence_type === undefined) {
      return res.status(400).json({ error: 'presence_type é obrigatório' });
    }

    const state = {
      presence_type: parseInt(presence_type),
      last_update: new Date().toISOString()
    };

    saveState(state);
    res.json({ success: true, message: 'Estado atualizado' });
  } catch (error) {
    console.error('Erro ao atualizar estado:', error);
    res.status(500).json({ error: 'Erro ao atualizar estado' });
  }
});

// Servir HTML
app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

// Health check
app.get('/health', (req, res) => {
  res.json({ status: 'ok', timestamp: new Date().toISOString() });
});

// Iniciar servidor
app.listen(PORT, () => {
  console.log(`Servidor rodando em http://localhost:${PORT}` );
  console.log(`Health check: http://localhost:${PORT}/health` );
});
