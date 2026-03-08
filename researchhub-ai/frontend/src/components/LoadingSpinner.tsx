import React from 'react'

interface Props {
  size?: 'sm' | 'md' | 'lg'
  className?: string
}

const LoadingSpinner: React.FC<Props> = ({ size = 'md', className = '' }) => {
  const sizes = { sm: 'w-4 h-4', md: 'w-8 h-8', lg: 'w-12 h-12' }
  return (
    <div
      className={`${sizes[size]} border-4 border-blue-600 border-t-transparent rounded-full animate-spin ${className}`}
    />
  )
}

export default LoadingSpinner
