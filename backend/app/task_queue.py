"""
Task Queue Manager for AI-powered document processing
"""
import asyncio
import uuid
from datetime import datetime
from enum import Enum
from typing import Dict, Optional, List, Any
from dataclasses import dataclass, asdict
import logging

logger = logging.getLogger(__name__)

class TaskStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class TaskStep(str, Enum):
    UPLOAD_RECEIVED = "upload_received"
    DOCUMENT_LOADING = "document_loading"
    TEXT_EXTRACTION = "text_extraction"
    LLM_PROCESSING = "llm_processing"
    DATA_VALIDATION = "data_validation"
    SAVING_RESULTS = "saving_results"
    COMPLETED = "completed"

@dataclass
class TaskUpdate:
    task_id: str
    status: TaskStatus
    current_step: TaskStep
    progress: int  # 0-100
    message: str
    timestamp: datetime
    error_message: Optional[str] = None
    result_count: Optional[int] = None
    
    def to_dict(self):
        return {
            **asdict(self),
            'timestamp': self.timestamp.isoformat()
        }

class TaskQueue:
    def __init__(self):
        self.tasks: Dict[str, TaskUpdate] = {}
        self.subscribers: Dict[str, List[asyncio.Queue]] = {}
    
    def create_task(self, filename: str, use_llm: bool = False) -> str:
        """Create a new task and return task ID"""
        task_id = str(uuid.uuid4())
        initial_update = TaskUpdate(
            task_id=task_id,
            status=TaskStatus.PENDING,
            current_step=TaskStep.UPLOAD_RECEIVED,
            progress=0,
            message=f"Upload received: {filename}",
            timestamp=datetime.now()
        )
        self.tasks[task_id] = initial_update
        logger.info(f"Created task {task_id} for {filename} (LLM: {use_llm})")
        return task_id
    
    async def update_task(
        self,
        task_id: str,
        status: Optional[TaskStatus] = None,
        current_step: Optional[TaskStep] = None,
        progress: Optional[int] = None,
        message: Optional[str] = None,
        error_message: Optional[str] = None,
        result_count: Optional[int] = None
    ):
        """Update task status and notify subscribers"""
        if task_id not in self.tasks:
            logger.warning(f"Task {task_id} not found")
            return
        
        current_task = self.tasks[task_id]
        
        # Update fields that are provided
        updated_task = TaskUpdate(
            task_id=task_id,
            status=status or current_task.status,
            current_step=current_step or current_task.current_step,
            progress=progress if progress is not None else current_task.progress,
            message=message or current_task.message,
            timestamp=datetime.now(),
            error_message=error_message,
            result_count=result_count
        )
        
        self.tasks[task_id] = updated_task
        
        # Notify subscribers
        await self._notify_subscribers(task_id, updated_task)
        
        logger.info(f"Task {task_id} updated: {updated_task.status} - {updated_task.message}")
    
    async def _notify_subscribers(self, task_id: str, update: TaskUpdate):
        """Notify all subscribers of task updates"""
        if task_id in self.subscribers:
            disconnected_queues = []
            for queue in self.subscribers[task_id]:
                try:
                    await asyncio.wait_for(queue.put(update.to_dict()), timeout=1.0)
                except asyncio.TimeoutError:
                    disconnected_queues.append(queue)
                except Exception as e:
                    logger.warning(f"Failed to notify subscriber: {e}")
                    disconnected_queues.append(queue)
            
            # Remove disconnected queues
            for queue in disconnected_queues:
                self.subscribers[task_id].remove(queue)
                
            # Clean up empty subscriber lists
            if not self.subscribers[task_id]:
                del self.subscribers[task_id]
    
    def subscribe_to_task(self, task_id: str) -> asyncio.Queue:
        """Subscribe to task updates"""
        if task_id not in self.subscribers:
            self.subscribers[task_id] = []
        
        queue = asyncio.Queue()
        self.subscribers[task_id].append(queue)
        
        return queue
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get current task status"""
        if task_id in self.tasks:
            return self.tasks[task_id].to_dict()
        return None
    
    def get_all_tasks(self) -> List[Dict[str, Any]]:
        """Get all task statuses"""
        return [task.to_dict() for task in self.tasks.values()]
    
    def cleanup_completed_tasks(self, max_age_hours: int = 24):
        """Clean up old completed tasks"""
        cutoff_time = datetime.now().timestamp() - (max_age_hours * 3600)
        
        tasks_to_remove = []
        for task_id, task in self.tasks.items():
            if (task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED] and 
                task.timestamp.timestamp() < cutoff_time):
                tasks_to_remove.append(task_id)
        
        for task_id in tasks_to_remove:
            del self.tasks[task_id]
            if task_id in self.subscribers:
                del self.subscribers[task_id]
        
        if tasks_to_remove:
            logger.info(f"Cleaned up {len(tasks_to_remove)} old tasks")

# Global task queue instance
task_queue = TaskQueue()
