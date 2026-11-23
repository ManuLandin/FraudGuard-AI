export type Risk = 'bajo' | 'medio' | 'alto' | 'pendiente'
export interface Transaction { id: number; batch_id: number; transaction_id: string; amount_cents: number; timestamp: string; account_id: string | null; anomaly_score: number | null; risk_level: Exclude<Risk, 'pendiente'> | null; model_created_at: string | null }
export interface Batch { id: number; filename: string; row_count: number; created_at: string }
export interface Summary { total: number; analyzed: number; pending: number; anomalies: number; anomaly_percentage: number | null; amount_cents: string; distribution: {name: string; count: number}[]; daily: {date: string; count: number; amount_cents: string}[]; amount_distribution: {name: string; count: number}[] }
export interface TransactionPage {items: Transaction[]; total: number; page: number; page_size: number}
export interface ModelStatus {ready: boolean; created_at?: string; fit_rows?: number; calibration_rows?: number; message?: string}
export interface DashboardData {summary: Summary; transactions: TransactionPage; batches: Batch[]; model: ModelStatus}
