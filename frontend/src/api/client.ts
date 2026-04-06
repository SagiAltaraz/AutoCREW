import { Task } from '../types';

const BASE_URL = 'http://localhost:8000/api';

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!res.ok) {
    const error = await res.text();
    throw new Error(error || `HTTP ${res.status}`);
  }
  return res.json();
}

export async function createTask(inputText: string): Promise<{ task_id: string; status: string }> {
  return request('/tasks', {
    method: 'POST',
    body: JSON.stringify({ input_text: inputText }),
  });
}

export async function getTask(taskId: string): Promise<Task> {
  return request(`/tasks/${taskId}`);
}

export async function listTasks(): Promise<Task[]> {
  return request('/tasks');
}
