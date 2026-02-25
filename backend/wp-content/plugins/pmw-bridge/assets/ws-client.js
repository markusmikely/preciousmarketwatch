/**
 * PMW Bridge — WebSocket client for Mission Control real-time updates
 * Connects to FastAPI bridge and receives: pipeline_update, agent_update,
 * alert, cost_update, intelligence_brief, heartbeat
 */
class PMWBridge {
    constructor(config) {
        this.url = config.ws_url;
        this.nonce = config.nonce;
        this.agentId = config.agent_id;
        this.socket = null;
        this.reconnectDelay = 3000;
        this.maxReconnectDelay = 30000;
        this.handlers = {};
    }

    connect() {
        const url = this.nonce ? `${this.url}?nonce=${this.nonce}` : this.url;
        this.socket = new WebSocket(url);

        this.socket.onopen = () => this.onOpen();
        this.socket.onmessage = (e) => this.onMessage(e);
        this.socket.onclose = () => this.scheduleReconnect();
        this.socket.onerror = (e) => console.error('[PMW Bridge]', e);
    }

    onOpen() {
        this.reconnectDelay = 3000;
        document.querySelectorAll('.pmw-connection-indicator').forEach(el => {
            el.classList.add('connected');
            el.textContent = 'Connected';
        });
        this.socket.send(JSON.stringify({ type: 'subscribe', scope: 'all' }));
    }

    onMessage(event) {
        try {
            const data = JSON.parse(event.data);
            const handler = this.handlers[data.type];
            if (handler) handler(data.payload);
        } catch (e) {
            console.warn('[PMW Bridge] Parse error', e);
        }
    }

    on(type, fn) {
        this.handlers[type] = fn;
        return this;
    }

    send(command) {
        if (this.socket?.readyState === WebSocket.OPEN) {
            this.socket.send(JSON.stringify(command));
        }
    }

    scheduleReconnect() {
        document.querySelectorAll('.pmw-connection-indicator').forEach(el => {
            el.classList.remove('connected');
            el.textContent = 'Connecting…';
        });
        setTimeout(() => this.connect(), this.reconnectDelay);
        this.reconnectDelay = Math.min(this.reconnectDelay * 1.5, this.maxReconnectDelay);
    }
}

if (typeof window !== 'undefined') {
    window.pmwBridge = window.PMW_BRIDGE ? new PMWBridge(window.PMW_BRIDGE) : null;
    if (window.pmwBridge) {
        window.pmwBridge.connect();
    }
}
