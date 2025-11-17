import type React from "react"
import { cn } from "@/lib/utils"

interface SectionProps extends React.HTMLAttributes<HTMLDivElement> {
  title?: string
  description?: string
}

export function Section({ className, title, description, children, ...props }: SectionProps) {
  return (
    <section className={cn("space-y-6", className)} {...props}>
      {(title || description) && (
        <div className="space-y-1">
          {title && <h2 className="text-2xl font-bold tracking-tight">{title}</h2>}
          {description && <p className="text-muted-foreground">{description}</p>}
        </div>
      )}
      {children}
    </section>
  )
}
