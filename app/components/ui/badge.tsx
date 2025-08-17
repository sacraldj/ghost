import * as React from "react"

export interface BadgeProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'default' | 'secondary' | 'destructive' | 'outline'
}

function Badge({ className = '', variant = 'default', ...props }: BadgeProps) {
  const baseClasses = "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors"
  
  const variantClasses = {
    default: "border-transparent bg-yellow-500 text-black hover:bg-yellow-600",
    secondary: "border-transparent bg-gray-600 text-white hover:bg-gray-700",
    destructive: "border-transparent bg-red-500 text-white hover:bg-red-600",
    outline: "border-gray-600 bg-transparent text-white hover:bg-gray-800",
  }
  
  const classes = `${baseClasses} ${variantClasses[variant]} ${className}`
  
  return (
    <div className={classes} {...props} />
  )
}

export { Badge }
