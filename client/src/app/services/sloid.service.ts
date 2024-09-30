import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class SloidService {
  private apiUrl = 'http://localhost:8000/check-sloid'; // URL zum Backend-Endpoint

  constructor(private http: HttpClient) { }

  getSloids(sloid: string): Observable<any> {
    return this.http.get(`${this.apiUrl}/${sloid}`);
  }
}
