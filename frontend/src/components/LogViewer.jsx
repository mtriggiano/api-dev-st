import { useState, useEffect, useRef, useCallback } from 'react';
import { 
  Terminal, RefreshCw, Search, Filter, Download, 
  ChevronDown, AlertTriangle, AlertCircle, Info,
  Bug, X, ArrowDown, Pause, Play, FileText
} from 'lucide-react';

const LEVEL_COLORS = {
  DEBUG: { bg: 'bg-gray-800', text: 'text-gray-400', badge: 'bg-gray-600 text-gray-200' },
  INFO: { bg: 'bg-transparent', text: 'text-green-300', badge: 'bg-blue-600 text-blue-100' },
  WARNING: { bg: 'bg-yellow-900/30', text: 'text-yellow-200', badge: 'bg-yellow-600 text-yellow-100' },
  ERROR: { bg: 'bg-red-900/40', text: 'text-red-300', badge: 'bg-red-600 text-red-100' },
  CRITICAL: { bg: 'bg-red-900/60', text: 'text-red-200', badge: 'bg-red-800 text-red-100' },
  CONTINUATION: { bg: 'bg-transparent', text: 'text-gray-400', badge: '' },
};

const LEVEL_ICONS = {
  DEBUG: Bug,
  INFO: Info,
  WARNING: AlertTriangle,
  ERROR: AlertCircle,
  CRITICAL: AlertCircle,
};

