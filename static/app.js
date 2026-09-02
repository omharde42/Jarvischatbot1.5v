// JARVIS AI Assistant Frontend Client Logic

let isListening = false;
let currentPendingToken = null;
let recognition = null;
let synth = window.speechSynthesis;

// DOM Elements
const micBtn = document.getElementById('micBtn');
const stateIndicator = document.querySelector('.state-indicator');
const stateLabel = document.getElementById('stateLabel');
const commandForm = document.getElementById('commandForm');
const commandInput = document.getElementById('commandInput');
const conversationContainer = document.getElementById('conversationContainer');
const activityLog = document.getElementById('activityLog');
const confirmModal = document.getElementById('confirmModal');
const modalPromptText = document.getElementById('modalPromptText');
const cancelModalBtn = document.getElementById('cancelModalBtn');
const confirmModalBtn = document.getElementById('confirmModalBtn');

// Telemetry Elements
const cpuValue = document.getElementById('cpuValue');
const cpuBar = document.getElementById('cpuBar');
const ramValue = document.getElementById('ramValue');
const ramBar = document.getElementById('ramBar');
const diskValue = document.getElementById('diskValue');
const diskBar = document.getElementById('diskBar');
const uptimeValue = document.getElementById('uptimeValue');
const topProcInfo = document.getElementById('topProcInfo');

// Canvas Waveform Animation
const canvas = document.getElementById('waveformCanvas');
const ctx = canvas.getContext('2d');
let animationFrameId;

function drawWaveform(state = 'idle') {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.beginPath();
  ctx.lineWidth = 2;

  if (state === 'listening' || state === 'speaking') {
    ctx.strokeStyle = state === 'listening' ? '#00f0ff' : '#00ff88';
    const time = Date.now() * 0.005;
    for (let x = 0; x < canvas.width; x++) {
      const y = canvas.height / 2 + Math.sin(x * 0.05 + time) * 15 * Math.cos(x * 0.02 + time);
      if (x === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    }
  } else {
    ctx.strokeStyle = '#2a364f';
    ctx.moveTo(0, canvas.height / 2);
    ctx.lineTo(canvas.width, canvas.height / 2);
  }
  ctx.stroke();
  animationFrameId = requestAnimationFrame(() => drawWaveform(state));
}

function setJARVISState(state) {
  // States: IDLE, LISTENING, THINKING, EXECUTING, SPEAKING
  const upperState = state.toUpperCase();
  stateLabel.textContent = upperState;

  stateIndicator.className = 'state-indicator ' + state.toLowerCase();

  if (state.toLowerCase() === 'listening') {
    micBtn.classList.add('active');
  } else {
    micBtn.classList.remove('active');
  }

  cancelAnimationFrame(animationFrameId);
  drawWaveform(state.toLowerCase());
  logActivity(`State changed to ${upperState}`);
}

function logActivity(message) {
  const timeStr = new Date().toLocaleTimeString();
  const entry = document.createElement('div');
  entry.className = 'log-entry';

  const timeSpan = document.createElement('span');
  timeSpan.className = 'log-time';
  timeSpan.textContent = `[${timeStr}]`;

  const msgSpan = document.createElement('span');
  msgSpan.className = 'log-msg';
  msgSpan.textContent = message;

  entry.appendChild(timeSpan);
  entry.appendChild(document.createTextNode(' '));
  entry.appendChild(msgSpan);

  activityLog.appendChild(entry);
  activityLog.scrollTop = activityLog.scrollHeight;
}

function addChatMessage(speaker, text) {
  const bubble = document.createElement('div');
  bubble.className = `chat-bubble ${speaker.toLowerCase()}`;

  const speakerDiv = document.createElement('div');
  speakerDiv.className = 'speaker';
  speakerDiv.textContent = speaker.toUpperCase();

  const textDiv = document.createElement('div');
  textDiv.className = 'text';
  textDiv.textContent = text;

  bubble.appendChild(speakerDiv);
  bubble.appendChild(textDiv);

  conversationContainer.appendChild(bubble);
  conversationContainer.scrollTop = conversationContainer.scrollHeight;
}

function speakText(text) {
  if (!synth) return;
  synth.cancel(); // Stop current speech
  const utterance = new SpeechSynthesisUtterance(text);

  utterance.onstart = () => {
    setJARVISState('SPEAKING');
  };

  utterance.onend = () => {
    setJARVISState('IDLE');
  };

  utterance.onerror = () => {
    setJARVISState('IDLE');
  };

  synth.speak(utterance);
}

// Web Speech API STT Setup
function setupSpeechRecognition() {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) {
    logActivity('Web Speech API not supported in this browser.');
    return;
  }

  recognition = new SpeechRecognition();
  recognition.continuous = false;
  recognition.interimResults = false;
  recognition.lang = 'en-US';

  recognition.onstart = () => {
    isListening = true;
    setJARVISState('LISTENING');
    logActivity('Voice listening started');
  };

  recognition.onresult = (event) => {
    const transcript = event.results[0][0].transcript;
    logActivity(`Voice recognized: "${transcript}"`);
    commandInput.value = transcript;
    processUserCommand(transcript);
  };

  recognition.onerror = (event) => {
    logActivity(`Speech recognition error: ${event.error}`);
    setJARVISState('IDLE');
    isListening = false;
  };

  recognition.onend = () => {
    isListening = false;
    if (stateLabel.textContent === 'LISTENING') {
      setJARVISState('IDLE');
    }
  };
}

