import { Component, OnInit } from '@angular/core';

@Component({
  selector: 'app-controls',
  templateUrl: './controls.component.html',
  styleUrls: ['./controls.component.css']
})
export class ControlsComponent implements OnInit {
  accessibility!: boolean; // Using non-null assertion
  guidanceMarkings!: boolean;

  ngOnInit() {
    // Load the initial values from session storage if available
    this.accessibility = JSON.parse(sessionStorage.getItem('accessibility') || 'true');
    this.guidanceMarkings = JSON.parse(sessionStorage.getItem('guidancemarkings') || 'true');
  }

  onToggleChange(event: {id: string, checked: boolean}) {
    if (event.id === 'accessibility') {
      this.accessibility = event.checked;
      console.log('Accessibility Toggle status:', event.checked);
      sessionStorage.setItem('accessibility', JSON.stringify(event.checked));
    } else if (event.id === 'guidancemarkings') {
      this.guidanceMarkings = event.checked;
      console.log('Guidance Markings Toggle status:', event.checked);
      sessionStorage.setItem('guidancemarkings', JSON.stringify(event.checked));
    }
  }
}
