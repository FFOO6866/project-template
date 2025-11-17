import type React from "react"
import { cn } from "@/lib/utils"
import { heading, type HeadingProps } from "@/lib/design-system"

interface Props extends React.HTMLAttributes<HTMLHeadingElement>, HeadingProps {
  as?: "h1" | "h2" | "h3" | "h4" | "h5" | "h6"
}

export function Heading({ className, level, as, children, ...props }: Props) {
  // Create a valid heading tag based on the level number
  let headingTag: "h1" | "h2" | "h3" | "h4" | "h5" | "h6" = "h1"

  if (typeof level === "number" && level >= 1 && level <= 6) {
    headingTag = `h${level}` as "h1" | "h2" | "h3" | "h4" | "h5" | "h6"
  }

  const Component = as || headingTag

  return (
    <Component className={cn(heading({ level }), className)} {...props}>
      {children}
    </Component>
  )
}