export default function LogViewer({ instanceName, onClose }) {
  const [logs, setLogs] = useState([]);
  const [availableLogs, setAvailableLogs] = useState([]);
  const [selectedLogType, setSelectedLogType] = useState('odoo');
  const [levelFilter, setLevelFilter] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [searchInput, setSearchInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [stats, setStats] = useState({});
  const [fileInfo, setFileInfo] = useState({});
  const [autoRefresh, setAutoRefresh] = useState(false);
  const [autoScroll, setAutoScroll] = useState(true);
  const [linesCount, setLinesCount] = useState(500);
  
  const logContainerRef = useRef(null);
  const autoRefreshRef = useRef(null);

  const getToken = () => localStorage.getItem('access_token');

  const fetchAvailableLogs = useCallback(async () => {
    try {
      const response = await fetch(`/api/odoo-logs/available/${instanceName}`, {
        headers: { 'Authorization': `Bearer ${getToken()}` }
      });
      const data = await response.json();
      if (data.success) {
        setAvailableLogs(data.logs);
      }
    } catch (err) {
      console.error('Error fetching available logs:', err);
    }
  }, [instanceName]);

  const fetchLogs = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const params = new URLSearchParams({
        type: selectedLogType,
        lines: linesCount.toString(),
      });
      if (levelFilter) params.append('level', levelFilter);
      if (searchQuery) params.append('search', searchQuery);

      const response = await fetch(`/api/odoo-logs/view/${instanceName}?${params}`, {
        headers: { 'Authorization': `Bearer ${getToken()}` }
      });
      const data = await response.json();
      
      if (data.success) {
        setLogs(data.lines);
        setStats(data.stats);
        setFileInfo(data.file_info);
      } else {
        setError(data.error || 'Error al cargar logs');
      }
    } catch (err) {
      setError('Error de conexión al cargar logs');
    } finally {
      setLoading(false);
    }
  }, [instanceName, selectedLogType, linesCount, levelFilter, searchQuery]);

  useEffect(() => {
    fetchAvailableLogs();
  }, [fetchAvailableLogs]);

  useEffect(() => {
    fetchLogs();
  }, [fetchLogs]);

  useEffect(() => {
    if (autoScroll && logContainerRef.current) {
      logContainerRef.current.scrollTop = logContainerRef.current.scrollHeight;
    }
  }, [logs, autoScroll]);

  useEffect(() => {
    if (autoRefresh) {
      autoRefreshRef.current = setInterval(fetchLogs, 5000);
    } else {
      if (autoRefreshRef.current) clearInterval(autoRefreshRef.current);
    }
    return () => {
      if (autoRefreshRef.current) clearInterval(autoRefreshRef.current);
    };
  }, [autoRefresh, fetchLogs]);

  const handleSearch = (e) => {
    e.preventDefault();
    setSearchQuery(searchInput);
  };

  const clearSearch = () => {
    setSearchInput('');
    setSearchQuery('');
  };

  const downloadLog = () => {
    const content = logs.map(l => l.raw).join('\n');
    const blob = new Blob([content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${instanceName}-${selectedLogType}.log`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const scrollToBottom = () => {
    if (logContainerRef.current) {
      logContainerRef.current.scrollTop = logContainerRef.current.scrollHeight;
    }
  };

  return (
    <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4">
      <div className="bg-gray-900 rounded-xl w-full max-w-7xl h-[90vh] flex flex-col shadow-2xl border border-gray-700">
        
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-gray-700 bg-gray-800/50 rounded-t-xl">
          <div className="flex items-center gap-3">
            <Terminal className="w-5 h-5 text-green-400" />
            <h2 className="text-lg font-semibold text-white">
              Logs — <span className="text-green-400">{instanceName}</span>
            </h2>
            {fileInfo.size_human && (
              <span className="text-xs text-gray-500 bg-gray-800 px-2 py-1 rounded">
                {fileInfo.size_human}
              </span>
            )}
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-white transition-colors p-1 rounded hover:bg-gray-700"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Toolbar */}
        <div className="flex flex-wrap items-center gap-2 px-4 py-2 border-b border-gray-700 bg-gray-800/30">
          
          {/* Selector de tipo de log */}
          <div className="flex items-center gap-2">
            <FileText className="w-4 h-4 text-gray-400" />
            <select
              value={selectedLogType}
              onChange={(e) => setSelectedLogType(e.target.value)}
              className="bg-gray-700 text-white text-sm rounded px-2 py-1.5 border border-gray-600 focus:border-blue-500 focus:outline-none"
            >
              {availableLogs.map(log => (
                <option key={log.name} value={log.name}>
                  {log.filename} {log.size_human !== 'systemd' ? `(${log.size_human})` : ''}
                </option>
              ))}
              {availableLogs.length === 0 && (
                <option value="odoo">odoo.log</option>
              )}
            </select>
          </div>

          {/* Separador */}
          <div className="w-px h-6 bg-gray-600" />

          {/* Filtros de nivel */}
          <div className="flex items-center gap-1">
            <Filter className="w-4 h-4 text-gray-400" />
            <button
              onClick={() => setLevelFilter('')}
              className={`px-2 py-1 rounded text-xs font-medium transition-colors ${
                !levelFilter ? 'bg-gray-600 text-white' : 'text-gray-400 hover:text-white hover:bg-gray-700'
              }`}
            >
              TODO
            </button>
            {['INFO', 'WARNING', 'ERROR', 'CRITICAL', 'DEBUG'].map(level => {
              const colors = LEVEL_COLORS[level];
              const count = stats[level.toLowerCase()] || 0;
              return (
                <button
                  key={level}
                  onClick={() => setLevelFilter(levelFilter === level ? '' : level)}
                  className={`px-2 py-1 rounded text-xs font-medium transition-colors flex items-center gap-1 ${
                    levelFilter === level 
                      ? colors.badge
                      : 'text-gray-400 hover:text-white hover:bg-gray-700'
                  }`}
                >
                  {level}
                  {count > 0 && (
                    <span className={`text-[10px] ${levelFilter === level ? 'opacity-80' : 'opacity-60'}`}>
                      ({count})
                    </span>
                  )}
                </button>
              );
            })}
          </div>

          {/* Separador */}
          <div className="w-px h-6 bg-gray-600" />

          {/* Búsqueda */}
          <form onSubmit={handleSearch} className="flex items-center gap-1">
            <div className="relative">
              <Search className="w-4 h-4 text-gray-400 absolute left-2 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                value={searchInput}
                onChange={(e) => setSearchInput(e.target.value)}
                placeholder="Buscar..."
                className="bg-gray-700 text-white text-sm rounded pl-8 pr-8 py-1.5 border border-gray-600 focus:border-blue-500 focus:outline-none w-48"
              />
              {searchInput && (
                <button
                  type="button"
                  onClick={clearSearch}
                  className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-white"
                >
                  <X className="w-3 h-3" />
                </button>
              )}
            </div>
          </form>

          {/* Spacer */}
          <div className="flex-1" />

          {/* Controles */}
          <div className="flex items-center gap-1">
            {/* Líneas */}
            <select
              value={linesCount}
              onChange={(e) => setLinesCount(Number(e.target.value))}
              className="bg-gray-700 text-white text-xs rounded px-2 py-1.5 border border-gray-600 focus:outline-none"
            >
              <option value={100}>100 líneas</option>
              <option value={500}>500 líneas</option>
              <option value={1000}>1000 líneas</option>
              <option value={2000}>2000 líneas</option>
              <option value={5000}>5000 líneas</option>
            </select>

            {/* Auto-refresh */}
            <button
              onClick={() => setAutoRefresh(!autoRefresh)}
              className={`p-1.5 rounded transition-colors ${
                autoRefresh 
                  ? 'bg-green-600/30 text-green-400 hover:bg-green-600/50' 
                  : 'text-gray-400 hover:text-white hover:bg-gray-700'
              }`}
              title={autoRefresh ? 'Detener auto-refresh (5s)' : 'Activar auto-refresh (5s)'}
            >
              {autoRefresh ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
            </button>

            {/* Refresh manual */}
            <button
              onClick={fetchLogs}
              disabled={loading}
              className="p-1.5 rounded text-gray-400 hover:text-white hover:bg-gray-700 transition-colors disabled:opacity-50"
              title="Refrescar"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            </button>

            {/* Descargar */}
            <button
              onClick={downloadLog}
              className="p-1.5 rounded text-gray-400 hover:text-white hover:bg-gray-700 transition-colors"
              title="Descargar log"
            >
              <Download className="w-4 h-4" />
            </button>

            {/* Scroll al final */}
            <button
              onClick={scrollToBottom}
              className={`p-1.5 rounded transition-colors ${
                autoScroll
                  ? 'bg-blue-600/30 text-blue-400 hover:bg-blue-600/50'
                  : 'text-gray-400 hover:text-white hover:bg-gray-700'
              }`}
              title="Ir al final"
              onDoubleClick={() => setAutoScroll(!autoScroll)}
            >
              <ArrowDown className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Error */}
        {error && (
          <div className="px-4 py-2 bg-red-900/30 border-b border-red-800 text-red-300 text-sm flex items-center gap-2">
            <AlertCircle className="w-4 h-4" />
            {error}
          </div>
        )}

        {/* Stats bar */}
        {stats.total > 0 && (
          <div className="px-4 py-1.5 border-b border-gray-700 bg-gray-800/20 flex items-center gap-4 text-xs text-gray-500">
            <span>{stats.total} líneas</span>
            {stats.info > 0 && <span className="text-blue-400">● {stats.info} INFO</span>}
            {stats.warning > 0 && <span className="text-yellow-400">● {stats.warning} WARNING</span>}
            {stats.error > 0 && <span className="text-red-400">● {stats.error} ERROR</span>}
            {stats.critical > 0 && <span className="text-red-300">● {stats.critical} CRITICAL</span>}
            {stats.debug > 0 && <span className="text-gray-400">● {stats.debug} DEBUG</span>}
            {autoRefresh && <span className="text-green-400 ml-auto">⟳ Auto-refresh cada 5s</span>}
          </div>
        )}

        {/* Log content */}
        <div
          ref={logContainerRef}
          className="flex-1 overflow-auto font-mono text-xs leading-5 bg-gray-950"
          onScroll={(e) => {
            const { scrollTop, scrollHeight, clientHeight } = e.target;
            setAutoScroll(scrollHeight - scrollTop - clientHeight < 50);
          }}
        >
          {loading && logs.length === 0 ? (
            <div className="flex items-center justify-center h-full text-gray-500">
              <RefreshCw className="w-6 h-6 animate-spin mr-2" />
              Cargando logs...
            </div>
          ) : logs.length === 0 ? (
            <div className="flex items-center justify-center h-full text-gray-500">
              No se encontraron logs
              {levelFilter && ` con nivel ${levelFilter}`}
              {searchQuery && ` que contengan "${searchQuery}"`}
            </div>
          ) : (
            <table className="w-full">
              <tbody>
                {logs.map((line, idx) => {
                  const colors = LEVEL_COLORS[line.level] || LEVEL_COLORS.CONTINUATION;
                  const LevelIcon = LEVEL_ICONS[line.level];
                  
                  return (
                    <tr
                      key={idx}
                      className={`${colors.bg} hover:bg-gray-800/50 border-b border-gray-800/30`}
                    >
                      {/* Número de línea */}
                      <td className="text-gray-600 text-right pr-3 pl-3 py-0.5 select-none w-12 align-top">
                        {idx + 1}
                      </td>
                      
                      {/* Timestamp */}
                      {line.timestamp && (
                        <td className="text-gray-500 pr-3 py-0.5 whitespace-nowrap align-top w-44">
                          {line.timestamp}
                        </td>
                      )}
                      
                      {/* Level badge */}
                      <td className="pr-3 py-0.5 align-top w-20">
                        {line.level !== 'CONTINUATION' && (
                          <span className={`inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-bold ${colors.badge}`}>
                            {LevelIcon && <LevelIcon className="w-3 h-3" />}
                            {line.level}
                          </span>
                        )}
                      </td>
                      
                      {/* Logger */}
                      <td className="text-cyan-600 pr-3 py-0.5 whitespace-nowrap align-top max-w-[200px] truncate">
                        {line.logger}
                      </td>
                      
                      {/* Message */}
                      <td className={`${colors.text} py-0.5 pr-4 align-top break-all`}>
                        {line.message}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          )}
        </div>

        {/* Footer */}
        <div className="px-4 py-2 border-t border-gray-700 bg-gray-800/30 rounded-b-xl flex items-center justify-between text-xs text-gray-500">
          <span>
            {instanceName} — {selectedLogType}.log
            {fileInfo.path && ` — ${fileInfo.path}`}
          </span>
          <span>
            {loading ? 'Actualizando...' : `${logs.length} líneas cargadas`}
          </span>
        </div>
      </div>
    </div>
  );
}
