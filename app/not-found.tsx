import Link from 'next/link'

export default function NotFound() {
  return (
    <div className="min-h-screen bg-black text-white flex items-center justify-center">
      <div className="text-center">
        <h2 className="text-6xl font-bold mb-4">404</h2>
        <h1 className="text-2xl font-semibold mb-4">Страница не найдена</h1>
        <p className="text-gray-400 mb-8">
          Извините, но страница, которую вы ищете, не существует.
        </p>
        <Link
          href="/"
          className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg transition-colors"
        >
          Вернуться на главную
        </Link>
      </div>
    </div>
  )
}