function toggleListening() {
  if (!recognition) {
    setupSpeechRecognition();
  }

  if (!recognition) {
    alert('Web Speech API is not supported in this browser.');
    return;
  }

  if (isListening) {
    recognition.stop();
  } else {
    recognition.start();
  }
}

// Telemetry Polling
async function updateTelemetry() {
  try {
    const response = await fetch('/api/status');
    const data = await response.json();
    if (data.telemetry) {
      const t = data.telemetry;
      cpuValue.textContent = `${t.cpu_percent}%`;
      cpuBar.style.width = `${t.cpu_percent}%`;

      ramValue.textContent = `${t.memory_percent}%`;
      ramBar.style.width = `${t.memory_percent}%`;

      diskValue.textContent = `${t.disk_percent}%`;
      diskBar.style.width = `${t.disk_percent}%`;

      uptimeValue.textContent = t.uptime;

      if (t.top_processes && t.top_processes.length > 0) {
        const top = t.top_processes[0];
        topProcInfo.textContent = `${top.name || 'Process'} (PID: ${top.pid || 'N/A'}) - CPU: ${top.cpu_percent || 0}%`;
      }
    }
  } catch (err) {
    // Silent fail on polling error
  }
}

// Process Command Submission
async function processUserCommand(commandText) {
  if (!commandText.trim()) return;

  addChatMessage('user', commandText);
  commandInput.value = '';
  setJARVISState('THINKING');
  logActivity(`Executing command: "${commandText}"`);

  try {
    setJARVISState('EXECUTING');
    const response = await fetch('/api/execute', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ command: commandText })
    });

    const data = await response.json();

    if (data.requires_confirmation) {
      currentPendingToken = data.confirmation_token;
      modalPromptText.textContent = data.prompt;
      confirmModal.classList.remove('hidden');
      setJARVISState('IDLE');
      if (data.spoken_response) speakText(data.spoken_response);
      return;
    }

    const spokenText = data.spoken_response || (data.success ? 'Action executed.' : 'Failed to execute command.');
    addChatMessage('jarvis', spokenText);
    speakText(spokenText);

  } catch (err) {
    logActivity(`Error executing command: ${err.message}`);
    const errorMsg = 'An error occurred while connecting to the server.';
    addChatMessage('jarvis', errorMsg);
    speakText(errorMsg);
  }
}

// Confirmation Handler
async function handleConfirmation(confirmed) {
  confirmModal.classList.add('hidden');
  if (!currentPendingToken) return;

  setJARVISState('EXECUTING');
  logActivity(`Sending confirmation choice (${confirmed}) for token ${currentPendingToken}`);

  try {
    const response = await fetch('/api/confirm', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        confirmation_token: currentPendingToken,
        confirmed: confirmed
      })
    });

    const data = await response.json();
    currentPendingToken = null;

    const spokenText = data.spoken_response || (data.success ? 'Action confirmed and executed.' : 'Action canceled.');
    addChatMessage('jarvis', spokenText);
    speakText(spokenText);

  } catch (err) {
    logActivity(`Confirmation error: ${err.message}`);
    setJARVISState('IDLE');
  }
}

// Event Listeners
micBtn.addEventListener('click', toggleListening);

commandForm.addEventListener('submit', (e) => {
  e.preventDefault();
  processUserCommand(commandInput.value);
});

cancelModalBtn.addEventListener('click', () => handleConfirmation(false));
confirmModalBtn.addEventListener('click', () => handleConfirmation(true));

// Initialization
document.addEventListener('DOMContentLoaded', () => {
  setupSpeechRecognition();
  drawWaveform('idle');
  updateTelemetry();
  setInterval(updateTelemetry, 3000);
});
