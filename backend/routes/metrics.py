from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from datetime import datetime, timedelta
from services.system_monitor import SystemMonitor
from models import db, MetricsHistory

metrics_bp = Blueprint('metrics', __name__)
monitor = SystemMonitor()

MAX_RANGE_MINUTES = 60 * 24 * 30  # 30 días
DEFAULT_POINTS = 240
MAX_POINTS = 1000
AUTO_SAVE_INTERVAL_SECONDS = 15


def _build_history_entry(metrics):
    return MetricsHistory(
        cpu_percent=metrics['cpu']['percent'],
        ram_percent=metrics['memory']['percent'],
        ram_used_gb=metrics['memory']['used_gb'],
        ram_total_gb=metrics['memory']['total_gb'],
        disk_percent=metrics['disk'][0]['percent'] if metrics['disk'] else None,
        disk_used_gb=metrics['disk'][0]['used_gb'] if metrics['disk'] else None,
        disk_total_gb=metrics['disk'][0]['total_gb'] if metrics['disk'] else None,
        network_sent_mb=metrics['network']['mb_sent'],
        network_recv_mb=metrics['network']['mb_recv']
    )


def _downsample_metrics(rows, max_points):
    total_rows = len(rows)
    if total_rows <= max_points:
        return rows

    if max_points <= 1:
        return [rows[-1]]

    step = (total_rows - 1) / (max_points - 1)
    sampled = []
    seen_indexes = set()

    for i in range(max_points):
        index = int(round(i * step))
        if index >= total_rows:
            index = total_rows - 1
        if index in seen_indexes:
            continue
        sampled.append(rows[index])
        seen_indexes.add(index)

    if sampled and sampled[-1] != rows[-1]:
        sampled.append(rows[-1])

    return sampled

@metrics_bp.route('/current', methods=['GET'])
@jwt_required()
def get_current_metrics():
    """Obtiene las métricas actuales del sistema"""
    try:
        metrics = monitor.get_all_metrics()

        # Guardado oportunista para asegurar historial aunque el cron falle
        latest = MetricsHistory.query.order_by(MetricsHistory.timestamp.desc()).first()
        now = datetime.utcnow()
        should_store = (
            latest is None
            or latest.timestamp is None
            or (now - latest.timestamp).total_seconds() >= AUTO_SAVE_INTERVAL_SECONDS
        )

        if should_store:
            history = _build_history_entry(metrics)
            db.session.add(history)
            db.session.commit()

        return jsonify(metrics), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@metrics_bp.route('/history', methods=['GET'])
@jwt_required()
def get_metrics_history():
    """Obtiene el historial de métricas"""
    try:
        # Parámetros
        minutes = request.args.get('minutes', default=60, type=int) or 60
        minutes = max(1, min(minutes, MAX_RANGE_MINUTES))

        requested_points = request.args.get('points', default=DEFAULT_POINTS, type=int) or DEFAULT_POINTS
        max_points = max(1, min(requested_points, MAX_POINTS))
        
        # Calcular timestamp de inicio
        start_time = datetime.utcnow() - timedelta(minutes=minutes)
        
        # Consultar historial
        metrics = MetricsHistory.query.filter(
            MetricsHistory.timestamp >= start_time
        ).order_by(MetricsHistory.timestamp.asc()).all()

        # Asegurar al menos un dato para que el dashboard nunca quede vacío
        if not metrics:
            live_metrics = monitor.get_all_metrics()
            history = _build_history_entry(live_metrics)
            db.session.add(history)
            db.session.commit()
            metrics = [history]

        sampled_metrics = _downsample_metrics(metrics, max_points)
        
        return jsonify({
            'metrics': [m.to_dict() for m in sampled_metrics],
            'count': len(sampled_metrics),
            'total': len(metrics),
            'range_minutes': minutes
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@metrics_bp.route('/save', methods=['POST'])
def save_current_metrics():
    """Guarda las métricas actuales en el historial (llamado por cron)"""
    try:
        metrics = monitor.get_all_metrics()
        
        # Crear registro
        history = _build_history_entry(metrics)
        
        db.session.add(history)
        db.session.commit()
        
        return jsonify({'message': 'Métricas guardadas', 'id': history.id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
