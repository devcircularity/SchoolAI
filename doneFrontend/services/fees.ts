// services/fees.ts
import { api } from './api'

type CreateInvoiceRequest = {
  student_id: number
  amount: number
  description?: string
}

type CreateInvoiceByAdmissionRequest = {
  admission_no: string
  amount: number
  description?: string
}

type CreatePaymentRequest = {
  invoice_id: number
  amount: number
}

type Invoice = {
  id: number
  student_id: number
  amount: number
  status: 'paid' | 'unpaid'
  description?: string
  school_id: number
}

type Payment = {
  id: number
  invoice_id: number
  amount: number
  school_id: number
}

export const feeService = {
  async listInvoices() {
    const { data } = await api.get('/api/fees/invoices')
    return data as Invoice[]
  },
  
  async createInvoice(body: CreateInvoiceRequest) {
    const { data } = await api.post('/api/fees/invoices', body)
    return data as Invoice
  },
  
  async createInvoiceByAdmission(body: CreateInvoiceByAdmissionRequest) {
    const { data } = await api.post('/api/fees/invoices/by-admission', body)
    return data as Invoice
  },
  
  async createPayment(body: CreatePaymentRequest) {
    const { data } = await api.post('/api/fees/payments', body)
    return data as Payment
  }
}

// Export individual functions for convenience
export const listInvoices = feeService.listInvoices
export const createInvoice = feeService.createInvoice
export const createInvoiceByAdmission = feeService.createInvoiceByAdmission
export const recordPayment = feeService.createPayment