import type React from "react"
import { cn } from "@/lib/utils"
import { text, type TextProps } from "@/lib/design-system"

interface Props extends Omit<React.HTMLAttributes<HTMLParagraphElement>, 'color'>, TextProps {}

export function Text({ className, size, weight, color, children, ...props }: Props) {
  return (
    <p className={cn(text({ size, weight, color }), className)} {...props}>
      {children}
    </p>
  )
}
