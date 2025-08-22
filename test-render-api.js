// Тест Render API
const RENDER_API_KEY = 'rnd_XKaMTwq7JfnZs5j71yh8g0h6CyjM'

async function testRenderAPI() {
  try {
    console.log('🧪 Тестируем Render API...')
    
    const response = await fetch('https://api.render.com/v1/services?limit=5', {
      headers: {
        'Authorization': `Bearer ${RENDER_API_KEY}`,
        'Content-Type': 'application/json',
      },
    })
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }
    
    const data = await response.json()
    console.log('✅ API работает!')
    console.log('📊 Полный ответ API:')
    console.log(JSON.stringify(data, null, 2))
    
    if (Array.isArray(data) && data.length > 0) {
      console.log(`\n📊 Найдено сервисов: ${data.length}`)
      data.forEach((service, index) => {
        console.log(`${index + 1}. ${service.name || service.service?.name || 'Unknown'} - ${service.status || service.service?.status || 'Unknown'}`)
      })
    } else if (data && data.length !== undefined) {
      console.log(`📊 Найдено сервисов: ${data.length}`)
    } else {
      console.log('📊 Структура ответа:', Object.keys(data))
    }
    
  } catch (error) {
    console.error('❌ Ошибка API:', error.message)
    console.log('💡 Проверьте правильность API ключа')
  }
}

// Тестируем API:
testRenderAPI()

console.log(`
🔑 Для тестирования:
1. Получите API ключ в Render Dashboard
2. Замените 'rnd_your_api_key_here' на ваш ключ
3. Раскомментируйте последнюю строку
4. Запустите: node test-render-api.js
`)
