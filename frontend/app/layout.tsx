import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'my-recipe-app',
  description: 'my-recipe-app',
  generator: 'my-recipe-app',
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}
