import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HttpClient, HttpClientModule } from '@angular/common/http';
import { DomSanitizer, SafeHtml } from '@angular/platform-browser';

interface Task {
  _id?: string;
  task_time: string;
  entity_name: string;
  contact_person: string;
  phone: string;
  note?: string;
  status?: string;
  date?: string;
  task_type: string;
}

interface TaskDisplay {
  id: string;
  date: string;
  entity: string;
  time: string;
  contact: string;
  phone: string;
  notes: string;
  status: string;
  taskType: string;
}

@Component({
  selector: 'app-todo',
  standalone: true,
  imports: [CommonModule, FormsModule, HttpClientModule],
  templateUrl: './todo.component.html',
  styleUrls: ['./todo.component.css']
})
export class TodoComponent implements OnInit {
  showNewTaskForm = false;
  isSubmitting = false;
  tasks: TaskDisplay[] = [];
  sortField: string = '';
  sortDirection: 'asc' | 'desc' = 'asc';

  private apiUrl = 'https://task-list-web-app.onrender.com/tasks';

  hours = Array.from({ length: 12 }, (_, i) => (i + 1).toString().padStart(2, '0'));
  minutes = Array.from({ length: 60 }, (_, i) => i.toString().padStart(2, '0'));

  newTask = {
    date: '',
    entity: '',
    timeHour: '01',
    timeMinute: '00',
    timePeriod: 'AM',
    contact: '',
    phone: '',
    notes: '',
    status: 'Open',
    taskType: 'Call'
  };

  constructor(private http: HttpClient, private sanitizer: DomSanitizer) {}

  
  ngOnInit() {
    this.loadTasks();
  }

  openNewTaskForm() {
    this.showNewTaskForm = true;
  }

  cancelForm() {
    this.showNewTaskForm = false;
    this.resetForm();
  }

  sanitizeHtml(html: string): SafeHtml {
    return this.sanitizer.bypassSecurityTrustHtml(html);
  }

  private convertTo24Hour(hour: string, period: string): number {
    let hour24 = parseInt(hour, 10);
    if (period === 'PM' && hour24 !== 12) {
      hour24 += 12;
    } else if (period === 'AM' && hour24 === 12) {
      hour24 = 0;
    }
    return hour24;
  }

  private createTaskDateTime(): string {
    const hour24 = this.convertTo24Hour(this.newTask.timeHour, this.newTask.timePeriod);
    const minute = parseInt(this.newTask.timeMinute, 10);
    const taskDate = new Date(this.newTask.date);
    taskDate.setHours(hour24, minute, 0, 0);
    return taskDate.toISOString();
  }


  addTask() {
    if (
      !this.newTask.entity.trim() ||
      !this.newTask.contact.trim() ||
      !/^\d{10}$/.test(this.newTask.phone) ||
      !this.newTask.date ||
      !this.newTask.timeHour ||
      !this.newTask.timeMinute ||
      !this.newTask.timePeriod ||
      !this.newTask.taskType
    ) {
      alert('Please fill out all required fields correctly. Phone must be 10 digits.');
      return;
    }

    this.isSubmitting = true;
    const taskTime = this.createTaskDateTime();

    const payload = {
      entity_name: this.newTask.entity.trim(),
      task_type: this.newTask.taskType.trim(),
      contact_person: this.newTask.contact.trim(),
      phone_number: this.newTask.phone.trim(),
      task_time: taskTime,
      note: this.newTask.notes?.trim() || '',
      status: this.newTask.status.toLowerCase()
    };

    this.http.post(this.apiUrl, payload).subscribe({
      next: (response: any) => {
        const timeString = `${this.newTask.timeHour}:${this.newTask.timeMinute} ${this.newTask.timePeriod}`;

        const newLocalTask: TaskDisplay = {
          id: response.id,
          date: new Date(this.newTask.date).toLocaleDateString('en-GB'),
          entity: this.newTask.entity.trim(),
          time: timeString,
          contact: this.newTask.contact.trim(),
          phone: this.newTask.phone.trim(),
          notes: this.newTask.notes.trim(),
          status: this.newTask.status,
          taskType: this.newTask.taskType
        };

        this.tasks.unshift(newLocalTask);
        this.showNewTaskForm = false;
        this.resetForm();
        alert('Task created successfully!');
      },
      error: (error) => {
        console.error('Error creating task:', error);
        let errorMessage = 'Failed to create task. Please try again.';
        if (error.error && error.error.error) {
          errorMessage = error.error.error;
        }
        alert(errorMessage);
      },
      complete: () => {
        this.isSubmitting = false;
      }
    });
  }

