// whatsapp-bridge/server.js - Multi-Instance Support
const express = require('express');
const { Client, LocalAuth, MessageMedia } = require('whatsapp-web.js');
const qrcode = require('qrcode');
const cors = require('cors');
const fs = require('fs');
const path = require('path');

const app = express();
const PORT = process.env.PORT || 3001;
const API_KEY = process.env.WA_BRIDGE_API_KEY || 'dev-secret';

app.use(express.json());
app.use(cors());

// Multi-instance storage
const clients = new Map(); // token -> client instance
const clientStates = new Map(); // token -> {isReady, qrString, clientInfo}

// Ensure sessions directory exists
const sessionsDir = './whatsapp-sessions';
if (!fs.existsSync(sessionsDir)) {
  fs.mkdirSync(sessionsDir, { recursive: true });
}

// API Key middleware
const authenticateApiKey = (req, res, next) => {
  const apiKey = req.headers['x-api-key'];
  if (apiKey !== API_KEY) {
    return res.status(401).json({ error: 'Invalid API key' });
  }
  next();
};

// Token extraction middleware
const extractToken = (req, res, next) => {
  // Try to get token from header first, then query parameter
  const token = req.headers['x-instance-token'] || req.query.token || req.body.token;
  
  if (!token) {
    return res.status(400).json({ 
      error: 'Instance token required. Provide via x-instance-token header or token parameter' 
    });
  }
  
  // Validate token format (alphanumeric + dash/underscore)
  if (!/^[a-zA-Z0-9_-]+$/.test(token)) {
    return res.status(400).json({ 
      error: 'Invalid token format. Use alphanumeric characters, dashes, and underscores only' 
    });
  }
  
  req.instanceToken = token;
  next();
};

// Apply middlewares
app.use(authenticateApiKey);

// Initialize WhatsApp Client for specific token
function initializeClient(token) {
  console.log(`Initializing WhatsApp client for token: ${token}`);
  
  // Initialize client state if not exists
  if (!clientStates.has(token)) {
    clientStates.set(token, {
      isReady: false,
      qrString: null,
      clientInfo: null
    });
  }
  
  const client = new Client({
    authStrategy: new LocalAuth({
      dataPath: path.join(sessionsDir, token),
      clientId: token
    }),
    puppeteer: {
      headless: true,
      args: [
        '--no-sandbox',
        '--disable-setuid-sandbox',
        '--disable-dev-shm-usage',
        '--disable-accelerated-2d-canvas',
        '--no-first-run',
        '--no-zygote',
        '--single-process',
        '--disable-gpu'
      ]
    }
  });

  const state = clientStates.get(token);

  client.on('qr', async (qr) => {
    console.log(`QR Code generated for token: ${token}`);
    try {
      const qrDataURL = await qrcode.toDataURL(qr);
      state.qrString = qrDataURL;
      console.log(`QR code ready for token: ${token}`);
    } catch (error) {
      console.error(`Error generating QR code for ${token}:`, error);
      state.qrString = qr; // Fallback to raw QR string
    }
  });

  client.on('ready', async () => {
    console.log(`WhatsApp client ready for token: ${token}`);
    state.isReady = true;
    state.qrString = null; // Clear QR code when ready
    
    try {
      state.clientInfo = await client.info;
      console.log(`${token} connected as ${state.clientInfo.pushname} (${state.clientInfo.wid.user})`);
    } catch (error) {
      console.error(`Error getting client info for ${token}:`, error);
    }
  });

  client.on('authenticated', () => {
    console.log(`WhatsApp client authenticated for token: ${token}`);
  });

  client.on('auth_failure', (msg) => {
    console.error(`Authentication failure for ${token}:`, msg);
    state.isReady = false;
    state.qrString = null;
  });

  client.on('disconnected', (reason) => {
    console.log(`WhatsApp client disconnected for ${token}:`, reason);
    state.isReady = false;
    state.clientInfo = null;
    
    // Clean up client from memory
    clients.delete(token);
  });

  client.on('message', async (message) => {
    // Log incoming messages for debugging
    console.log(`[${token}] Received message from ${message.from}: ${message.body}`);
  });

  // Store client instance
  clients.set(token, client);
  
  // Initialize the client
  client.initialize();
  
  return client;
}

// Helper function to get client and state
function getClientAndState(token) {
  const client = clients.get(token);
  const state = clientStates.get(token);
  return { client, state };
}

// Routes

