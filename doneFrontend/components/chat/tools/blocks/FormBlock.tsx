// components/chat/tools/blocks/FormBlock.tsx - Fixed TypeScript types
'use client'
import { useState } from 'react'
import { FormBlock as FormBlockType, Action } from '../types'

// Extended field type to include all input types used
interface FormField {
  key: string
  label: string
  type: 'text' | 'textarea' | 'select' | 'date' | 'email' | 'number' | 'tel' | 'password' | 'checkbox' | 'radio'
  placeholder?: string
  required?: boolean
  options?: string[]
  help?: string
  min?: number
  max?: number
  step?: number
}

// Extended submit configuration to include label
interface SubmitConfig {
  endpoint: string
  method: "GET" | "POST" | "PUT" | "DELETE"
  label?: string
}

// Extended form configuration
interface FormConfig {
  title: string
  description?: string
  fields: FormField[]
  submit: SubmitConfig
}

// Override the FormBlockType to use our extended types
interface ExtendedFormBlockType {
  type: 'form'
  config: FormConfig
}

interface Props {
  block: ExtendedFormBlockType
  onAction?: (action: Action) => void
}

export function FormBlock({ block, onAction }: Props) {
  const [formData, setFormData] = useState<Record<string, any>>({})
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [errors, setErrors] = useState<Record<string, string>>({})

  const handleInputChange = (key: string, value: any) => {
    setFormData(prev => ({ ...prev, [key]: value }))
    // Clear error when user starts typing
    if (errors[key]) {
      setErrors(prev => ({ ...prev, [key]: '' }))
    }
  }

  const validateForm = () => {
    const newErrors: Record<string, string> = {}
    
    block.config.fields.forEach((field: FormField) => {
      const value = formData[field.key]
      
      if (field.required && (!value || (typeof value === 'string' && !value.trim()))) {
        newErrors[field.key] = `${field.label} is required`
      }
      
      // Add more validation rules as needed
      if (field.type === 'email' && value && !/\S+@\S+\.\S+/.test(value)) {
        newErrors[field.key] = 'Please enter a valid email address'
      }
      
      if (field.type === 'number' && value && isNaN(Number(value))) {
        newErrors[field.key] = 'Please enter a valid number'
      }

      if (field.type === 'tel' && value && !/^[\+]?[1-9][\d]{0,15}$/.test(value.replace(/\s/g, ''))) {
        newErrors[field.key] = 'Please enter a valid phone number'
      }
    })
    
    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!validateForm()) {
      return
    }
    
    setIsSubmitting(true)

    try {
      // In a real app, you'd make the API call here
      console.log('Form submission:', {
        endpoint: block.config.submit.endpoint,
        method: block.config.submit.method,
        data: formData
      })

      if (onAction) {
        onAction({
          type: 'mutation',
          endpoint: block.config.submit.endpoint,
          method: block.config.submit.method,
          data: formData
        } as any)
      }
      
      // Clear form on success
      setFormData({})
      
    } catch (error) {
      console.error('Form submission error:', error)
    } finally {
      setIsSubmitting(false)
    }
  }

  const renderField = (field: FormField) => {
    const value = formData[field.key] || ''
    const hasError = !!errors[field.key]

    const commonInputClass = `
      w-full px-3 py-2 sm:px-4 sm:py-2.5 
      border rounded-lg text-sm sm:text-base
      transition-colors duration-200
      ${hasError 
        ? 'border-red-300 dark:border-red-600 bg-red-50 dark:bg-red-900/10' 
        : 'border-neutral-300 dark:border-neutral-600 bg-white dark:bg-neutral-800'
      }
      focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500
      disabled:opacity-50 disabled:cursor-not-allowed
      placeholder:text-neutral-400 dark:placeholder:text-neutral-500
    `

    switch (field.type) {
      case 'textarea':
        return (
          <textarea
            className={`${commonInputClass} min-h-20 sm:min-h-24 resize-y`}
            placeholder={field.placeholder}
            value={value}
            onChange={(e) => handleInputChange(field.key, e.target.value)}
            required={field.required}
            disabled={isSubmitting}
            rows={3}
          />
        )

      case 'select':
        return (
          <select
            className={commonInputClass}
            value={value}
            onChange={(e) => handleInputChange(field.key, e.target.value)}
            required={field.required}
            disabled={isSubmitting}
          >
            <option value="">Select...</option>
            {field.options?.map((option: string) => (
              <option key={option} value={option}>{option}</option>
            ))}
          </select>
        )

      case 'date':
        return (
          <input
            type="date"
            className={commonInputClass}
            value={value}
            onChange={(e) => handleInputChange(field.key, e.target.value)}
            required={field.required}
            disabled={isSubmitting}
          />
        )

      case 'email':
        return (
          <input
            type="email"
            className={commonInputClass}
            placeholder={field.placeholder}
            value={value}
            onChange={(e) => handleInputChange(field.key, e.target.value)}
            required={field.required}
            disabled={isSubmitting}
          />
        )

      case 'number':
        return (
          <input
            type="number"
            className={commonInputClass}
            placeholder={field.placeholder}
            value={value}
            onChange={(e) => handleInputChange(field.key, e.target.value)}
            required={field.required}
            disabled={isSubmitting}
            min={field.min}
            max={field.max}
            step={field.step}
          />
        )

      case 'tel':
        return (
          <input
            type="tel"
            className={commonInputClass}
            placeholder={field.placeholder}
            value={value}
            onChange={(e) => handleInputChange(field.key, e.target.value)}
            required={field.required}
            disabled={isSubmitting}
          />
        )

      case 'password':
        return (
          <input
            type="password"
            className={commonInputClass}
            placeholder={field.placeholder}
            value={value}
            onChange={(e) => handleInputChange(field.key, e.target.value)}
            required={field.required}
            disabled={isSubmitting}
          />
        )

      case 'checkbox':
        return (
          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id={field.key}
              checked={value === true}
              onChange={(e) => handleInputChange(field.key, e.target.checked)}
              required={field.required}
              disabled={isSubmitting}
              className="rounded border-neutral-300 dark:border-neutral-600 text-blue-600 focus:ring-blue-500 focus:ring-offset-0"
            />
            <label 
              htmlFor={field.key}
              className="text-sm sm:text-base text-neutral-700 dark:text-neutral-300 cursor-pointer"
            >
              {field.placeholder || 'Check this box'}
            </label>
          </div>
        )

      case 'radio':
        return (
          <div className="space-y-2">
            {field.options?.map((option: string) => (
              <div key={option} className="flex items-center gap-2">
                <input
                  type="radio"
                  id={`${field.key}-${option}`}
                  name={field.key}
                  value={option}
                  checked={value === option}
                  onChange={(e) => handleInputChange(field.key, e.target.value)}
                  required={field.required}
                  disabled={isSubmitting}
                  className="text-blue-600 focus:ring-blue-500 focus:ring-offset-0"
                />
                <label 
                  htmlFor={`${field.key}-${option}`}
                  className="text-sm sm:text-base text-neutral-700 dark:text-neutral-300 cursor-pointer"
                >
                  {option}
                </label>
              </div>
            ))}
          </div>
        )

      default:
        return (
          <input
            type="text"
            className={commonInputClass}
            placeholder={field.placeholder}
            value={value}
            onChange={(e) => handleInputChange(field.key, e.target.value)}
            required={field.required}
            disabled={isSubmitting}
          />
        )
    }
  }

  return (
    <div className="bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-700 rounded-lg sm:rounded-xl shadow-sm">
      <div className="p-4 sm:p-6">
        <h3 className="text-lg sm:text-xl font-semibold text-neutral-900 dark:text-neutral-100 mb-4 sm:mb-6">
          {block.config.title}
        </h3>

        <form onSubmit={handleSubmit} className="space-y-4 sm:space-y-5">
          {/* Responsive grid for form fields */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 sm:gap-5">
            {block.config.fields.map((field: FormField) => {
              const isFullWidth = field.type === 'textarea' || field.type === 'checkbox' || field.type === 'radio'
              
              return (
                <div 
                  key={field.key}
                  className={isFullWidth ? 'sm:col-span-2' : ''}
                >
                  <label className="block text-sm sm:text-base font-medium text-neutral-700 dark:text-neutral-300 mb-1.5 sm:mb-2">
                    {field.label}
                    {field.required && <span className="text-red-500 ml-1">*</span>}
                  </label>
                  
                  {renderField(field)}
                  
                  {/* Error message */}
                  {errors[field.key] && (
                    <p className="mt-1 text-xs sm:text-sm text-red-600 dark:text-red-400">
                      {errors[field.key]}
                    </p>
                  )}
                  
                  {/* Help text */}
                  {field.help && !errors[field.key] && (
                    <p className="mt-1 text-xs sm:text-sm text-neutral-500 dark:text-neutral-400">
                      {field.help}
                    </p>
                  )}
                </div>
              )
            })}
          </div>

          {/* Form actions - responsive layout */}
          <div className="flex flex-col sm:flex-row gap-3 pt-4 sm:pt-6 border-t border-neutral-200 dark:border-neutral-700">
            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full sm:w-auto order-2 sm:order-1 px-6 py-2.5 sm:py-3 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed text-sm sm:text-base"
            >
              {isSubmitting ? (
                <div className="flex items-center justify-center gap-2">
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                  Submitting...
                </div>
              ) : (
                block.config.submit.label || 'Submit'
              )}
            </button>
            
            <button
              type="button"
              onClick={() => {
                setFormData({})
                setErrors({})
              }}
              disabled={isSubmitting}
              className="w-full sm:w-auto order-1 sm:order-2 px-4 py-2.5 sm:py-3 border border-neutral-300 dark:border-neutral-600 text-neutral-700 dark:text-neutral-300 hover:bg-neutral-50 dark:hover:bg-neutral-800 font-medium rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed text-sm sm:text-base"
            >
              Reset
            </button>
          </div>
          
          {/* Form footer info */}
          {block.config.description && (
            <div className="text-xs sm:text-sm text-neutral-500 dark:text-neutral-400 text-center pt-2">
              {block.config.description}
            </div>
          )}
        </form>
      </div>
    </div>
  )
}