import { Component, Output, EventEmitter } from '@angular/core';

@Component({
  selector: 'toggle-switch',
  templateUrl: './toggle-switch.component.html',
  styleUrls: ['./toggle-switch.component.css']
})
export class ToggleSwitchComponent {
  @Output() toggleChanged = new EventEmitter<boolean>();
  isChecked = false;

  onToggleChange(): void {
    this.toggleChanged.emit(this.isChecked);
  }
}
