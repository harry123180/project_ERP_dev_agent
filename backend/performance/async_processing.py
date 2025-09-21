# Asynchronous Processing System with Celery
# High-performance async task processing for ERP operations

import os
import json
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum

from celery import Celery, Task
from celery.result import AsyncResult
from celery.schedules import crontab
from celery.signals import task_prerun, task_postrun, task_failure
from kombu import Queue

logger = logging.getLogger(__name__)

# Celery application configuration
celery_app = Celery('erp_async_processing')

# Configure Celery
celery_app.conf.update(
    # Broker settings
    broker_url=os.environ.get('CELERY_BROKER_URL', 'redis://redis-cluster:6379/1'),
    result_backend=os.environ.get('CELERY_RESULT_BACKEND', 'redis://redis-cluster:6379/2'),
    
    # Task settings
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
    timezone='Asia/Taipei',
    enable_utc=True,
    
    # Task routing
    task_routes={
        'erp.tasks.email.*': {'queue': 'email'},
        'erp.tasks.reports.*': {'queue': 'reports'},
        'erp.tasks.procurement.*': {'queue': 'procurement'},
        'erp.tasks.notifications.*': {'queue': 'notifications'},
        'erp.tasks.maintenance.*': {'queue': 'maintenance'},
    },
    
    # Queue configuration
    task_default_queue='default',
    task_queues=(
        Queue('default', routing_key='default'),
        Queue('email', routing_key='email'),
        Queue('reports', routing_key='reports'),
        Queue('procurement', routing_key='procurement'),
        Queue('notifications', routing_key='notifications'),
        Queue('maintenance', routing_key='maintenance'),
    ),
    
    # Task execution settings
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_max_retries=3,
    task_default_retry_delay=60,
    
    # Monitoring
    worker_send_task_events=True,
    task_send_sent_event=True,
    
    # Beat schedule for periodic tasks
    beat_schedule={
        'generate-daily-reports': {
            'task': 'erp.tasks.reports.generate_daily_report',
            'schedule': crontab(hour=1, minute=0),  # 1:00 AM daily
        },
        'cleanup-expired-sessions': {
            'task': 'erp.tasks.maintenance.cleanup_expired_sessions',
            'schedule': crontab(hour=2, minute=0),  # 2:00 AM daily
        },
        'supplier-performance-analysis': {
            'task': 'erp.tasks.reports.analyze_supplier_performance',
            'schedule': crontab(hour=3, minute=0, day_of_week=1),  # Monday 3:00 AM
        },
        'send-delivery-reminders': {
            'task': 'erp.tasks.notifications.send_delivery_reminders',
            'schedule': crontab(hour=9, minute=0),  # 9:00 AM daily
        },
        'backup-critical-data': {
            'task': 'erp.tasks.maintenance.backup_critical_data',
            'schedule': crontab(hour=23, minute=0),  # 11:00 PM daily
        },
    },
)

class TaskPriority(Enum):
    """Task priority levels"""
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3

@dataclass
class TaskResult:
    """Standardized task result"""
    success: bool
    data: Any = None
    error: str = None
    task_id: str = None
    execution_time: float = None
    metadata: Dict[str, Any] = None

