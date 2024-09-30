import { Component, EventEmitter, Input, Output } from '@angular/core';

@Component({
  selector: 'toggle-on-off',
  templateUrl: './toggle-on-off.component.html',
  styleUrls: ['./toggle-on-off.component.css']
})
export class ToggleOnOffComponent {
  @Input() id: string = '0'; // Identifikator für den Schalter
  @Input() isChecked: boolean | undefined; // Default-Wert zu false geändert

  @Output() change = new EventEmitter<{id: string, checked: boolean}>(); // Sendet ein Objekt mit id und checked status

  toggleCheck() {
    this.isChecked = !this.isChecked;
    this.change.emit({id: this.id, checked: this.isChecked}); // Emitting the current state along with the id
  }
}
