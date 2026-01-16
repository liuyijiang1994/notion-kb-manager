// Standard API response format
export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: {
    code: string;
    message: string;
    details?: any;
  };
  timestamp: string;
}

// Pagination
export interface Pagination {
  total: number;
  page: number;
  limit: number;
  total_pages: number;
}

export interface PaginatedResponse<T> {
  items: T[];
  pagination: Pagination;
}

// Task types
export interface Task {
  id: number;
  type: string;
  status: 'pending' | 'queued' | 'running' | 'completed' | 'failed' | 'cancelled';
  progress: number;
  total_items: number;
  completed_items: number;
  failed_items: number;
  created_at: string;
  started_at?: string;
  completed_at?: string;
  config?: Record<string, any>;
  error_message?: string;
}

export interface TaskItem {
  id: number;
  task_id: number;
  item_id: number;
  item_type: string;
  status: 'pending' | 'completed' | 'failed';
  error_message?: string;
  result?: any;
  created_at: string;
  completed_at?: string;
}

// Monitoring types
export interface SystemHealth {
  redis: string;
  redis_version?: string;
  workers: {
    total: number;
    active: number;
    idle: number;
    busy: number;
  };
  queues_healthy: boolean;
  queues: Record<string, {
    healthy: boolean;
    pending: number;
  }>;
}

export interface WorkerInfo {
  name: string;
  state: 'idle' | 'busy' | 'suspended';
  queues: string[];
  current_job?: string;
  success_count: number;
  failed_count: number;
  birth_date?: string;
}

export interface QueueInfo {
  name: string;
  pending: number;
  running: number;
  finished: number;
  failed: number;
  scheduled: number;
  total: number;
}

export interface Statistics {
  total_tasks: number;
  running_tasks: number;
  completed_tasks: number;
  failed_tasks: number;
  total_links: number;
  parsed_links: number;
  ai_processed_links: number;
  notion_imported_links: number;
}

// Link types
export interface Link {
  id: number;
  url: string;
  title?: string;
  status: string;
  created_at: string;
  updated_at: string;
}

// Content types
export interface Content {
  id: number;
  link_id: number;
  title: string;
  text_content?: string;
  html_content?: string;
  markdown_content?: string;
  summary?: string;
  category?: string;
  sentiment?: string;
  keywords?: string[];
  created_at: string;
  updated_at: string;
}

// Configuration types
export interface AIModel {
  id: number;
  name: string;
  provider: string;
  model_id: string;
  is_default: boolean;
  capabilities: string[];
  created_at: string;
}

export interface NotionConfig {
  api_key?: string;
  database_id?: string;
  is_configured: boolean;
}

// Auth types
export interface LoginRequest {
  username: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  expires_in: number;
  user: {
    id: string;
    username: string;
    roles: string[];
    is_admin: boolean;
  };
}

export interface User {
  id: string;
  username: string;
  roles: string[];
  is_admin: boolean;
}

// Import types
export interface ImportTask {
  id: number;
  url?: string;
  status: 'pending' | 'completed' | 'failed';
  created_at: string;
  completed_at?: string;
  total_links: number;
  processed_links: number;
}

export interface Bookmark {
  url: string;
  title: string;
}

// Configuration types for settings
export interface Config {
  notion_api_key?: string;
  openai_api_key?: string;
  openai_base_url?: string;
  openai_model?: string;
  temperature?: number;
  max_tokens?: number;
  quality_threshold?: number;
  batch_size?: number;
  auto_export?: boolean;
  retry_attempts?: number;
  timeout?: number;
}

// Workflow types
export interface WorkflowResponse {
  import_task_id: number;
  parsing_job_id?: string;
  ai_job_id?: string;
  notion_job_id?: string;
  status: string;
}