class BaseERPTask(Task):
    """Base task class with common functionality"""
    
    def __init__(self):
        self.start_time = None
        
    def on_retry(self, exc, task_id, args, kwargs, einfo):
        """Called when task is retried"""
        logger.warning(f"Task {task_id} retrying due to: {exc}")
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Called when task fails"""
        logger.error(f"Task {task_id} failed: {exc}")
        # Could send notification or log to external system
    
    def on_success(self, retval, task_id, args, kwargs):
        """Called when task succeeds"""
        if self.start_time:
            execution_time = time.time() - self.start_time
            logger.info(f"Task {task_id} completed in {execution_time:.2f}s")

# Set base task class
celery_app.Task = BaseERPTask

# Task monitoring signals
@task_prerun.connect
def task_prerun_handler(sender=None, task_id=None, task=None, args=None, kwargs=None, **kwds):
    """Task pre-run signal handler"""
    task.start_time = time.time()
    logger.info(f"Starting task {task_id}: {sender}")

@task_postrun.connect
def task_postrun_handler(sender=None, task_id=None, task=None, args=None, kwargs=None, retval=None, state=None, **kwds):
    """Task post-run signal handler"""
    if hasattr(task, 'start_time') and task.start_time:
        execution_time = time.time() - task.start_time
        logger.info(f"Task {task_id} finished in {execution_time:.2f}s with state: {state}")

@task_failure.connect
def task_failure_handler(sender=None, task_id=None, exception=None, traceback=None, einfo=None, **kwds):
    """Task failure signal handler"""
    logger.error(f"Task {task_id} failed with exception: {exception}")

# ================================
# PROCUREMENT TASKS
# ================================

@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def process_purchase_order(self, po_data: Dict[str, Any]) -> TaskResult:
    """
    Process purchase order creation and notifications
    
    Args:
        po_data: Purchase order data
        
    Returns:
        TaskResult with processing outcome
    """
    try:
        from app.models import PurchaseOrder, Supplier
        from app import db
        
        logger.info(f"Processing purchase order: {po_data.get('po_number')}")
        
        # Create purchase order
        po = PurchaseOrder(
            po_number=po_data['po_number'],
            supplier_id=po_data['supplier_id'],
            requisition_id=po_data.get('requisition_id'),
            total_amount=po_data['total_amount'],
            status='pending',
            created_at=datetime.utcnow()
        )
        
        db.session.add(po)
        db.session.commit()
        
        # Send notification to supplier
        send_po_notification.delay(po.id)
        
        # Update inventory reservations
        update_inventory_reservations.delay(po.id, po_data.get('items', []))
        
        # Log audit event
        log_audit_event.delay('po_created', {
            'po_id': po.id,
            'po_number': po.po_number,
            'supplier_id': po.supplier_id,
            'amount': po.total_amount
        })
        
        return TaskResult(
            success=True,
            data={'po_id': po.id, 'po_number': po.po_number},
            task_id=self.request.id
        )
        
    except Exception as exc:
        logger.error(f"Purchase order processing failed: {exc}")
        
        # Retry with exponential backoff
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))
        
        return TaskResult(
            success=False,
            error=str(exc),
            task_id=self.request.id
        )

@celery_app.task(bind=True, max_retries=2)
def send_po_notification(self, po_id: int) -> TaskResult:
    """Send purchase order notification to supplier"""
    try:
        from app.models import PurchaseOrder, Supplier
        
        po = PurchaseOrder.query.get(po_id)
        if not po:
            raise ValueError(f"Purchase order {po_id} not found")
        
        supplier = Supplier.query.get(po.supplier_id)
        if not supplier:
            raise ValueError(f"Supplier {po.supplier_id} not found")
        
        # Send email notification
        send_email_notification.delay(
            'purchase_order_created',
            supplier.supplier_email,
            {
                'po_number': po.po_number,
                'supplier_name': supplier.supplier_name_zh,
                'total_amount': po.total_amount,
                'delivery_date': po.expected_delivery_date.isoformat() if po.expected_delivery_date else None
            }
        )
        
        # Update PO status
        po.notification_sent_at = datetime.utcnow()
        from app import db
        db.session.commit()
        
        return TaskResult(success=True, data={'po_id': po_id})
        
    except Exception as exc:
        logger.error(f"Failed to send PO notification: {exc}")
        
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc, countdown=300)  # Retry after 5 minutes
        
        return TaskResult(success=False, error=str(exc))

@celery_app.task(bind=True)
def update_inventory_reservations(self, po_id: int, items: List[Dict]) -> TaskResult:
    """Update inventory reservations for purchase order items"""
    try:
        from app.models import Storage
        from app import db
        
        for item in items:
            storage_item = Storage.query.filter_by(
                item_name=item['item_name']
            ).first()
            
            if storage_item:
                # Reserve quantity
                storage_item.reserved_quantity = (storage_item.reserved_quantity or 0) + item['quantity']
                
        db.session.commit()
        
        return TaskResult(success=True, data={'po_id': po_id, 'items_updated': len(items)})
        
    except Exception as exc:
        logger.error(f"Failed to update inventory reservations: {exc}")
        return TaskResult(success=False, error=str(exc))

# ================================
# REPORTING TASKS
# ================================

@celery_app.task(bind=True)
def generate_daily_report(self) -> TaskResult:
    """Generate daily procurement report"""
    try:
        from app.models import RequestOrder, PurchaseOrder, Supplier
        from app import db
        
        today = datetime.utcnow().date()
        yesterday = today - timedelta(days=1)
        
        # Query daily statistics
        requisitions_count = RequestOrder.query.filter(
            RequestOrder.created_at >= yesterday,
            RequestOrder.created_at < today
        ).count()
        
        pos_count = PurchaseOrder.query.filter(
            PurchaseOrder.created_at >= yesterday,
            PurchaseOrder.created_at < today
        ).count()
        
        total_po_amount = db.session.query(
            db.func.sum(PurchaseOrder.total_amount)
        ).filter(
            PurchaseOrder.created_at >= yesterday,
            PurchaseOrder.created_at < today
        ).scalar() or 0
        
        report_data = {
            'date': yesterday.isoformat(),
            'requisitions_created': requisitions_count,
            'purchase_orders_created': pos_count,
            'total_po_amount': float(total_po_amount),
            'generated_at': datetime.utcnow().isoformat()
        }
        
        # Store report
        store_report.delay('daily_procurement', report_data)
        
        # Send to stakeholders
        send_email_notification.delay(
            'daily_report',
            'management@company.com',
            report_data
        )
        
        return TaskResult(success=True, data=report_data)
        
    except Exception as exc:
        logger.error(f"Failed to generate daily report: {exc}")
        return TaskResult(success=False, error=str(exc))

@celery_app.task(bind=True)
def analyze_supplier_performance(self) -> TaskResult:
    """Analyze supplier performance over the past month"""
    try:
        from app.models import PurchaseOrder, Supplier
        from app import db
        
        # Get performance data for the last 30 days
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        
        supplier_performance = db.session.query(
            Supplier.supplier_id,
            Supplier.supplier_name_zh,
            db.func.count(PurchaseOrder.id).label('total_orders'),
            db.func.avg(
                db.func.extract('epoch', PurchaseOrder.delivery_date - PurchaseOrder.created_at) / 86400
            ).label('avg_delivery_days'),
            db.func.count(
                db.case([(PurchaseOrder.status == 'completed', 1)])
            ).label('completed_orders')
        ).join(
            PurchaseOrder, Supplier.supplier_id == PurchaseOrder.supplier_id
        ).filter(
            PurchaseOrder.created_at >= thirty_days_ago
        ).group_by(
            Supplier.supplier_id, Supplier.supplier_name_zh
        ).all()
        
        performance_data = []
        for performance in supplier_performance:
            completion_rate = (performance.completed_orders / performance.total_orders) if performance.total_orders > 0 else 0
            
            performance_data.append({
                'supplier_id': performance.supplier_id,
                'supplier_name': performance.supplier_name_zh,
                'total_orders': performance.total_orders,
                'avg_delivery_days': round(performance.avg_delivery_days or 0, 1),
                'completion_rate': round(completion_rate * 100, 1)
            })
        
        # Store analysis results
        analysis_result = {
            'analysis_date': datetime.utcnow().isoformat(),
            'period_days': 30,
            'supplier_performance': performance_data
        }
        
        store_report.delay('supplier_performance', analysis_result)
        
        return TaskResult(success=True, data=analysis_result)
        
    except Exception as exc:
        logger.error(f"Failed to analyze supplier performance: {exc}")
        return TaskResult(success=False, error=str(exc))

# ================================
# NOTIFICATION TASKS
# ================================

@celery_app.task(bind=True, rate_limit='10/m')
def send_email_notification(self, email_type: str, recipient: str, data: Dict[str, Any]) -> TaskResult:
    """Send email notification with rate limiting"""
    try:
        # Email templates
        templates = {
            'requisition_approved': {
                'subject': '請購單已核准 - {requisition_number}',
                'template': 'emails/requisition_approved.html'
            },
            'purchase_order_created': {
                'subject': '採購訂單 - {po_number}',
                'template': 'emails/purchase_order.html'
            },
            'delivery_reminder': {
                'subject': '交貨提醒 - {po_number}',
                'template': 'emails/delivery_reminder.html'
            },
            'daily_report': {
                'subject': '每日採購報告 - {date}',
                'template': 'emails/daily_report.html'
            }
        }
        
        if email_type not in templates:
            raise ValueError(f"Unknown email type: {email_type}")
        
        template_config = templates[email_type]
        
        # Format subject
        subject = template_config['subject'].format(**data)
        
        # Send email (mock implementation)
        logger.info(f"Sending {email_type} email to {recipient}: {subject}")
        
        # In real implementation, use Flask-Mail or similar
        # mail.send(Message(
        #     subject=subject,
        #     recipients=[recipient],
        #     html=render_template(template_config['template'], **data)
        # ))
        
        return TaskResult(
            success=True,
            data={'email_type': email_type, 'recipient': recipient}
        )
        
    except Exception as exc:
        logger.error(f"Failed to send email notification: {exc}")
        return TaskResult(success=False, error=str(exc))

@celery_app.task(bind=True)
def send_delivery_reminders(self) -> TaskResult:
    """Send delivery reminders for overdue purchase orders"""
    try:
        from app.models import PurchaseOrder
        
        # Find overdue purchase orders
        today = datetime.utcnow().date()
        overdue_pos = PurchaseOrder.query.filter(
            PurchaseOrder.expected_delivery_date < today,
            PurchaseOrder.status.in_(['confirmed', 'in_transit']),
            PurchaseOrder.delivery_reminder_sent.is_(False)
        ).all()
        
        reminder_count = 0
        for po in overdue_pos:
            # Send reminder
            send_email_notification.delay(
                'delivery_reminder',
                po.supplier.supplier_email,
                {
                    'po_number': po.po_number,
                    'expected_date': po.expected_delivery_date.isoformat(),
                    'days_overdue': (today - po.expected_delivery_date).days
                }
            )
            
            # Mark reminder as sent
            po.delivery_reminder_sent = True
            reminder_count += 1
        
        from app import db
        db.session.commit()
        
        return TaskResult(
            success=True,
            data={'reminders_sent': reminder_count}
        )
        
    except Exception as exc:
        logger.error(f"Failed to send delivery reminders: {exc}")
        return TaskResult(success=False, error=str(exc))

# ================================
# MAINTENANCE TASKS
# ================================

@celery_app.task(bind=True)
def cleanup_expired_sessions(self) -> TaskResult:
    """Clean up expired user sessions"""
    try:
        import redis
        
        redis_client = redis.from_url(os.environ.get('REDIS_URL', 'redis://redis-cluster:6379/0'))
        
        # Get all session keys
        session_keys = redis_client.keys('session:*')
        
        expired_count = 0
        for key in session_keys:
            try:
                # Check if session is expired
                ttl = redis_client.ttl(key)
                if ttl == -1:  # No expiration set
                    # Delete sessions older than 24 hours
                    redis_client.expire(key, 86400)
                elif ttl == -2:  # Key doesn't exist
                    expired_count += 1
            except redis.RedisError:
                continue
        
        return TaskResult(
            success=True,
            data={'expired_sessions_cleaned': expired_count}
        )
        
    except Exception as exc:
        logger.error(f"Failed to cleanup expired sessions: {exc}")
        return TaskResult(success=False, error=str(exc))

@celery_app.task(bind=True)
def backup_critical_data(self) -> TaskResult:
    """Backup critical business data"""
    try:
        from app.models import RequestOrder, PurchaseOrder, Supplier, User
        from app import db
        
        # Create backup data
        backup_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'users_count': User.query.count(),
            'suppliers_count': Supplier.query.count(),
            'requisitions_count': RequestOrder.query.count(),
            'purchase_orders_count': PurchaseOrder.query.count()
        }
        
        # Store backup metadata
        store_report.delay('backup_metadata', backup_data)
        
        logger.info(f"Backup completed: {backup_data}")
        
        return TaskResult(success=True, data=backup_data)
        
    except Exception as exc:
        logger.error(f"Failed to backup critical data: {exc}")
        return TaskResult(success=False, error=str(exc))

# ================================
# UTILITY TASKS
# ================================

@celery_app.task(bind=True)
def store_report(self, report_type: str, data: Dict[str, Any]) -> TaskResult:
    """Store report data"""
    try:
        # In real implementation, store in database or file system
        logger.info(f"Storing {report_type} report: {json.dumps(data, indent=2)}")
        
        return TaskResult(success=True, data={'report_type': report_type})
        
    except Exception as exc:
        logger.error(f"Failed to store report: {exc}")
        return TaskResult(success=False, error=str(exc))

@celery_app.task(bind=True)
def log_audit_event(self, event_type: str, data: Dict[str, Any]) -> TaskResult:
    """Log audit event"""
    try:
        audit_data = {
            'event_type': event_type,
            'timestamp': datetime.utcnow().isoformat(),
            'data': data
        }
        
        logger.info(f"Audit event: {json.dumps(audit_data)}")
        
        return TaskResult(success=True, data=audit_data)
        
    except Exception as exc:
        logger.error(f"Failed to log audit event: {exc}")
        return TaskResult(success=False, error=str(exc))

# ================================
# TASK MANAGEMENT UTILITIES
# ================================

class TaskManager:
    """Task management utilities"""
    
    @staticmethod
    def get_task_status(task_id: str) -> Dict[str, Any]:
        """Get task status and result"""
        result = AsyncResult(task_id, app=celery_app)
        
        return {
            'task_id': task_id,
            'status': result.status,
            'result': result.result,
            'traceback': result.traceback,
            'successful': result.successful(),
            'failed': result.failed()
        }
    
    @staticmethod
    def cancel_task(task_id: str) -> bool:
        """Cancel a running task"""
        try:
            celery_app.control.revoke(task_id, terminate=True)
            return True
        except Exception as e:
            logger.error(f"Failed to cancel task {task_id}: {e}")
            return False
    
    @staticmethod
    def get_active_tasks() -> List[Dict[str, Any]]:
        """Get list of active tasks"""
        try:
            inspect = celery_app.control.inspect()
            active_tasks = inspect.active()
            
            if active_tasks:
                return [
                    {
                        'worker': worker,
                        'tasks': tasks
                    }
                    for worker, tasks in active_tasks.items()
                ]
            return []
        except Exception as e:
            logger.error(f"Failed to get active tasks: {e}")
            return []
    
    @staticmethod
    def get_queue_stats() -> Dict[str, Any]:
        """Get queue statistics"""
        try:
            inspect = celery_app.control.inspect()
            stats = inspect.stats()
            
            return stats or {}
        except Exception as e:
            logger.error(f"Failed to get queue stats: {e}")
            return {}

# Global task manager instance
task_manager = TaskManager()