  deleteTask(taskId: string) {
    if (confirm('Are you sure you want to delete this task?')) {
      this.http.delete(`${this.apiUrl}/${taskId}`).subscribe({
        next: () => {
          this.tasks = this.tasks.filter(task => task.id !== taskId);
          alert('Task deleted successfully!');
        },
        error: (error) => {
          console.error('Error deleting task:', error);
          alert('Failed to delete task.');
        }
      });
    }
  }

  private resetForm() {
    this.newTask = {
      date: '',
      entity: '',
      timeHour: '01',
      timeMinute: '00',
      timePeriod: 'AM',
      contact: '',
      phone: '',
      notes: '',
      status: 'Open',
      taskType: 'Call'
    };
  }

  loadTasks() {
    this.http.get<any[]>(this.apiUrl).subscribe({
      next: (response: any) => {
        const tasksData = Array.isArray(response) ? response : response.data || [];

        this.tasks = tasksData.map((task: Task) => {
          const taskDateObj = new Date(task.task_time);
          const hours24 = taskDateObj.getHours();
          const minutes = taskDateObj.getMinutes();
          const period = hours24 >= 12 ? 'PM' : 'AM';
          const displayHours = hours24 === 0 ? 12 : hours24 > 12 ? hours24 - 12 : hours24;
          const displayTime = `${displayHours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')} ${period}`;

          return {
            id: task._id || '',
            date: task.date ? new Date(task.date).toLocaleDateString('en-GB') : taskDateObj.toLocaleDateString('en-GB'),
            entity: task.entity_name || '',
            time: displayTime,
            contact: task.contact_person || '',
            phone: task.phone || '',
            notes: task.note || '',
            status: task.status?.toLowerCase() === 'open' ? 'Open' : 'Closed',
            taskType: task.task_type || 'Call'
          };
        });
      },
      error: (error) => {
        console.error('Error loading tasks:', error);
        alert('Failed to load tasks from server.');
      }
    });
  }


  
  sortTasks(field: string) {
    if (this.sortField === field) {
      this.sortDirection = this.sortDirection === 'asc' ? 'desc' : 'asc';
    } else {
      this.sortField = field;
      this.sortDirection = 'asc';
    }

    this.tasks.sort((a, b) => {
      let valueA: any = a[field as keyof TaskDisplay];
      let valueB: any = b[field as keyof TaskDisplay];

      if (field === 'date') {
        valueA = new Date(valueA.split('/').reverse().join('-')).getTime();
        valueB = new Date(valueB.split('/').reverse().join('-')).getTime();
      }

      if (field === 'status') {
        const statusRank = (val: string) => (val === 'Open' ? 0 : 1);
        return this.sortDirection === 'asc'
          ? statusRank(valueA) - statusRank(valueB)
          : statusRank(valueB) - statusRank(valueA);
      }

      valueA = typeof valueA === 'string' ? valueA.toLowerCase() : valueA;
      valueB = typeof valueB === 'string' ? valueB.toLowerCase() : valueB;

      if (valueA < valueB) return this.sortDirection === 'asc' ? -1 : 1;
      if (valueA > valueB) return this.sortDirection === 'asc' ? 1 : -1;
      return 0;
    });
  }
}


