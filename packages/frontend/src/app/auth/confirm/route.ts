import { type EmailOtpType } from '@supabase/supabase-js'
import { type NextRequest, NextResponse } from 'next/server'
import { Resend } from 'resend'
import { createClient } from '@/lib/supabase/server'
import { renderWelcomeEmail, type WelcomeAlbum } from '@/lib/welcome-email'

async function sendWelcomeRecommendation(user: { id: string; email?: string; user_metadata?: { name?: string } }) {
    const albumId = process.env.WELCOME_ALBUM_ID
    const resendKey = process.env.RESEND_API_KEY
    const fromEmail = process.env.FROM_EMAIL ?? 'Jazzy <noreply@jazzy.yaennu.ch>'

    if (!albumId || !resendKey || !user.email) {
        console.error('Welcome email skipped: missing', !albumId && 'WELCOME_ALBUM_ID', !resendKey && 'RESEND_API_KEY', !user.email && 'user email')
        return
    }

    // Use admin client with service role key to bypass RLS for the album lookup
    const { createAdminClient } = await import('@/lib/supabase/admin')
    const admin = createAdminClient()

    const { data: album, error: albumError } = await admin
        .from('albums')
        .select('title, artist, release_year, cover_image_url, streaming_link_spotify, streaming_link_apple, album_summary, artist_summary')
        .eq('album_id', albumId)
        .single()

    if (!album) {
        console.error('Welcome email skipped: album not found for ID', albumId, albumError)
        return
    }

    const { data: userData } = await admin
        .from('users')
        .select('unsubscribe_token')
        .eq('user_id', user.id)
        .single()

    const frontendUrl = process.env.NEXT_PUBLIC_SITE_URL ?? process.env.NEXT_PUBLIC_SUPABASE_URL?.replace('.supabase.co', '') ?? ''
    const unsubscribeUrl = userData?.unsubscribe_token
        ? `${frontendUrl}/unsubscribe?token=${userData.unsubscribe_token}`
        : undefined

    const userName = user.user_metadata?.name ?? user.email.split('@')[0]
    const html = renderWelcomeEmail(userName, album as WelcomeAlbum, unsubscribeUrl)

    const resend = new Resend(resendKey)
    await resend.emails.send({
        from: fromEmail,
        to: user.email,
        subject: `Welcome to Jazzy — your first pick: ${album.title} by ${album.artist}`,
        html,
    })

    await admin
        .from('recommendations')
        .insert({ user_id: user.id, album_id: albumId })
}

export async function GET(request: NextRequest) {
    const { searchParams } = new URL(request.url)
    const token_hash = searchParams.get('token_hash')
    const type = searchParams.get('type') as EmailOtpType | null
    const code = searchParams.get('code')
    const next = searchParams.get('next') ?? '/settings'

    const redirectTo = request.nextUrl.clone()
    redirectTo.pathname = next
    redirectTo.searchParams.delete('token_hash')
    redirectTo.searchParams.delete('type')
    redirectTo.searchParams.delete('code')

    // PKCE flow: exchanging an auth code (used by resetPasswordForEmail with redirectTo)
    if (code) {
        const supabase = await createClient()
        const { error } = await supabase.auth.exchangeCodeForSession(code)

        if (!error) {
            redirectTo.searchParams.delete('next')
            return NextResponse.redirect(redirectTo)
        }
    }

    // Token hash flow: verifying an OTP (used by email confirmation templates)
    if (token_hash && type) {
        const supabase = await createClient()

        const { data, error } = await supabase.auth.verifyOtp({
            type,
            token_hash,
        })

        if (!error) {
            // Send a welcome recommendation only on initial account confirmation
            if (type === 'signup' && data.user) {
                await sendWelcomeRecommendation(data.user).catch(console.error)
            }

            redirectTo.searchParams.delete('next')
            return NextResponse.redirect(redirectTo)
        }
    }

    redirectTo.pathname = '/login'
    return NextResponse.redirect(redirectTo)
}