// Health check (no token required)
app.get('/health', (req, res) => {
  const totalInstances = clients.size;
  const readyInstances = Array.from(clientStates.values()).filter(state => state.isReady).length;
  
  res.json({
    server: 'running',
    timestamp: new Date().toISOString(),
    instances: {
      total: totalInstances,
      ready: readyInstances,
      tokens: Array.from(clients.keys())
    }
  });
});

// Initialize new instance
app.post('/init', extractToken, (req, res) => {
  const token = req.instanceToken;
  
  if (clients.has(token)) {
    const state = clientStates.get(token);
    return res.json({
      success: true,
      message: 'Instance already exists',
      token: token,
      status: state.isReady ? 'connected' : (state.qrString ? 'waiting_for_scan' : 'initializing')
    });
  }
  
  try {
    initializeClient(token);
    res.json({
      success: true,
      message: 'WhatsApp instance initializing',
      token: token,
      status: 'initializing'
    });
  } catch (error) {
    console.error(`Error initializing client for ${token}:`, error);
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

// Get instance status
app.get('/status', extractToken, (req, res) => {
  const token = req.instanceToken;
  const { client, state } = getClientAndState(token);
  
  if (!client || !state) {
    return res.json({
      token: token,
      ready: false,
      hasQr: false,
      status: 'not_initialized',
      message: 'Instance not found. Call /init first.'
    });
  }
  
  res.json({
    token: token,
    ready: state.isReady,
    hasQr: !!state.qrString,
    timestamp: new Date().toISOString(),
    status: state.isReady ? 'connected' : (state.qrString ? 'waiting_for_scan' : 'initializing')
  });
});

// Get QR code
app.get('/qr', extractToken, (req, res) => {
  const token = req.instanceToken;
  const { client, state } = getClientAndState(token);
  
  if (!client || !state) {
    return res.status(404).json({
      qr: null,
      status: 'not_initialized',
      message: 'Instance not found. Call /init first.'
    });
  }
  
  if (state.isReady) {
    res.json({
      qr: null,
      status: 'already_connected',
      message: 'WhatsApp is already connected'
    });
  } else if (state.qrString) {
    res.json({
      qr: state.qrString,
      status: 'qr_ready',
      message: 'Scan QR code with WhatsApp mobile app'
    });
  } else {
    res.json({
      qr: null,
      status: 'initializing',
      message: 'QR code not ready yet, please wait'
    });
  }
});

// Check if number is registered on WhatsApp
app.get('/number-id/:number', extractToken, async (req, res) => {
  const token = req.instanceToken;
  const { client, state } = getClientAndState(token);
  
  if (!client || !state || !state.isReady) {
    return res.status(503).json({ 
      registered: false, 
      error: 'WhatsApp client not ready',
      token: token
    });
  }

  try {
    const { number } = req.params;
    const numberId = await client.getNumberId(number);
    
    res.json({
      registered: !!numberId,
      number: number,
      numberId: numberId ? numberId._serialized : null,
      token: token
    });
  } catch (error) {
    console.error(`Error checking number for ${token}:`, error);
    res.status(500).json({
      registered: false,
      error: error.message,
      token: token
    });
  }
});

// Send message
app.post('/send', extractToken, async (req, res) => {
  const token = req.instanceToken;
  const { client, state } = getClientAndState(token);
  
  if (!client || !state || !state.isReady) {
    return res.status(503).json({ 
      success: false, 
      error: 'WhatsApp client not ready',
      token: token
    });
  }

  try {
    const { number, message } = req.body;

    if (!number || !message) {
      return res.status(400).json({
        success: false,
        error: 'Number and message are required'
      });
    }

    // Format number for WhatsApp
    const formattedNumber = number.includes('@') ? number : `${number}@c.us`;
    
    // Send message
    const sentMessage = await client.sendMessage(formattedNumber, message);
    
    res.json({
      success: true,
      messageId: sentMessage.id._serialized,
      timestamp: sentMessage.timestamp,
      to: formattedNumber,
      token: token
    });
    
    console.log(`[${token}] Message sent to ${formattedNumber}: ${message}`);
  } catch (error) {
    console.error(`Error sending message for ${token}:`, error);
    res.status(500).json({
      success: false,
      error: error.message,
      token: token
    });
  }
});

// Get client info
app.get('/info', extractToken, async (req, res) => {
  const token = req.instanceToken;
  const { client, state } = getClientAndState(token);
  
  if (!client || !state || !state.isReady) {
    return res.status(503).json({ 
      ready: false, 
      error: 'WhatsApp client not ready',
      token: token
    });
  }

  try {
    const info = await client.info;
    res.json({
      ready: true,
      token: token,
      info: {
        pushname: info.pushname,
        phone: info.wid.user,
        platform: info.platform,
        battery: info.battery,
        plugged: info.plugged
      }
    });
  } catch (error) {
    console.error(`Error getting client info for ${token}:`, error);
    res.status(500).json({
      ready: false,
      error: error.message,
      token: token
    });
  }
});

// Logout/Disconnect specific instance
app.post('/logout', extractToken, async (req, res) => {
  const token = req.instanceToken;
  const { client, state } = getClientAndState(token);
  
  try {
    if (client) {
      await client.logout();
      clients.delete(token);
    }
    
    if (state) {
      state.isReady = false;
      state.clientInfo = null;
      state.qrString = null;
    }
    
    res.json({
      success: true,
      message: 'Logged out successfully',
      token: token
    });
  } catch (error) {
    console.error(`Error logging out ${token}:`, error);
    res.status(500).json({
      success: false,
      error: error.message,
      token: token
    });
  }
});

// Restart specific instance
app.post('/restart', extractToken, async (req, res) => {
  const token = req.instanceToken;
  const { client, state } = getClientAndState(token);
  
  try {
    if (client) {
      await client.destroy();
      clients.delete(token);
    }
    
    if (state) {
      state.isReady = false;
      state.clientInfo = null;
      state.qrString = null;
    }
    
    // Reinitialize after a short delay
    setTimeout(() => {
      initializeClient(token);
    }, 1000);
    
    res.json({
      success: true,
      message: 'Restarting WhatsApp instance',
      token: token
    });
  } catch (error) {
    console.error(`Error restarting ${token}:`, error);
    res.status(500).json({
      success: false,
      error: error.message,
      token: token
    });
  }
});

// List all instances
app.get('/instances', (req, res) => {
  const instances = Array.from(clients.keys()).map(token => {
    const state = clientStates.get(token);
    return {
      token: token,
      ready: state ? state.isReady : false,
      hasQr: state ? !!state.qrString : false,
      status: state ? (state.isReady ? 'connected' : (state.qrString ? 'waiting_for_scan' : 'initializing')) : 'unknown'
    };
  });
  
  res.json({
    total: instances.length,
    instances: instances
  });
});

// Delete instance (logout and remove)
app.delete('/instance', extractToken, async (req, res) => {
  const token = req.instanceToken;
  const { client, state } = getClientAndState(token);
  
  try {
    if (client) {
      await client.destroy();
      clients.delete(token);
    }
    
    clientStates.delete(token);
    
    // Optionally remove session files
    const sessionPath = path.join(sessionsDir, token);
    if (fs.existsSync(sessionPath)) {
      fs.rmSync(sessionPath, { recursive: true, force: true });
    }
    
    res.json({
      success: true,
      message: 'Instance deleted successfully',
      token: token
    });
  } catch (error) {
    console.error(`Error deleting instance ${token}:`, error);
    res.status(500).json({
      success: false,
      error: error.message,
      token: token
    });
  }
});

// Error handling middleware
app.use((error, req, res, next) => {
  console.error('Express error:', error);
  res.status(500).json({
    success: false,
    error: 'Internal server error'
  });
});

// 404 handler
app.use((req, res) => {
  res.status(404).json({
    success: false,
    error: 'Endpoint not found'
  });
});

// Start server
app.listen(PORT, () => {
  console.log(`Multi-Instance WhatsApp Bridge Server running on port ${PORT}`);
  console.log(`API Key: ${API_KEY}`);
  console.log(`Sessions directory: ${path.resolve(sessionsDir)}`);
  console.log(`\nExample usage:`);
  console.log(`  Initialize: POST /init with x-instance-token: school1`);
  console.log(`  Get QR: GET /qr with x-instance-token: school1`);
  console.log(`  Send: POST /send with x-instance-token: school1`);
});

// Graceful shutdown
const gracefulShutdown = async () => {
  console.log('Shutting down Multi-Instance WhatsApp Bridge...');
  
  const shutdownPromises = Array.from(clients.values()).map(async (client) => {
    try {
      await client.destroy();
    } catch (error) {
      console.error('Error during client shutdown:', error);
    }
  });
  
  await Promise.all(shutdownPromises);
  console.log('All WhatsApp clients disconnected.');
  process.exit(0);
};

process.on('SIGINT', gracefulShutdown);
process.on('SIGTERM', gracefulShutdown);