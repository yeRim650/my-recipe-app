import { type NextRequest, NextResponse } from "next/server"

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const { query } = body

    // 시뮬레이션된 당근 밥요리 추천 데이터
    const carrotRecipes = [
      {
        id: 1,
        title: "당근 볶음밥",
        description: "달콤한 당근과 계란이 어우러진 영양만점 볶음밥",
        ingredients: ["당근 2개", "밥 2공기", "계란 2개", "양파 1/2개", "간장 2큰술", "참기름 1큰술"],
        cookingTime: "15분",
        difficulty: "쉬움",
        calories: "320kcal",
        image: "/placeholder.svg?height=200&width=300",
      },
      {
        id: 2,
        title: "당근 카레라이스",
        description: "부드러운 당근이 들어간 진한 카레라이스",
        ingredients: ["당근 3개", "감자 2개", "양파 1개", "카레루 4조각", "쇠고기 200g", "밥 3공기"],
        cookingTime: "30분",
        difficulty: "보통",
        calories: "450kcal",
        image: "/placeholder.svg?height=200&width=300",
      },
      {
        id: 3,
        title: "당근 주먹밥",
        description: "아이들이 좋아하는 달콤한 당근 주먹밥",
        ingredients: ["당근 1개", "밥 2공기", "참치 1캔", "마요네즈 2큰술", "김 3장"],
        cookingTime: "10분",
        difficulty: "쉬움",
        calories: "280kcal",
        image: "/placeholder.svg?height=200&width=300",
      },
      {
        id: 4,
        title: "당근 비빔밥",
        description: "신선한 당근과 각종 나물이 어우러진 건강한 비빔밥",
        ingredients: ["당근 2개", "밥 2공기", "시금치 100g", "콩나물 100g", "고추장 2큰술", "참기름 1큰술"],
        cookingTime: "20분",
        difficulty: "보통",
        calories: "380kcal",
        image: "/placeholder.svg?height=200&width=300",
      },
    ]

    // 간단한 지연 시뮬레이션
    await new Promise((resolve) => setTimeout(resolve, 1000))

    return NextResponse.json({
      success: true,
      query,
      recommendations: carrotRecipes,
      total: carrotRecipes.length,
      timestamp: new Date().toISOString(),
    })
  } catch (error) {
    console.error("API Error:", error)
    return NextResponse.json({ success: false, error: "Failed to get recommendations" }, { status: 500 })
  }
}
