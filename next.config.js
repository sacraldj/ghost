/** @type {import('next').NextConfig} */
const nextConfig = {
  // Временно отключаем optimizePackageImports — может провоцировать расхождения чанков
  // experimental: {
  //   optimizePackageImports: ['framer-motion', 'recharts', 'lucide-react']
  // },
  
  // Webpack конфигурация для исправления module loading
  webpack: (config, { dev, isServer }) => {
    // Исправление для webpack module resolution
    config.resolve.fallback = {
      ...config.resolve.fallback,
      fs: false,
      net: false,
      tls: false,
    }
    
    // Оптимизация для клиентского бандла
    if (!isServer) {
      config.resolve.alias = {
        ...config.resolve.alias,
        'encoding': false,
      }
    }
    
    return config
  },
  
  // Transpile packages для совместимости
  transpilePackages: ['@supabase/auth-ui-react', '@supabase/auth-ui-shared']
}

module.exports = nextConfig 