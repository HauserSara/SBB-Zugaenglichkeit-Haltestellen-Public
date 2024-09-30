import { BreakpointObserver, MediaMatcher , Breakpoints} from '@angular/cdk/layout';
import { CommonModule } from '@angular/common';
import { AfterViewInit, CUSTOM_ELEMENTS_SCHEMA, Component, OnDestroy } from '@angular/core';
import { FormControl, FormsModule, ReactiveFormsModule } from '@angular/forms';
import { SbbCheckboxModule } from '@sbb-esta/angular/checkbox';
import { SbbOptionModule } from '@sbb-esta/angular/core';
import { FakeMediaMatcher } from '@sbb-esta/angular/core/testing';
import { SbbFormField, SbbLabel } from '@sbb-esta/angular/form-field';
import { SbbIconModule } from '@sbb-esta/angular/icon';
import { SbbSelect } from '@sbb-esta/angular/select';
import { SbbSidebarModule } from '@sbb-esta/angular/sidebar';
import { Subject } from 'rxjs';
import { startWith, takeUntil } from 'rxjs/operators';
import { RouterModule } from '@angular/router';

/**
 * @title Icon Sidebar
 * @order 20
 */
@Component({
  selector: 'sbb-icon-sidebar-example',
  templateUrl: 'icon-sidebar-example.html',
  styleUrls: ['icon-sidebar-example.css'],
  providers: [
    FakeMediaMatcher,
    { provide: MediaMatcher, useExisting: FakeMediaMatcher },
    BreakpointObserver
  ],
  standalone: true,
  imports: [
    SbbSidebarModule,
    SbbIconModule,
    SbbCheckboxModule,
    FormsModule,
    ReactiveFormsModule,
    SbbOptionModule,
    SbbSelect,
    SbbFormField,
    CommonModule,
    RouterModule,
    SbbLabel
  ],
  schemas: [CUSTOM_ELEMENTS_SCHEMA]
})
export class IconSidebarExample implements AfterViewInit, OnDestroy {
  expanded = false;
  position = new FormControl<'start' | 'end'>('start', { nonNullable: true });
  simulateMobile = new FormControl(false, { initialValueIsDefault: true });
  private _destroyed = new Subject<void>();

  constructor(private breakpointObserver: BreakpointObserver) {}


  ngAfterViewInit(): void {
    this.breakpointObserver.observe([
      Breakpoints.Handset, // Überwacht Änderungen in der Fensterbreite für mobile Geräte
      Breakpoints.Small // Sie können auch andere Breakpoints hinzufügen, je nach Ihren Anforderungen
    ]).pipe(
      takeUntil(this._destroyed)
    ).subscribe(result => {
      if (result.matches) {
        this.simulateMobile.setValue(true); // Setzen Sie die simulateMobile-Steuerung auf true, wenn der Bildschirm klein ist
      } else {
        this.simulateMobile.setValue(false); // Setzen Sie die simulateMobile-Steuerung auf false, wenn der Bildschirm groß ist
      }
    });
  }


  ngOnDestroy(): void {
    this._destroyed.next();
    this._destroyed.complete();
  }
}
