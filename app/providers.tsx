'use client'

import posthog from 'posthog-js'
import { PostHogProvider as PHProvider } from 'posthog-js/react'
import { Suspense, useEffect } from 'react'

export function PostHogProvider({ children }: { children: React.ReactNode }) {
  useEffect(() => {
    if (typeof window === 'undefined') return
    if (process.env.NODE_ENV !== 'production' && !process.env.NEXT_PUBLIC_POSTHOG_DEBUG) return
    if (!process.env.NEXT_PUBLIC_POSTHOG_KEY) return

    posthog.init(process.env.NEXT_PUBLIC_POSTHOG_KEY, {
      api_host: process.env.NEXT_PUBLIC_POSTHOG_HOST || 'https://us.i.posthog.com',
      person_profiles: 'identified_only',
      capture_pageview: 'history_change',
      capture_pageleave: true,
      loaded: (ph) => {
        // Register `site` super-property so every event tags the source domain
        ph.register({ site: window.location.hostname })
      },
    })
  }, [])

  return <PHProvider client={posthog}>{children}</PHProvider>
}
