# Event-Driven Architecture Implementation
# Comprehensive event management system with Redis Streams

import json
import uuid
import redis
import logging
import asyncio
from datetime import datetime
from typing import Dict, List, Callable, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

class EventType(Enum):
    """Enumeration of business events in the ERP system"""
    # Requisition Events
    REQUISITION_CREATED = "requisition.created"
    REQUISITION_UPDATED = "requisition.updated"
    REQUISITION_SUBMITTED = "requisition.submitted"
    REQUISITION_APPROVED = "requisition.approved"
    REQUISITION_REJECTED = "requisition.rejected"
    REQUISITION_CANCELLED = "requisition.cancelled"
    
    # Purchase Order Events
    PURCHASE_ORDER_CREATED = "purchase_order.created"
    PURCHASE_ORDER_SENT = "purchase_order.sent"
    PURCHASE_ORDER_CONFIRMED = "purchase_order.confirmed"
    PURCHASE_ORDER_UPDATED = "purchase_order.updated"
    PURCHASE_ORDER_CANCELLED = "purchase_order.cancelled"
    
    # Supplier Events
    SUPPLIER_CREATED = "supplier.created"
    SUPPLIER_UPDATED = "supplier.updated"
    SUPPLIER_ACTIVATED = "supplier.activated"
    SUPPLIER_DEACTIVATED = "supplier.deactivated"
    
    # Delivery Events
    DELIVERY_SCHEDULED = "delivery.scheduled"
    DELIVERY_IN_TRANSIT = "delivery.in_transit"
    DELIVERY_DELIVERED = "delivery.delivered"
    DELIVERY_DELAYED = "delivery.delayed"
    
    # Acceptance Events
    GOODS_RECEIVED = "goods.received"
    GOODS_INSPECTED = "goods.inspected"
    GOODS_ACCEPTED = "goods.accepted"
    GOODS_REJECTED = "goods.rejected"
    
    # Inventory Events
    INVENTORY_UPDATED = "inventory.updated"
    INVENTORY_LOW_STOCK = "inventory.low_stock"
    INVENTORY_RESERVED = "inventory.reserved"
    INVENTORY_RELEASED = "inventory.released"
    
    # User Events
    USER_LOGIN = "user.login"
    USER_LOGOUT = "user.logout"
    USER_CREATED = "user.created"
    USER_UPDATED = "user.updated"
    
    # System Events
    SYSTEM_BACKUP = "system.backup"
    SYSTEM_MAINTENANCE = "system.maintenance"
    SYSTEM_ERROR = "system.error"


