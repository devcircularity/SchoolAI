// app/school/[schoolId]/page.tsx
'use client'

import { useEffect, useState } from 'react'
import { useParams } from 'next/navigation'
import { schoolService, type SchoolOverview } from '@/services/schools'
import { useAuth } from '@/contexts/AuthContext'
import { GraduationCap, Users, BookOpen, DollarSign, FileText, Loader2 } from 'lucide-react'

type SchoolInfo = {
  id: string
  name: string
}

export default function SchoolOverviewPage() {
  const params = useParams()
  const schoolId = params.schoolId as string
  const { isAuthenticated, isLoading: authLoading, token } = useAuth()
  
  const [schoolInfo, setSchoolInfo] = useState<SchoolInfo | null>(null)
  const [overview, setOverview] = useState<SchoolOverview | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    // Don't make API calls if auth is still loading or user is not authenticated
    if (authLoading || !isAuthenticated || !schoolId || !token) {
      if (!authLoading && !isAuthenticated) {
        setError('Please log in to view school information')
        setLoading(false)
      }
      return
    }

    const loadSchoolData = async () => {
      try {
        setLoading(true)
        setError(null)

        console.log('Loading school data with token:', token ? 'present' : 'missing')

        // Load school basic info and overview in parallel
        const [schoolData, overviewData] = await Promise.all([
          schoolService.get(schoolId),
          schoolService.getOverview(schoolId)
        ])

        setSchoolInfo(schoolData)
        setOverview(overviewData)
      } catch (err: any) {
        console.error('Failed to load school data:', err)
        if (err?.response?.status === 401) {
          setError('Authentication failed. Please log in again.')
        } else {
          setError('Failed to load school information')
        }
      } finally {
        setLoading(false)
      }
    }

    loadSchoolData()
  }, [authLoading, isAuthenticated, schoolId, token])

  // Show loading while auth is initializing
  if (authLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="flex items-center gap-3">
          <Loader2 className="w-6 h-6 animate-spin text-blue-600" />
          <span className="text-lg">Initializing...</span>
        </div>
      </div>
    )
  }

  // Show auth required message
  if (!isAuthenticated) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <h2 className="text-xl font-semibold mb-2">Authentication Required</h2>
          <p className="text-neutral-600 dark:text-neutral-400">Please log in to view school information.</p>
        </div>
      </div>
    )
  }

  // Show loading while fetching school data
  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="flex items-center gap-3">
          <Loader2 className="w-6 h-6 animate-spin text-blue-600" />
          <span className="text-lg">Loading school overview...</span>
        </div>
      </div>
    )
  }

  // Show error state
  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <h2 className="text-xl font-semibold mb-2 text-red-600">Error</h2>
          <p className="text-neutral-600 dark:text-neutral-400">{error}</p>
        </div>
      </div>
    )
  }

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-KE', {
      style: 'currency',
      currency: 'KES',
      minimumFractionDigits: 0
    }).format(amount)
  }

  const stats = [
    {
      label: 'Total Students',
      value: overview?.students || 0,
      icon: Users,
      color: 'text-blue-600',
      bgColor: 'bg-blue-50 dark:bg-blue-900/20'
    },
    {
      label: 'Classes',
      value: overview?.classes || 0,
      icon: BookOpen,
      color: 'text-green-600',
      bgColor: 'bg-green-50 dark:bg-green-900/20'
    },
    {
      label: 'Fees Collected',
      value: formatCurrency(overview?.feesCollected || 0),
      icon: DollarSign,
      color: 'text-purple-600',
      bgColor: 'bg-purple-50 dark:bg-purple-900/20'
    },
    {
      label: 'Pending Invoices',
      value: overview?.pendingInvoices || 0,
      icon: FileText,
      color: 'text-orange-600',
      bgColor: 'bg-orange-50 dark:bg-orange-900/20'
    }
  ]

  return (
    <div className="min-h-screen bg-neutral-50 dark:bg-neutral-950">
      {/* Header */}
      <div className="bg-white dark:bg-neutral-900 border-b border-neutral-200 dark:border-neutral-800">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center gap-4">
            <div className="p-3 rounded-xl bg-blue-100 dark:bg-blue-900/30">
              <GraduationCap className="w-8 h-8 text-blue-600" />
            </div>
            <div>
              <h1 className="text-3xl font-bold text-neutral-900 dark:text-neutral-100">
                {schoolInfo?.name || 'School Overview'}
              </h1>
              <p className="text-neutral-600 dark:text-neutral-400 mt-1">
                Manage your school's academic and administrative operations
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Statistics Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          {stats.map((stat, index) => {
            const Icon = stat.icon
            return (
              <div
                key={index}
                className="card p-6 hover:shadow-lg transition-shadow duration-200"
              >
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-neutral-600 dark:text-neutral-400 mb-1">
                      {stat.label}
                    </p>
                    <p className="text-2xl font-bold text-neutral-900 dark:text-neutral-100">
                      {stat.value}
                    </p>
                  </div>
                  <div className={`p-3 rounded-lg ${stat.bgColor}`}>
                    <Icon className={`w-6 h-6 ${stat.color}`} />
                  </div>
                </div>
              </div>
            )
          })}
        </div>

        {/* Quick Actions */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Academic Management */}
          <div className="card p-6">
            <h3 className="text-lg font-semibold text-neutral-900 dark:text-neutral-100 mb-4">
              Academic Management
            </h3>
            <div className="space-y-3">
              <button className="w-full text-left p-4 rounded-lg hover:bg-neutral-50 dark:hover:bg-neutral-800 transition-colors border border-neutral-200 dark:border-neutral-700">
                <div className="flex items-center gap-3">
                  <Users className="w-5 h-5 text-blue-600" />
                  <div>
                    <h4 className="font-medium">Manage Students</h4>
                    <p className="text-sm text-neutral-600 dark:text-neutral-400">
                      Add, edit, and organize student records
                    </p>
                  </div>
                </div>
              </button>
              
              <button className="w-full text-left p-4 rounded-lg hover:bg-neutral-50 dark:hover:bg-neutral-800 transition-colors border border-neutral-200 dark:border-neutral-700">
                <div className="flex items-center gap-3">
                  <BookOpen className="w-5 h-5 text-green-600" />
                  <div>
                    <h4 className="font-medium">Manage Classes</h4>
                    <p className="text-sm text-neutral-600 dark:text-neutral-400">
                      Create and organize class structures
                    </p>
                  </div>
                </div>
              </button>
            </div>
          </div>

          {/* Financial Management */}
          <div className="card p-6">
            <h3 className="text-lg font-semibold text-neutral-900 dark:text-neutral-100 mb-4">
              Financial Management
            </h3>
            <div className="space-y-3">
              <button className="w-full text-left p-4 rounded-lg hover:bg-neutral-50 dark:hover:bg-neutral-800 transition-colors border border-neutral-200 dark:border-neutral-700">
                <div className="flex items-center gap-3">
                  <DollarSign className="w-5 h-5 text-purple-600" />
                  <div>
                    <h4 className="font-medium">Fee Management</h4>
                    <p className="text-sm text-neutral-600 dark:text-neutral-400">
                      Set up fee structures and track payments
                    </p>
                  </div>
                </div>
              </button>
              
              <button className="w-full text-left p-4 rounded-lg hover:bg-neutral-50 dark:hover:bg-neutral-800 transition-colors border border-neutral-200 dark:border-neutral-700">
                <div className="flex items-center gap-3">
                  <FileText className="w-5 h-5 text-orange-600" />
                  <div>
                    <h4 className="font-medium">Invoices & Reports</h4>
                    <p className="text-sm text-neutral-600 dark:text-neutral-400">
                      Generate invoices and financial reports
                    </p>
                  </div>
                </div>
              </button>
            </div>
          </div>
        </div>

        {/* Recent Activity Placeholder */}
        <div className="mt-8">
          <div className="card p-6">
            <h3 className="text-lg font-semibold text-neutral-900 dark:text-neutral-100 mb-4">
              Recent Activity
            </h3>
            <div className="text-center py-8">
              <div className="w-16 h-16 bg-neutral-100 dark:bg-neutral-800 rounded-full flex items-center justify-center mx-auto mb-4">
                <GraduationCap className="w-8 h-8 text-neutral-400" />
              </div>
              <p className="text-neutral-600 dark:text-neutral-400">
                Recent school activities will appear here
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}