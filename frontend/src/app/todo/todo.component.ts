import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

@Component({
  selector: 'app-todo',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './todo.component.html',
  styleUrls: ['./todo.component.css']
})
export class TodoComponent {
  // Define tasks with some example data
  tasks = [
    {
      date: '2025-05-28',
      entity: 'Company ABC',
      time: '10:00 AM',
      contact: 'John Doe',
      notes: 'Follow-up call',
      status: 'Open'
    },
    {
      date: '2025-05-27',
      entity: 'Company XYZ',
      time: '2:00 PM',
      contact: 'Jane Smith',
      notes: '',
      status: 'Closed'
    }
  ];
}
