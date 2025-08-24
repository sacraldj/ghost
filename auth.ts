import NextAuth from 'next-auth'
import Google from 'next-auth/providers/google'
import Credentials from 'next-auth/providers/credentials'
import { createClient } from '@supabase/supabase-js'
import bcrypt from 'bcryptjs'

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_ROLE_KEY!
)

export const { handlers, signIn, signOut, auth } = NextAuth({
  providers: [
    Google({
      clientId: process.env.GOOGLE_CLIENT_ID!,
      clientSecret: process.env.GOOGLE_CLIENT_SECRET!,
    }),
    Credentials({
      name: 'credentials',
      credentials: {
        email: { label: 'Email', type: 'email' },
        password: { label: 'Password', type: 'password' }
      },
      async authorize(credentials) {
        if (!credentials?.email || !credentials?.password) {
          return null
        }

        // Admin access
        if (credentials.email === 'admin@ghost.com' && credentials.password === '88888888') {
          return {
            id: 'admin',
            email: 'admin@ghost.com',
            name: 'GHOST Admin',
            role: 'admin',
            image: '/admin-avatar.png'
          }
        }

        // Check user in database
        const { data: user, error } = await supabase
          .from('users')
          .select('*')
          .eq('email', credentials.email)
          .single()

        if (error || !user) {
          return null
        }

        // Verify password
        const isValidPassword = await bcrypt.compare(credentials.password as string, user.password_hash as string)
        if (!isValidPassword) {
          return null
        }

        return {
          id: user.id,
          email: user.email,
          name: user.name,
          role: user.role || 'user',
          image: user.avatar_url
        }
      }
    })
  ],
  callbacks: {
    async signIn({ user, account, profile }) {
      if (account?.provider === 'google') {
        try {
          // Check if user exists
          const { data: existingUser, error } = await supabase
            .from('users')
            .select('*')
            .eq('email', user.email)
            .single()

          if (error && error.code !== 'PGRST116') {
            console.error('Error checking user:', error)
            return false
          }

          if (!existingUser) {
            // Create new user
            const { error: insertError } = await supabase
              .from('users')
              .insert({
                email: user.email,
                name: user.name,
                avatar_url: user.image,
                provider: 'google',
                provider_id: account.providerAccountId,
                role: 'user',
                created_at: new Date().toISOString(),
                last_login: new Date().toISOString()
              })

            if (insertError) {
              console.error('Error creating user:', insertError)
              return false
            }
          } else {
            // Update last login
            await supabase
              .from('users')
              .update({ 
                last_login: new Date().toISOString(),
                avatar_url: user.image,
                name: user.name
              })
              .eq('id', existingUser.id)
          }
        } catch (error) {
          console.error('Error in signIn callback:', error)
          return false
        }
      }
      return true
    },
    async jwt({ token, user }) {
      if (user) {
        token.role = user.role
        token.userId = user.id
      }
      return token
    },
    async session({ session, token }) {
      if (token) {
        session.user.role = token.role as string
        session.user.id = token.userId as string
      }
      return session
    }
  },
  pages: {
    signIn: '/auth/signin',
    error: '/auth/error',
  },
  session: {
    strategy: 'jwt',
    maxAge: 30 * 24 * 60 * 60, // 30 days
  },
  secret: process.env.NEXTAUTH_SECRET,
})
