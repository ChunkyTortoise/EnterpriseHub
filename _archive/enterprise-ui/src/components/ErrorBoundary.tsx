/**
 * React Error Boundary Component for Jorge Platform
 * Catches JavaScript errors anywhere in the component tree and displays fallback UI
 */

'use client'

import React, { Component, ReactNode, ErrorInfo } from 'react'
import { AlertTriangle, RefreshCw, Home, Bug } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { errorService } from '@/lib/errors/ErrorService'

interface Props {
  children: ReactNode
  fallback?: ReactNode
  onError?: (error: Error, errorInfo: ErrorInfo) => void
}

interface State {
  hasError: boolean
  error?: Error
  errorId?: string
  retryCount: number
}

export class ErrorBoundary extends Component<Props, State> {
  private maxRetries = 3

  constructor(props: Props) {
    super(props)
    this.state = {
      hasError: false,
      retryCount: 0
    }
  }

  static getDerivedStateFromError(error: Error): State {
    return {
      hasError: true,
      error,
      errorId: `error_${Date.now()}`,
      retryCount: 0
    }
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    // Log to our error service
    const handledError = errorService.handleError(error, 'ErrorBoundary', {
      logToConsole: true,
      reportToService: true,
      showToUser: false // We handle UI ourselves
    })

    this.setState({ errorId: handledError.code })

    // Call custom error handler if provided
    if (this.props.onError) {
      this.props.onError(error, errorInfo)
    }

    console.error('Error Boundary caught an error:', {
      error,
      errorInfo,
      componentStack: errorInfo.componentStack
    })
  }

  handleRetry = () => {
    if (this.state.retryCount < this.maxRetries) {
      this.setState({
        hasError: false,
        error: undefined,
        errorId: undefined,
        retryCount: this.state.retryCount + 1
      })
    }
  }

  handleReload = () => {
    window.location.reload()
  }

  handleGoHome = () => {
    window.location.href = '/'
  }

  render() {
    if (this.state.hasError) {
      // Use custom fallback if provided
      if (this.props.fallback) {
        return this.props.fallback
      }

      // Default error UI
      return (
        <div className="min-h-screen flex items-center justify-center p-4 bg-gray-900">
          <Card className="w-full max-w-md p-6 bg-gray-800 border-gray-700">
            <div className="flex items-center gap-3 mb-4">
              <div className="p-2 bg-red-500/20 rounded-full">
                <AlertTriangle className="w-6 h-6 text-red-400" />
              </div>
              <div>
                <h2 className="text-lg font-semibold text-white">
                  Something went wrong
                </h2>
                <p className="text-sm text-gray-400">
                  Error ID: {this.state.errorId}
                </p>
              </div>
            </div>

            <div className="mb-6 p-4 bg-gray-900/50 rounded-lg border border-gray-700">
              <p className="text-sm text-gray-300 mb-2">
                We apologize for the inconvenience. The application encountered an unexpected error.
              </p>
              {process.env.NODE_ENV === 'development' && this.state.error && (
                <details className="mt-3">
                  <summary className="text-xs text-gray-500 cursor-pointer hover:text-gray-400">
                    <Bug className="w-3 h-3 inline mr-1" />
                    Error Details (Development)
                  </summary>
                  <pre className="mt-2 text-xs text-red-400 bg-red-500/10 p-2 rounded overflow-auto max-h-32">
                    {this.state.error.message}
                    {this.state.error.stack && '\n\n' + this.state.error.stack}
                  </pre>
                </details>
              )}
            </div>

            <div className="space-y-3">
              {this.state.retryCount < this.maxRetries && (
                <Button
                  onClick={this.handleRetry}
                  className="w-full bg-blue-600 hover:bg-blue-700"
                >
                  <RefreshCw className="w-4 h-4 mr-2" />
                  Try Again ({this.maxRetries - this.state.retryCount} attempts left)
                </Button>
              )}

              <div className="grid grid-cols-2 gap-3">
                <Button
                  variant="outline"
                  onClick={this.handleReload}
                  className="border-gray-600 text-gray-300 hover:bg-gray-700"
                >
                  <RefreshCw className="w-4 h-4 mr-2" />
                  Reload Page
                </Button>
                <Button
                  variant="outline"
                  onClick={this.handleGoHome}
                  className="border-gray-600 text-gray-300 hover:bg-gray-700"
                >
                  <Home className="w-4 h-4 mr-2" />
                  Go Home
                </Button>
              </div>
            </div>

            <div className="mt-4 text-center">
              <p className="text-xs text-gray-500">
                If this problem persists, please contact support with Error ID: {this.state.errorId}
              </p>
            </div>
          </Card>
        </div>
      )
    }

    return this.props.children
  }
}

// Higher-order component for wrapping components with error boundary
export const withErrorBoundary = <P extends object>(
  Component: React.ComponentType<P>,
  fallback?: ReactNode
) => {
  const WrappedComponent = (props: P) => (
    <ErrorBoundary fallback={fallback}>
      <Component {...props} />
    </ErrorBoundary>
  )

  WrappedComponent.displayName = `withErrorBoundary(${Component.displayName || Component.name})`

  return WrappedComponent
}

// Specialized error boundary for specific sections
export function SectionErrorBoundary({
  children,
  sectionName,
  className = ''
}: {
  children: ReactNode
  sectionName: string
  className?: string
}) {
  return (
    <ErrorBoundary
      fallback={
        <div className={`p-4 bg-red-500/10 border border-red-500/20 rounded-lg ${className}`}>
          <div className="flex items-center gap-2 mb-2">
            <AlertTriangle className="w-4 h-4 text-red-400" />
            <span className="text-sm font-medium text-red-400">
              Error in {sectionName}
            </span>
          </div>
          <p className="text-xs text-gray-400 mb-3">
            This section encountered an error and couldn't load properly.
          </p>
          <Button
            size="sm"
            variant="outline"
            onClick={() => window.location.reload()}
            className="text-xs border-red-500/30 text-red-400 hover:bg-red-500/10"
          >
            <RefreshCw className="w-3 h-3 mr-1" />
            Reload
          </Button>
        </div>
      }
    >
      {children}
    </ErrorBoundary>
  )
}

export default ErrorBoundary