@dataclass
class Event:
    """Event data structure"""
    event_type: EventType
    data: Dict[str, Any]
    correlation_id: str
    timestamp: datetime
    source: str
    version: str = "1.0"
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for serialization"""
        return {
            'event_type': self.event_type.value,
            'data': self.data,
            'correlation_id': self.correlation_id,
            'timestamp': self.timestamp.isoformat(),
            'source': self.source,
            'version': self.version,
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Event':
        """Create event from dictionary"""
        return cls(
            event_type=EventType(data['event_type']),
            data=data['data'],
            correlation_id=data['correlation_id'],
            timestamp=datetime.fromisoformat(data['timestamp']),
            source=data['source'],
            version=data.get('version', '1.0'),
            metadata=data.get('metadata', {})
        )


class EventPublisher:
    """Event publisher using Redis Streams"""
    
    def __init__(self, redis_url: str):
        self.redis_client = redis.from_url(redis_url, decode_responses=True)
        self.stream_prefix = "events"
        
    def publish(self, event: Event) -> str:
        """
        Publish event to Redis Stream
        
        Args:
            event: Event to publish
            
        Returns:
            Message ID from Redis
        """
        try:
            stream_name = f"{self.stream_prefix}:{event.event_type.value}"
            event_data = event.to_dict()
            
            # Add event to stream
            message_id = self.redis_client.xadd(stream_name, event_data)
            
            # Log event for audit
            logger.info(f"Published event {event.event_type.value} with ID {message_id}")
            
            # Update event statistics
            self._update_event_stats(event.event_type)
            
            return message_id
            
        except redis.RedisError as e:
            logger.error(f"Failed to publish event {event.event_type.value}: {e}")
            raise
    
    def publish_business_event(self, event_type: EventType, data: Dict[str, Any], 
                             source: str, correlation_id: str = None) -> str:
        """
        Convenience method to publish business events
        
        Args:
            event_type: Type of event
            data: Event data
            source: Event source
            correlation_id: Optional correlation ID
            
        Returns:
            Message ID
        """
        event = Event(
            event_type=event_type,
            data=data,
            correlation_id=correlation_id or str(uuid.uuid4()),
            timestamp=datetime.utcnow(),
            source=source
        )
        
        return self.publish(event)
    
    def _update_event_stats(self, event_type: EventType):
        """Update event statistics"""
        stats_key = f"event_stats:{event_type.value}"
        current_date = datetime.utcnow().strftime('%Y-%m-%d')
        
        # Increment daily counter
        self.redis_client.hincrby(f"{stats_key}:daily", current_date, 1)
        
        # Increment total counter
        self.redis_client.incr(f"{stats_key}:total")
        
        # Set expiration for daily stats (keep 30 days)
        self.redis_client.expire(f"{stats_key}:daily", 30 * 24 * 3600)


class EventSubscriber:
    """Event subscriber with handler management"""
    
    def __init__(self, redis_url: str, consumer_group: str, consumer_name: str):
        self.redis_client = redis.from_url(redis_url, decode_responses=True)
        self.consumer_group = consumer_group
        self.consumer_name = consumer_name
        self.stream_prefix = "events"
        self.handlers: Dict[EventType, List[Callable]] = {}
        self.running = False
        
    def subscribe(self, event_type: EventType, handler: Callable[[Event], None]):
        """
        Subscribe to specific event type
        
        Args:
            event_type: Event type to subscribe to
            handler: Function to handle the event
        """
        if event_type not in self.handlers:
            self.handlers[event_type] = []
        
        self.handlers[event_type].append(handler)
        logger.info(f"Subscribed to {event_type.value} with handler {handler.__name__}")
    
    def create_consumer_groups(self):
        """Create consumer groups for all subscribed event types"""
        for event_type in self.handlers.keys():
            stream_name = f"{self.stream_prefix}:{event_type.value}"
            try:
                # Create consumer group (ignore if already exists)
                self.redis_client.xgroup_create(
                    stream_name, 
                    self.consumer_group, 
                    id='0', 
                    mkstream=True
                )
                logger.info(f"Created consumer group {self.consumer_group} for {stream_name}")
            except redis.ResponseError as e:
                if "BUSYGROUP" not in str(e):
                    logger.error(f"Failed to create consumer group: {e}")
    
    def start_consuming(self):
        """Start consuming events from subscribed streams"""
        self.running = True
        self.create_consumer_groups()
        
        logger.info(f"Starting event consumer {self.consumer_name} in group {self.consumer_group}")
        
        # Build stream mapping
        streams = {}
        for event_type in self.handlers.keys():
            stream_name = f"{self.stream_prefix}:{event_type.value}"
            streams[stream_name] = '>'
        
        try:
            while self.running:
                try:
                    # Read from streams
                    messages = self.redis_client.xreadgroup(
                        self.consumer_group,
                        self.consumer_name,
                        streams,
                        count=10,
                        block=1000  # Block for 1 second
                    )
                    
                    if messages:
                        self._process_messages(messages)
                        
                except redis.RedisError as e:
                    logger.error(f"Redis error while consuming: {e}")
                    asyncio.sleep(5)  # Wait before retrying
                    
                except KeyboardInterrupt:
                    logger.info("Received interrupt signal, stopping consumer")
                    break
                    
        finally:
            self.running = False
            logger.info("Event consumer stopped")
    
    def stop_consuming(self):
        """Stop consuming events"""
        self.running = False
    
    def _process_messages(self, messages):
        """Process received messages"""
        for stream, stream_messages in messages:
            # Extract event type from stream name
            event_type_str = stream.split(':')[-1]
            try:
                event_type = EventType(event_type_str)
            except ValueError:
                logger.warning(f"Unknown event type: {event_type_str}")
                continue
            
            for message_id, fields in stream_messages:
                try:
                    # Reconstruct event
                    event = Event.from_dict(fields)
                    
                    # Process with all handlers for this event type
                    handlers = self.handlers.get(event_type, [])
                    for handler in handlers:
                        try:
                            handler(event)
                            logger.debug(f"Successfully processed event {event.correlation_id} with {handler.__name__}")
                        except Exception as e:
                            logger.error(f"Handler {handler.__name__} failed for event {event.correlation_id}: {e}")
                    
                    # Acknowledge message
                    self.redis_client.xack(stream, self.consumer_group, message_id)
                    
                except Exception as e:
                    logger.error(f"Failed to process message {message_id}: {e}")


class EventOrchestrator:
    """Orchestrates complex business workflows using events"""
    
    def __init__(self, publisher: EventPublisher, subscriber: EventSubscriber):
        self.publisher = publisher
        self.subscriber = subscriber
        self.workflow_states: Dict[str, Dict] = {}
        
    def setup_procurement_workflow(self):
        """Set up the complete procurement workflow"""
        # Subscribe to requisition events
        self.subscriber.subscribe(EventType.REQUISITION_CREATED, self._handle_requisition_created)
        self.subscriber.subscribe(EventType.REQUISITION_APPROVED, self._handle_requisition_approved)
        
        # Subscribe to purchase order events
        self.subscriber.subscribe(EventType.PURCHASE_ORDER_CREATED, self._handle_po_created)
        self.subscriber.subscribe(EventType.PURCHASE_ORDER_SENT, self._handle_po_sent)
        
        # Subscribe to delivery events
        self.subscriber.subscribe(EventType.GOODS_RECEIVED, self._handle_goods_received)
        self.subscriber.subscribe(EventType.GOODS_ACCEPTED, self._handle_goods_accepted)
    
    def _handle_requisition_created(self, event: Event):
        """Handle requisition creation"""
        requisition_id = event.data.get('requisition_id')
        correlation_id = event.correlation_id
        
        # Initialize workflow state
        self.workflow_states[correlation_id] = {
            'requisition_id': requisition_id,
            'status': 'requisition_created',
            'created_at': event.timestamp,
            'steps_completed': ['requisition_created']
        }
        
        # Send notification to procurement team
        self.publisher.publish_business_event(
            EventType.SYSTEM_ERROR,  # Using as notification event
            {
                'type': 'notification',
                'message': f'New requisition {requisition_id} created',
                'recipients': ['procurement_team']
            },
            source='workflow_orchestrator',
            correlation_id=correlation_id
        )
    
    def _handle_requisition_approved(self, event: Event):
        """Handle requisition approval"""
        correlation_id = event.correlation_id
        requisition_id = event.data.get('requisition_id')
        
        # Update workflow state
        if correlation_id in self.workflow_states:
            self.workflow_states[correlation_id]['status'] = 'requisition_approved'
            self.workflow_states[correlation_id]['steps_completed'].append('requisition_approved')
        
        # Trigger purchase order creation
        self.publisher.publish_business_event(
            EventType.PURCHASE_ORDER_CREATED,
            {
                'requisition_id': requisition_id,
                'auto_created': True,
                'created_by': 'system'
            },
            source='workflow_orchestrator',
            correlation_id=correlation_id
        )
    
    def _handle_po_created(self, event: Event):
        """Handle purchase order creation"""
        correlation_id = event.correlation_id
        po_id = event.data.get('po_id')
        
        # Update workflow state
        if correlation_id in self.workflow_states:
            self.workflow_states[correlation_id]['po_id'] = po_id
            self.workflow_states[correlation_id]['status'] = 'po_created'
            self.workflow_states[correlation_id]['steps_completed'].append('po_created')
    
    def _handle_po_sent(self, event: Event):
        """Handle purchase order sent to supplier"""
        correlation_id = event.correlation_id
        
        # Update workflow state
        if correlation_id in self.workflow_states:
            self.workflow_states[correlation_id]['status'] = 'po_sent'
            self.workflow_states[correlation_id]['steps_completed'].append('po_sent')
        
        # Schedule delivery reminder
        self._schedule_delivery_reminder(correlation_id, event.data)
    
    def _handle_goods_received(self, event: Event):
        """Handle goods received"""
        correlation_id = event.correlation_id
        
        # Update workflow state
        if correlation_id in self.workflow_states:
            self.workflow_states[correlation_id]['status'] = 'goods_received'
            self.workflow_states[correlation_id]['steps_completed'].append('goods_received')
    
    def _handle_goods_accepted(self, event: Event):
        """Handle goods acceptance - complete workflow"""
        correlation_id = event.correlation_id
        
        # Update workflow state
        if correlation_id in self.workflow_states:
            self.workflow_states[correlation_id]['status'] = 'workflow_completed'
            self.workflow_states[correlation_id]['steps_completed'].append('goods_accepted')
            self.workflow_states[correlation_id]['completed_at'] = datetime.utcnow()
        
        # Trigger payment process
        self.publisher.publish_business_event(
            EventType.SYSTEM_ERROR,  # Using as payment trigger
            {
                'type': 'payment_trigger',
                'po_id': event.data.get('po_id'),
                'amount': event.data.get('amount')
            },
            source='workflow_orchestrator',
            correlation_id=correlation_id
        )
    
    def _schedule_delivery_reminder(self, correlation_id: str, po_data: Dict):
        """Schedule delivery reminder"""
        # This would integrate with a task scheduler
        logger.info(f"Scheduled delivery reminder for correlation_id: {correlation_id}")
    
    def get_workflow_status(self, correlation_id: str) -> Optional[Dict]:
        """Get workflow status"""
        return self.workflow_states.get(correlation_id)


class EventStore:
    """Event store for audit and replay capabilities"""
    
    def __init__(self, redis_url: str):
        self.redis_client = redis.from_url(redis_url, decode_responses=True)
        self.store_key_prefix = "event_store"
    
    def store_event(self, event: Event):
        """Store event for audit purposes"""
        try:
            # Store in hash with correlation_id as key
            store_key = f"{self.store_key_prefix}:{event.correlation_id}"
            
            # Add event to the correlation's event list
            event_data = json.dumps(event.to_dict())
            self.redis_client.lpush(store_key, event_data)
            
            # Set expiration (keep for 1 year)
            self.redis_client.expire(store_key, 365 * 24 * 3600)
            
            # Index by event type for queries
            type_index_key = f"{self.store_key_prefix}:by_type:{event.event_type.value}"
            self.redis_client.zadd(
                type_index_key, 
                {event.correlation_id: event.timestamp.timestamp()}
            )
            
            # Index by date for cleanup
            date_index_key = f"{self.store_key_prefix}:by_date:{event.timestamp.strftime('%Y-%m-%d')}"
            self.redis_client.sadd(date_index_key, event.correlation_id)
            
        except redis.RedisError as e:
            logger.error(f"Failed to store event: {e}")
    
    def get_events_by_correlation(self, correlation_id: str) -> List[Event]:
        """Get all events for a correlation ID"""
        try:
            store_key = f"{self.store_key_prefix}:{correlation_id}"
            event_data_list = self.redis_client.lrange(store_key, 0, -1)
            
            events = []
            for event_data in event_data_list:
                event_dict = json.loads(event_data)
                events.append(Event.from_dict(event_dict))
            
            # Return in chronological order
            return sorted(events, key=lambda e: e.timestamp)
            
        except (redis.RedisError, json.JSONDecodeError) as e:
            logger.error(f"Failed to retrieve events: {e}")
            return []


# Global instances
event_publisher = None
event_subscriber = None
event_orchestrator = None
event_store = None

def init_event_system(redis_url: str, consumer_group: str, consumer_name: str):
    """Initialize the event system"""
    global event_publisher, event_subscriber, event_orchestrator, event_store
    
    event_publisher = EventPublisher(redis_url)
    event_subscriber = EventSubscriber(redis_url, consumer_group, consumer_name)
    event_orchestrator = EventOrchestrator(event_publisher, event_subscriber)
    event_store = EventStore(redis_url)
    
    # Set up workflows
    event_orchestrator.setup_procurement_workflow()
    
    return event_publisher, event_subscriber, event_orchestrator, event_store