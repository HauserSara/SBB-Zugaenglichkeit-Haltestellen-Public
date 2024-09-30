import { Component } from '@angular/core';
import { FormControl } from '@angular/forms';
import { SbbDateInputEvent } from '@sbb-esta/angular/datepicker';

/**
 * @title Basic Inputs
 * @order 10
 */
@Component({
  selector: 'app-navigate',
  templateUrl: './navigate.component.html',
  styleUrl: './navigate.component.css'
})
export class NavigateComponent {
  date = new FormControl(new Date());
  readonly = new FormControl(false);
  toggle = new FormControl(true);
  arrows = new FormControl(false);
  disabled = new FormControl(false);

  dateChangeEvent($event: SbbDateInputEvent<Date>) {
    console.log('DATE_CHANGED', $event);
  }

  dateInputEvent($event: SbbDateInputEvent<Date>) {
    console.log('DATE_INPUT', $event);
  }
}

