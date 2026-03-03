import { useEffect, useMemo, useState } from 'react';
import { metrics } from '../lib/api';
import { Cpu, HardDrive, Activity, Network, Clock } from 'lucide-react';
import { Area, AreaChart, CartesianGrid, Line, LineChart, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';

const RANGE_OPTIONS = [
  { minutes: 60, label: '1h', description: 'Ultima hora' },
  { minutes: 360, label: '6h', description: 'Ultimas 6 horas' },
  { minutes: 1440, label: '24h', description: 'Ultimo dia' },
  { minutes: 10080, label: '7d', description: 'Ultima semana' },
  { minutes: 43200, label: '30d', description: 'Ultimo mes' },
];

const DASHBOARD_RANGE_STORAGE_KEY = 'api-dev.dashboard.rangeMinutes';

const formatXAxisTick = (value, rangeMinutes) => {
  if (!value) return '';
  const date = new Date(value);

  if (rangeMinutes <= 1440) {
    return date.toLocaleTimeString('es-AR', { hour: '2-digit', minute: '2-digit' });
  }

  return date.toLocaleDateString('es-AR', { day: '2-digit', month: '2-digit' });
};

const formatTooltipLabel = (value) => {
  if (!value) return '';
  return new Date(value).toLocaleString('es-AR', {
    day: '2-digit',
    month: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  });
};

const formatArgentinaDateTime = (value) => {
  if (!value) return '-';

  return new Date(value).toLocaleString('es-AR', {
    timeZone: 'America/Argentina/Buenos_Aires',
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false,
  });
};

const buildSeriesStats = (rows, key) => {
  const values = rows
    .map((row) => Number(row?.[key]))
    .filter((value) => Number.isFinite(value));

  if (values.length === 0) {
    return { last: 0, min: 0, avg: 0, max: 0 };
  }

  const sum = values.reduce((acc, value) => acc + value, 0);
  return {
    last: Number(values[values.length - 1].toFixed(2)),
    min: Number(Math.min(...values).toFixed(2)),
    avg: Number((sum / values.length).toFixed(2)),
    max: Number(Math.max(...values).toFixed(2)),
  };
};

export default function Dashboard() {
  const [currentMetrics, setCurrentMetrics] = useState(null);
  const [history, setHistory] = useState([]);
  const [rangeMinutes, setRangeMinutes] = useState(() => {
    try {
      const storedValue = Number(localStorage.getItem(DASHBOARD_RANGE_STORAGE_KEY));
      const isValid = RANGE_OPTIONS.some((option) => option.minutes === storedValue);
      return isValid ? storedValue : 60;
    } catch {
      return 60;
    }
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    try {
      localStorage.setItem(DASHBOARD_RANGE_STORAGE_KEY, String(rangeMinutes));
    } catch {
      // Ignorar errores de acceso a localStorage
    }
  }, [rangeMinutes]);

  useEffect(() => {
    fetchMetrics();
    const interval = setInterval(fetchMetrics, 15000);
    return () => clearInterval(interval);
  }, [rangeMinutes]);

  const fetchMetrics = async () => {
    try {
      const [current, hist] = await Promise.all([
        metrics.getCurrent(),
        metrics.getHistory(rangeMinutes)
      ]);
      setCurrentMetrics(current.data);
      setHistory(hist.data.metrics || []);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching metrics:', error);
      setLoading(false);
    }
  };

  const selectedRange = RANGE_OPTIONS.find((range) => range.minutes === rangeMinutes) || RANGE_OPTIONS[0];

  const chartHistory = useMemo(() => {
    return history.map((point, index) => {
      if (index === 0) {
        return {
          ...point,
          network_sent_rate_mb_min: 0,
          network_recv_rate_mb_min: 0,
        };
      }

      const previousPoint = history[index - 1];
      const elapsedSeconds = (new Date(point.timestamp) - new Date(previousPoint.timestamp)) / 1000;

      if (elapsedSeconds <= 0) {
        return {
          ...point,
          network_sent_rate_mb_min: 0,
          network_recv_rate_mb_min: 0,
        };
      }

      const sentDelta = Math.max((point.network_sent_mb ?? 0) - (previousPoint.network_sent_mb ?? 0), 0);
      const recvDelta = Math.max((point.network_recv_mb ?? 0) - (previousPoint.network_recv_mb ?? 0), 0);
      const secondsPerMinute = 60;

      return {
        ...point,
        network_sent_rate_mb_min: Number(((sentDelta / elapsedSeconds) * secondsPerMinute).toFixed(2)),
        network_recv_rate_mb_min: Number(((recvDelta / elapsedSeconds) * secondsPerMinute).toFixed(2)),
      };
    });
  }, [history]);

  const cpuStats = useMemo(() => buildSeriesStats(chartHistory, 'cpu_percent'), [chartHistory]);
  const ramStats = useMemo(() => buildSeriesStats(chartHistory, 'ram_percent'), [chartHistory]);
  const diskStats = useMemo(() => buildSeriesStats(chartHistory, 'disk_percent'), [chartHistory]);
  const netRecvStats = useMemo(() => buildSeriesStats(chartHistory, 'network_recv_rate_mb_min'), [chartHistory]);
  const netSentStats = useMemo(() => buildSeriesStats(chartHistory, 'network_sent_rate_mb_min'), [chartHistory]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (!currentMetrics) {
    return <div className="text-center text-gray-600 dark:text-gray-300">No hay datos disponibles</div>;
  }

  const { cpu, memory, disk, network, system } = currentMetrics;
  const serverDateTime = system?.server_datetime || currentMetrics?.timestamp;
  const serverTimezone = system?.server_timezone || 'America/Argentina/Buenos_Aires';

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Estado del Servidor</h2>
            <p className="text-gray-600 dark:text-gray-300 mt-1">{system.hostname}</p>
          </div>
          <div className="text-right">
            <div className="flex items-center gap-2 text-gray-600 dark:text-gray-300">
              <Clock className="w-5 h-5" />
              <span>Uptime: {system.uptime_formatted}</span>
            </div>
            <p className="text-sm text-gray-600 dark:text-gray-300 mt-1">
              Fecha y hora servidor (AR): {formatArgentinaDateTime(serverDateTime)}
            </p>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">Zona horaria: {serverTimezone}</p>
            <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">{system.platform} {system.platform_release}</p>
          </div>
        </div>
      </div>

      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-sm font-medium text-gray-700 dark:text-gray-200">Rango historico:</span>
          {RANGE_OPTIONS.map((option) => (
            <button
              key={option.minutes}
              type="button"
              onClick={() => setRangeMinutes(option.minutes)}
              className={`px-3 py-1.5 text-sm rounded-md border transition-colors ${
                rangeMinutes === option.minutes
                  ? 'bg-blue-600 text-white border-blue-600'
                  : 'bg-white dark:bg-gray-900 text-gray-700 dark:text-gray-200 border-gray-300 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-800'
              }`}
            >
              {option.label}
            </button>
          ))}
        </div>
        <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">
          Mostrando datos de: {selectedRange.description}
        </p>
        {chartHistory.length < 5 && (
          <p className="text-xs text-amber-600 dark:text-amber-400 mt-2">
            Recolectando historial... ({chartHistory.length} punto{chartHistory.length === 1 ? '' : 's'}). En unos minutos vas a ver una curva completa.
          </p>
        )}
      </div>

      {/* Métricas principales */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {/* CPU */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <div className="bg-blue-100 p-2 rounded-lg">
                <Cpu className="w-6 h-6 text-blue-600" />
              </div>
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-300">CPU</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">{cpu.percent}%</p>
              </div>
            </div>
          </div>
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span className="text-gray-600 dark:text-gray-300">Cores</span>
              <span className="font-medium">{cpu.count}</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-blue-600 h-2 rounded-full transition-all"
                style={{ width: `${cpu.percent}%` }}
              ></div>
            </div>
          </div>
        </div>

        {/* RAM */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <div className="bg-green-100 p-2 rounded-lg">
                <Activity className="w-6 h-6 text-green-600" />
              </div>
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-300">RAM</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">{memory.percent}%</p>
              </div>
            </div>
          </div>
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span className="text-gray-600 dark:text-gray-300">Usado</span>
              <span className="font-medium">{memory.used_gb} GB / {memory.total_gb} GB</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-green-600 h-2 rounded-full transition-all"
                style={{ width: `${memory.percent}%` }}
              ></div>
            </div>
          </div>
        </div>

        {/* Disco */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <div className="bg-purple-100 p-2 rounded-lg">
                <HardDrive className="w-6 h-6 text-purple-600" />
              </div>
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-300">Disco</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">
                  {disk[0]?.percent || 0}%
                </p>
              </div>
            </div>
          </div>
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span className="text-gray-600 dark:text-gray-300">Usado</span>
              <span className="font-medium">
                {disk[0]?.used_gb || 0} GB / {disk[0]?.total_gb || 0} GB
              </span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-purple-600 h-2 rounded-full transition-all"
                style={{ width: `${disk[0]?.percent || 0}%` }}
              ></div>
            </div>
          </div>
        </div>

        {/* Red */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <div className="bg-orange-100 p-2 rounded-lg">
                <Network className="w-6 h-6 text-orange-600" />
              </div>
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-300">Red</p>
                <p className="text-lg font-bold text-gray-900 dark:text-white">
                  {network.speed_mbps_recv.toFixed(2)} MB/s
                </p>
              </div>
            </div>
          </div>
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span className="text-gray-600 dark:text-gray-300">↓ Recibido</span>
              <span className="font-medium">{network.mb_recv} MB</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-gray-600 dark:text-gray-300">↑ Enviado</span>
              <span className="font-medium">{network.mb_sent} MB</span>
            </div>
          </div>
        </div>
      </div>

      {/* Gráficos */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* CPU History */}
        <div className="bg-zinc-900 border border-zinc-700 rounded-lg shadow p-4">
          <h3 className="text-sm font-semibold text-zinc-100 mb-3">CPU utilization · {selectedRange.description}</h3>
          <ResponsiveContainer width="100%" height={200}>
            <AreaChart data={chartHistory}>
              <CartesianGrid stroke="#3f3f46" strokeDasharray="2 2" />
              <XAxis
                dataKey="timestamp"
                tickFormatter={(value) => formatXAxisTick(value, rangeMinutes)}
                tick={{ fill: '#d4d4d8', fontSize: 11 }}
                axisLine={{ stroke: '#52525b' }}
                tickLine={{ stroke: '#52525b' }}
              />
              <YAxis domain={[0, 100]} tick={{ fill: '#d4d4d8', fontSize: 11 }} axisLine={{ stroke: '#52525b' }} tickLine={{ stroke: '#52525b' }} />
              <Tooltip
                labelFormatter={formatTooltipLabel}
                formatter={(value) => [`${Number(value ?? 0).toFixed(2)}%`, 'CPU']}
                contentStyle={{ backgroundColor: '#18181b', borderColor: '#3f3f46', borderRadius: '8px' }}
                labelStyle={{ color: '#fafafa' }}
                itemStyle={{ color: '#22c55e' }}
              />
              <ReferenceLine y={90} stroke="#eab308" strokeDasharray="4 4" ifOverflow="extendDomain" />
              <Area type="monotone" dataKey="cpu_percent" stroke="#22c55e" fill="#14532d" fillOpacity={0.35} strokeWidth={2} dot={false} />
            </AreaChart>
          </ResponsiveContainer>
          <div className="grid grid-cols-4 gap-2 text-xs text-zinc-200 mt-3">
            <div><p className="text-zinc-400">último</p><p>{cpuStats.last}%</p></div>
            <div><p className="text-zinc-400">mínimo</p><p>{cpuStats.min}%</p></div>
            <div><p className="text-zinc-400">media</p><p>{cpuStats.avg}%</p></div>
            <div><p className="text-zinc-400">máximo</p><p>{cpuStats.max}%</p></div>
          </div>
        </div>

        {/* RAM History */}
        <div className="bg-zinc-900 border border-zinc-700 rounded-lg shadow p-4">
          <h3 className="text-sm font-semibold text-zinc-100 mb-3">RAM utilization · {selectedRange.description}</h3>
          <ResponsiveContainer width="100%" height={200}>
            <AreaChart data={chartHistory}>
              <CartesianGrid stroke="#3f3f46" strokeDasharray="2 2" />
              <XAxis
                dataKey="timestamp"
                tickFormatter={(value) => formatXAxisTick(value, rangeMinutes)}
                tick={{ fill: '#d4d4d8', fontSize: 11 }}
                axisLine={{ stroke: '#52525b' }}
                tickLine={{ stroke: '#52525b' }}
              />
              <YAxis domain={[0, 100]} tick={{ fill: '#d4d4d8', fontSize: 11 }} axisLine={{ stroke: '#52525b' }} tickLine={{ stroke: '#52525b' }} />
              <Tooltip
                labelFormatter={formatTooltipLabel}
                formatter={(value) => [`${Number(value ?? 0).toFixed(2)}%`, 'RAM']}
                contentStyle={{ backgroundColor: '#18181b', borderColor: '#3f3f46', borderRadius: '8px' }}
                labelStyle={{ color: '#fafafa' }}
                itemStyle={{ color: '#22c55e' }}
              />
              <ReferenceLine y={90} stroke="#eab308" strokeDasharray="4 4" ifOverflow="extendDomain" />
              <Area type="monotone" dataKey="ram_percent" stroke="#22c55e" fill="#14532d" fillOpacity={0.35} strokeWidth={2} dot={false} />
            </AreaChart>
          </ResponsiveContainer>
          <div className="grid grid-cols-4 gap-2 text-xs text-zinc-200 mt-3">
            <div><p className="text-zinc-400">último</p><p>{ramStats.last}%</p></div>
            <div><p className="text-zinc-400">mínimo</p><p>{ramStats.min}%</p></div>
            <div><p className="text-zinc-400">media</p><p>{ramStats.avg}%</p></div>
            <div><p className="text-zinc-400">máximo</p><p>{ramStats.max}%</p></div>
          </div>
        </div>

        {/* Disk History */}
        <div className="bg-zinc-900 border border-zinc-700 rounded-lg shadow p-4">
          <h3 className="text-sm font-semibold text-zinc-100 mb-3">Disk usage · {selectedRange.description}</h3>
          <ResponsiveContainer width="100%" height={200}>
            <AreaChart data={chartHistory}>
              <CartesianGrid stroke="#3f3f46" strokeDasharray="2 2" />
              <XAxis
                dataKey="timestamp"
                tickFormatter={(value) => formatXAxisTick(value, rangeMinutes)}
                tick={{ fill: '#d4d4d8', fontSize: 11 }}
                axisLine={{ stroke: '#52525b' }}
                tickLine={{ stroke: '#52525b' }}
              />
              <YAxis domain={[0, 100]} tick={{ fill: '#d4d4d8', fontSize: 11 }} axisLine={{ stroke: '#52525b' }} tickLine={{ stroke: '#52525b' }} />
              <Tooltip
                labelFormatter={formatTooltipLabel}
                formatter={(value) => [`${Number(value ?? 0).toFixed(2)}%`, 'Disco']}
                contentStyle={{ backgroundColor: '#18181b', borderColor: '#3f3f46', borderRadius: '8px' }}
                labelStyle={{ color: '#fafafa' }}
                itemStyle={{ color: '#a855f7' }}
              />
              <ReferenceLine y={85} stroke="#eab308" strokeDasharray="4 4" ifOverflow="extendDomain" />
              <Area type="monotone" dataKey="disk_percent" stroke="#a855f7" fill="#581c87" fillOpacity={0.35} strokeWidth={2} dot={false} />
            </AreaChart>
          </ResponsiveContainer>
          <div className="grid grid-cols-4 gap-2 text-xs text-zinc-200 mt-3">
            <div><p className="text-zinc-400">último</p><p>{diskStats.last}%</p></div>
            <div><p className="text-zinc-400">mínimo</p><p>{diskStats.min}%</p></div>
            <div><p className="text-zinc-400">media</p><p>{diskStats.avg}%</p></div>
            <div><p className="text-zinc-400">máximo</p><p>{diskStats.max}%</p></div>
          </div>
        </div>

        {/* Network History */}
        <div className="bg-zinc-900 border border-zinc-700 rounded-lg shadow p-4">
          <h3 className="text-sm font-semibold text-zinc-100 mb-3">Network traffic (MB/min) · {selectedRange.description}</h3>
          <ResponsiveContainer width="100%" height={200}>
            <LineChart data={chartHistory}>
              <CartesianGrid stroke="#3f3f46" strokeDasharray="2 2" />
              <XAxis
                dataKey="timestamp"
                tickFormatter={(value) => formatXAxisTick(value, rangeMinutes)}
                tick={{ fill: '#d4d4d8', fontSize: 11 }}
                axisLine={{ stroke: '#52525b' }}
                tickLine={{ stroke: '#52525b' }}
              />
              <YAxis tick={{ fill: '#d4d4d8', fontSize: 11 }} axisLine={{ stroke: '#52525b' }} tickLine={{ stroke: '#52525b' }} />
              <Tooltip
                labelFormatter={formatTooltipLabel}
                formatter={(value, name) => [
                  `${Number(value ?? 0).toFixed(2)} MB/min`,
                  name === 'network_recv_rate_mb_min' ? 'Recibido' : 'Enviado'
                ]}
                contentStyle={{ backgroundColor: '#18181b', borderColor: '#3f3f46', borderRadius: '8px' }}
                labelStyle={{ color: '#fafafa' }}
              />
              <Line type="monotone" dataKey="network_recv_rate_mb_min" stroke="#f97316" strokeWidth={2} dot={false} name="network_recv_rate_mb_min" />
              <Line type="monotone" dataKey="network_sent_rate_mb_min" stroke="#38bdf8" strokeWidth={2} dot={false} name="network_sent_rate_mb_min" />
            </LineChart>
          </ResponsiveContainer>
          <div className="grid grid-cols-2 gap-2 text-xs text-zinc-200 mt-3">
            <div>
              <p className="text-zinc-400">recibido (últ / máx)</p>
              <p>{netRecvStats.last} / {netRecvStats.max} MB/min</p>
            </div>
            <div>
              <p className="text-zinc-400">enviado (últ / máx)</p>
              <p>{netSentStats.last} / {netSentStats.max} MB/min</p>
            </div>
          </div>
        </div>
      </div>

      {/* Discos */}
      {disk.length > 0 && (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Particiones de Disco</h3>
          <div className="space-y-4">
            {disk.map((partition, index) => (
              <div key={index} className="border-b border-gray-200 pb-4 last:border-0">
                <div className="flex justify-between items-center mb-2">
                  <div>
                    <p className="font-medium text-gray-900 dark:text-white">{partition.mountpoint}</p>
                    <p className="text-sm text-gray-600 dark:text-gray-300">{partition.device} ({partition.fstype})</p>
                  </div>
                  <div className="text-right">
                    <p className="font-medium text-gray-900 dark:text-white">{partition.percent}%</p>
                    <p className="text-sm text-gray-600 dark:text-gray-300">
                      {partition.used_gb} GB / {partition.total_gb} GB
                    </p>
                  </div>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-purple-600 h-2 rounded-full transition-all"
                    style={{ width: `${partition.percent}%` }}
                  ></div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
