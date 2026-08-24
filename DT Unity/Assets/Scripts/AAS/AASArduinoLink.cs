using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.Text;
using System.Threading;
using UnityEngine;
using Newtonsoft.Json.Linq;

/// <summary>
/// Singleton that manages shared TCP connections to Arduino hardware endpoints.
/// Supports multiple connections (one per unique IP:port combination).
/// All AASSensorController instances subscribe here instead of opening their own connections.
/// 
/// Architecture:
///   Arduino A (192.168.10.1:8888) <-> ConnectionState thread A
///   Arduino B (192.168.10.2:9000) <-> ConnectionState thread B
///          \                    /
///           AASArduinoLink.Instance
///                    |
///        port callbacks -> all controllers
/// </summary>
public class AASArduinoLink : MonoBehaviour
{
    // -----------------------------------------------------------------------
    // Singleton
    // -----------------------------------------------------------------------
    public static AASArduinoLink Instance { get; private set; }

    void Awake()
    {
        if (Instance != null && Instance != this) { Destroy(gameObject); return; }
        Instance = this;
        DontDestroyOnLoad(gameObject);
    }

    // -----------------------------------------------------------------------
    // Per-endpoint connection state
    // -----------------------------------------------------------------------
    private class ConnectionState
    {
        public string ip;
        public int    port;
        public Thread thread;
        public volatile bool running;
        public System.Net.Sockets.TcpClient client;
    }

    private readonly object _connLock = new object();
    private readonly Dictionary<string, ConnectionState> _connections = new();

    private static string Key(string ip, int port) => $"{ip}:{port}";

    // -----------------------------------------------------------------------
    // Subscriber registry  portId -> list of callbacks
    // -----------------------------------------------------------------------
    private readonly object _regLock = new object();
    private readonly Dictionary<string, List<Action<bool>>> _subscribers = new();

    public void Subscribe(string portId, Action<bool> callback)
    {
        lock (_regLock)
        {
            if (!_subscribers.TryGetValue(portId, out var list))
            {
                list = new List<Action<bool>>();
                _subscribers[portId] = list;
            }
            if (!list.Contains(callback))
                list.Add(callback);
        }
    }

    public void Unsubscribe(string portId, Action<bool> callback)
    {
        lock (_regLock)
        {
            if (_subscribers.TryGetValue(portId, out var list))
                list.Remove(callback);
        }
    }

    // -----------------------------------------------------------------------
    // Main-thread event queue (all connections enqueue here)
    // -----------------------------------------------------------------------
    private readonly ConcurrentQueue<(string portId, bool value)> _queue = new();

    // -----------------------------------------------------------------------
    // Connection management
    // -----------------------------------------------------------------------

    /// <summary>
    /// Start a TCP connection to ip:port if one isn't already running.
    /// Idempotent: calling multiple times with the same endpoint is safe.
    /// </summary>
    public void StartConnection(string ip, int port)
    {
        string key = Key(ip, port);
        lock (_connLock)
        {
            if (_connections.TryGetValue(key, out var existing) && existing.running)
            {
                Debug.Log($"[ArduinoLink] Already connected to {key}, skipping.");
                return;
            }

            var cs = new ConnectionState { ip = ip, port = port, running = true };
            cs.thread = new Thread(() => ReceiveLoop(cs))
            {
                IsBackground = true,
                Name         = $"ArduinoLink_{key}"
            };
            _connections[key] = cs;
            cs.thread.Start();
            Debug.Log($"[ArduinoLink] Starting TCP connection to {key}");
        }
    }

    /// <summary>Stop the connection to a specific ip:port.</summary>
    public void StopConnection(string ip, int port)
    {
        string key = Key(ip, port);
        ConnectionState cs;
        lock (_connLock)
        {
            if (!_connections.TryGetValue(key, out cs)) return;
            _connections.Remove(key);
        }
        cs.running = false;
        try { cs.client?.Close(); } catch { }
        cs.thread?.Join(400);
        Debug.Log($"[ArduinoLink] Stopped connection to {key}");
    }

    public void StopAllConnections()
    {
        List<ConnectionState> all;
        lock (_connLock)
        {
            all = new List<ConnectionState>(_connections.Values);
            _connections.Clear();
        }
        foreach (var cs in all)
        {
            cs.running = false;
            try { cs.client?.Close(); } catch { }
            cs.thread?.Join(400);
        }
        while (_queue.TryDequeue(out _)) { }
        Debug.Log("[ArduinoLink] All connections stopped.");
    }

    // -----------------------------------------------------------------------
    // Background TCP receive loop (one per ConnectionState)
    // -----------------------------------------------------------------------
    private void ReceiveLoop(ConnectionState cs)
    {
        while (cs.running)
        {
            try
            {
                cs.client = new System.Net.Sockets.TcpClient();
                cs.client.Connect(cs.ip, cs.port);
                cs.client.ReceiveTimeout = 0;

                using var stream = cs.client.GetStream();
                Debug.Log($"[ArduinoLink] Connected to {cs.ip}:{cs.port}");

                var buf        = new StringBuilder();
                int braceDepth = 0;

                while (cs.running && cs.client.Connected)
                {
                    int b = stream.ReadByte();
                    if (b < 0) break;

                    char c = (char)b;
                    if (c == '{') braceDepth++;
                    else if (c == '}') braceDepth--;
                    buf.Append(c);

                    if (braceDepth == 0 && buf.Length > 2)
                    {
                        ParseAndEnqueue(buf.ToString());
                        buf.Clear();
                    }
                }
            }
            catch (Exception ex)
            {
                if (cs.running)
                {
                    Debug.LogWarning($"[ArduinoLink] TCP error ({cs.ip}:{cs.port}): {ex.Message} — retrying in 3s");
                    Thread.Sleep(3000);
                }
            }
            finally
            {
                try { cs.client?.Close(); } catch { }
                cs.client = null;
            }
        }
    }

    private void ParseAndEnqueue(string json)
    {
        try
        {
            var obj   = JObject.Parse(json);
            string id = obj["Port"]?.ToString();
            int raw   = obj["Value"] != null ? (int)obj["Value"] : -1;
            if (id != null && raw >= 0)
                _queue.Enqueue((id, raw == 1));
        }
        catch { }
    }

    // -----------------------------------------------------------------------
    // Main-thread dispatch
    // -----------------------------------------------------------------------
    void Update()
    {
        while (_queue.TryDequeue(out var evt))
        {
            List<Action<bool>> callbacks;
            lock (_regLock)
            {
                _subscribers.TryGetValue(evt.portId, out callbacks);
            }
            if (callbacks != null)
                foreach (var cb in callbacks)
                    cb?.Invoke(evt.value);
        }
    }

    void OnDestroy()
    {
        if (Instance == this)
        {
            StopAllConnections();
            Instance = null;
        }
    }
}
