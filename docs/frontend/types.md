# Interfaces TypeScript — `src/types/index.ts`

## Usuarios y Autenticación

```typescript
interface User {
  id: number;
  email: string;
  full_name: string;
  role: 'admin' | 'coordinador' | 'participante';
  is_active: boolean;
  is_staff: boolean;
}

interface AuthTokens {
  access: string;
  refresh: string;
}

interface LoginResponse {
  access: string;
  refresh: string;
  user: { id, email, full_name, role?, is_staff? };
}
```

## Participantes

```typescript
interface Participant {
  id: number;
  document_id: string;
  first_name: string;
  last_name: string;
  full_name: string;       // computado
  email: string;
  phone: string;
  is_active: boolean;
  is_deleted: boolean;
  deleted_at: string | null;
  deleted_by: number | null;
  deleted_by_detail: { id, full_name, email } | null;
  created_by: number;
  created_at: string;
  updated_at: string;
}
```

## Eventos

```typescript
interface Event {
  id: number;
  category: number | null;
  category_name?: string;
  instructor?: number;
  instructor_name?: string | null;
  name: string;
  description: string;
  event_date: string;
  end_date: string | null;
  duration_hours: number | null;
  location: string;
  status: 'draft' | 'active' | 'finished' | 'cancelled';
  status_display?: string;
  template?: number;
  template_name?: string | null;
  font_color?: string;
  name_font_size?: number;
  name_x?: number;
  name_y?: number;
  is_deleted: boolean;
  // ... timestamps
}
```

## Certificados

```typescript
interface Certificate {
  id: number;
  participant: { id, full_name, email, phone? };
  event: { id, name, event_date?, end_date?, description?, location?, duration_hours?, instructor_name?, category? };
  template?: number;
  status: 'pending' | 'generated' | 'sent' | 'failed';
  status_display?: string;
  verification_code: string;
  pdf_url?: string;
  issued_at: string;
  expires_at?: string;
  is_expired?: boolean;
}

interface CertificateDetail extends Certificate {
  delivery_history?: DeliveryLog[];
  last_delivery?: DeliveryLog | null;
  has_delivery_attempts?: boolean;
}
```

## Entregas

```typescript
interface DeliveryLog {
  id: number;
  certificate: number;
  delivery_method: 'email' | 'whatsapp' | 'link';
  delivery_method_display: string;
  recipient: string;
  status: 'success' | 'error' | 'pending';
  status_display: string;
  error_message?: string;
  sent_at: string;
  is_successful: boolean;
  is_failed: boolean;
  is_pending: boolean;
}
```

## Instructores

```typescript
interface Instructor {
  id: number;
  full_name: string;
  email: string;
  phone: string;
  specialty: string;
  bio: string;
  signature_url: string;
  signature_image?: string | null;
}
```

## Plantillas

```typescript
interface Template {
  id: number;
  name: string;
  category: string;
  background_image: number | null;
  background_url: string;
  layout_config: Record<string, unknown>;
  is_active: boolean;
  font_color?: string;
  font_family?: string;
  font_size?: number;
  x_coord?: number;
  y_coord?: number;
  // ... timestamps
}
```

## Bulk / Importación

```typescript
interface BulkImportResult {
  processing_timestamp: string;
  total_rows: number;
  successful: number;
  failed: number;
  success_rate: string;
  errors: Array<{ row, field?, message, data? }>;
  created_certificates: number[];
  data_preview?: Array<Record<string, unknown>>;
  summary: string;
}

interface ExcelPreview {
  success: boolean;
  row_count: number;
  columns: string[];
  data: Array<Record<string, unknown>>;
}
```

## Auxiliares

```typescript
interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

interface DashboardStats {
  total_certificates: number;
  pending_certificates: number;
  generated_certificates: number;
  sent_certificates: number;
  failed_certificates: number;
  active_events: number;
  total_participants: number;
}

interface EnrolledParticipant {
  enrollment_id: number;
  participant_id: number;
  participant_name: string;
  participant_email: string;
  attendance: boolean;
  certificate_id: number | null;
  certificate_status: string | null;
  has_certificate: boolean;
}
```
