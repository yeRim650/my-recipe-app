"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog"
import { ChefHat, Search, User, Refrigerator, Plus, X } from "lucide-react"
import type { Recipe, RecommendationResponse } from "../types/recipe"
import { Label } from "@/components/ui/label"

export default function CleanRecipeRecommender() {
  const [recipes, setRecipes] = useState<Recipe[]>([])
  const [fridgeItems, setFridgeItems] = useState<string[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [hasSearched, setHasSearched] = useState(false)
  const [query, setQuery] = useState("")
  const [newIngredient, setNewIngredient] = useState("")
  const [isLoggedIn, setIsLoggedIn] = useState(false)
  const [username, setUsername] = useState("")
  const [loginUsername, setLoginUsername] = useState("")
  const [loginPassword, setLoginPassword] = useState("")

  // 로딩 상태들
  const [fridgeLoading, setFridgeLoading] = useState(false)
  const [addingIngredient, setAddingIngredient] = useState(false)
  const [deletingIngredient, setDeletingIngredient] = useState<string | null>(null)
  const [loginLoading, setLoginLoading] = useState(false)
  const [logoutLoading, setLogoutLoading] = useState(false)

  // 냉장고 재료와 매칭되는 재료를 찾는 함수 추가
  const findMatchingIngredients = (description: string, fridgeItems: string[]) => {
    const ingredients = description.split(",").map((item) => item.trim())
    const matches: { ingredient: string; fridgeItem: string }[] = []

    ingredients.forEach((ingredient) => {
      fridgeItems.forEach((fridgeItem) => {
        if (ingredient.includes(fridgeItem)) {
          matches.push({ ingredient, fridgeItem })
        }
      })
    })

    return matches
  }

  // 재료 텍스트를 하이라이트하는 함수 추가
  const highlightIngredients = (description: string, fridgeItems: string[]) => {
    let highlightedText = description

    fridgeItems.forEach((fridgeItem) => {
      const regex = new RegExp(`(${fridgeItem})`, "gi")
      highlightedText = highlightedText.replace(
        regex,
        `<mark class="bg-green-100 text-green-800 px-1 rounded">$1</mark>`,
      )
    })

    return highlightedText
  }

  const fetchRecommendations = async () => {
    if (!query.trim()) return

    setLoading(true)
    setError(null)

    try {
      const response = await fetch("http://127.0.0.1:8000/api/rag/recommend", {
        method: "POST",
        headers: {
          accept: "application/json",
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          user_id: 1,
          query: query,
          top_k: 10,
          boost: 0.2,
        }),
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const data: RecommendationResponse = await response.json()
      setRecipes(data.recommendations)
      setFridgeItems(data.fridge)
      setHasSearched(true)
    } catch (err) {
      // Mock data for development
      setFridgeItems(["당근", "두부", "양파", "계란"])
      setRecipes([
        {
          id: 1,
          name: "당근 볶음밥",
          category: "밥",
          method: "볶기",
          description: "당근 2개, 밥 2공기, 계란 2개, 양파 1/2개, 간장 2큰술, 참기름 1큰술",
          reason: "냉장고에 있는 당근과 계란을 활용한 영양만점 볶음밥입니다.",
        },
        {
          id: 2,
          name: "두부 당근 조림",
          category: "반찬",
          method: "끓이기",
          description: "두부 1모, 당근 1개, 양파 1/2개, 간장 3큰술, 설탕 1큰술, 물 1컵",
          reason: "부드러운 두부와 달콤한 당근이 어우러진 건강한 반찬입니다.",
        },
        {
          id: 3,
          name: "당근 계란말이",
          category: "반찬",
          method: "굽기",
          description: "계란 4개, 당근 1/2개, 소금 약간, 식용유 2큰술",
          reason: "아이들이 좋아하는 달콤한 당근이 들어간 계란말이입니다.",
        },
      ])
      setHasSearched(true)
    } finally {
      setLoading(false)
    }
  }

  // 냉장고 재료 조회
  const loadFridgeItems = async () => {
    setFridgeLoading(true)
    try {
      // API 호출 시뮬레이션
      await new Promise((resolve) => setTimeout(resolve, 800))
      // 실제로는 API에서 사용자의 냉장고 재료를 가져옴
    } catch (err) {
      console.error("Failed to load fridge items:", err)
    } finally {
      setFridgeLoading(false)
    }
  }

  const addIngredient = async () => {
    if (!newIngredient.trim() || fridgeItems.includes(newIngredient.trim())) return

    setAddingIngredient(true)
    try {
      // API 호출 시뮬레이션
      await new Promise((resolve) => setTimeout(resolve, 500))
      setFridgeItems([...fridgeItems, newIngredient.trim()])
      setNewIngredient("")
    } catch (err) {
      console.error("Failed to add ingredient:", err)
    } finally {
      setAddingIngredient(false)
    }
  }

  const removeIngredient = async (ingredient: string) => {
    setDeletingIngredient(ingredient)
    try {
      // API 호출 시뮬레이션
      await new Promise((resolve) => setTimeout(resolve, 500))
      setFridgeItems(fridgeItems.filter((item) => item !== ingredient))
    } catch (err) {
      console.error("Failed to remove ingredient:", err)
    } finally {
      setDeletingIngredient(null)
    }
  }

  const handleLogin = async () => {
    if (!isLoggedIn) {
      if (!loginUsername.trim()) return

      setLoginLoading(true)
      try {
        // 로그인 API 호출 시뮬레이션
        await new Promise((resolve) => setTimeout(resolve, 1000))
        setIsLoggedIn(true)
        setUsername(loginUsername)
        setLoginUsername("")
        setLoginPassword("")
      } catch (err) {
        console.error("Login failed:", err)
      } finally {
        setLoginLoading(false)
      }
    } else {
      setLogoutLoading(true)
      try {
        // 로그아웃 API 호출 시뮬레이션
        await new Promise((resolve) => setTimeout(resolve, 800))
        setIsLoggedIn(false)
        setUsername("")
      } catch (err) {
        console.error("Logout failed:", err)
      } finally {
        setLogoutLoading(false)
      }
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-4xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-gray-900 rounded-lg flex items-center justify-center">
              <ChefHat className="w-6 h-6 text-white" />
            </div>
            <h1 className="text-2xl font-bold text-gray-900">레시피 추천</h1>
          </div>

          <div className="flex items-center gap-3">
            {isLoggedIn && username && (
              <span className="text-gray-600">
                안녕하세요, <span className="font-medium text-gray-900">{username}</span>님
              </span>
            )}

            {!isLoggedIn ? (
              <Dialog>
                <DialogTrigger asChild>
                  <Button className="flex items-center gap-2">
                    <User className="w-4 h-4" />
                    로그인
                  </Button>
                </DialogTrigger>
                <DialogContent className="sm:max-w-md">
                  <DialogHeader>
                    <DialogTitle>로그인</DialogTitle>
                  </DialogHeader>
                  <div className="space-y-4">
                    <div className="space-y-2">
                      <Label htmlFor="username">사용자명</Label>
                      <Input
                        id="username"
                        value={loginUsername}
                        onChange={(e) => setLoginUsername(e.target.value)}
                        placeholder="사용자명을 입력하세요"
                        disabled={loginLoading}
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="password">이메일</Label>
                      <Input
                        id="password"
                        value={loginPassword}
                        onChange={(e) => setLoginPassword(e.target.value)}
                        placeholder="이메일울 입력하세요"
                        disabled={loginLoading}
                      />
                    </div>
                    <Button onClick={handleLogin} className="w-full" disabled={!loginUsername.trim() || loginLoading}>
                      {loginLoading ? (
                        <>
                          <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2" />
                          로그인 중...
                        </>
                      ) : (
                        "로그인"
                      )}
                    </Button>
                  </div>
                </DialogContent>
              </Dialog>
            ) : (
              <Button
                onClick={handleLogin}
                variant="outline"
                className="flex items-center gap-2"
                disabled={logoutLoading}
              >
                {logoutLoading ? (
                  <>
                    <div className="w-4 h-4 border-2 border-gray-600 border-t-transparent rounded-full animate-spin" />
                    로그아웃 중...
                  </>
                ) : (
                  <>
                    <User className="w-4 h-4" />
                    로그아웃
                  </>
                )}
              </Button>
            )}
          </div>
        </div>
      </header>

      <div className="max-w-4xl mx-auto px-6 py-8">
        {/* Search Section */}
        <Card className="mb-8 shadow-sm">
          <CardContent className="p-6">
            <div className="space-y-4">
              <div className="flex gap-3">
                <div className="flex-1">
                  <Input
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    placeholder="어떤 요리를 만들고 싶으신가요? (예: 상큼한 샐러드)"
                    className="h-12 text-lg"
                    onKeyPress={(e) => e.key === "Enter" && fetchRecommendations()}
                  />
                </div>
                <Button onClick={fetchRecommendations} disabled={loading || !query.trim()} className="h-12 px-6">
                  {loading ? (
                    <>
                      <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin mr-2" />
                      검색 중...
                    </>
                  ) : (
                    <>
                      <Search className="w-5 h-5 mr-2" />
                      검색
                    </>
                  )}
                </Button>
              </div>

              {/* Fridge Management */}
              <div className="flex items-center gap-3">
                <Dialog onOpenChange={(open) => open && loadFridgeItems()}>
                  <DialogTrigger asChild>
                    <Button variant="outline" className="flex items-center gap-2">
                      <Refrigerator className="w-4 h-4" />
                      냉장고 재료 관리
                      {fridgeItems.length > 0 && (
                        <Badge variant="secondary" className="ml-1">
                          {fridgeItems.length}
                        </Badge>
                      )}
                    </Button>
                  </DialogTrigger>
                  <DialogContent className="sm:max-w-md">
                    <DialogHeader>
                      <DialogTitle>냉장고 재료</DialogTitle>
                    </DialogHeader>
                    <div className="space-y-4">
                      <div className="flex gap-2">
                        <Input
                          value={newIngredient}
                          onChange={(e) => setNewIngredient(e.target.value)}
                          placeholder="재료 추가"
                          onKeyPress={(e) => e.key === "Enter" && addIngredient()}
                          disabled={addingIngredient}
                        />
                        <Button onClick={addIngredient} size="sm" disabled={addingIngredient || !newIngredient.trim()}>
                          {addingIngredient ? (
                            <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                          ) : (
                            <Plus className="w-4 h-4" />
                          )}
                        </Button>
                      </div>

                      <div className="space-y-2 max-h-60 overflow-y-auto">
                        {fridgeLoading ? (
                          <div className="space-y-2">
                            {[1, 2, 3].map((i) => (
                              <div key={i} className="flex items-center justify-between p-2 bg-gray-50 rounded-md">
                                <div className="h-4 bg-gray-200 rounded w-20 animate-pulse"></div>
                                <div className="h-6 w-6 bg-gray-200 rounded animate-pulse"></div>
                              </div>
                            ))}
                          </div>
                        ) : (
                          <>
                            {fridgeItems.map((ingredient, index) => (
                              <div key={index} className="flex items-center justify-between p-2 bg-gray-50 rounded-md">
                                <span>{ingredient}</span>
                                <Button
                                  onClick={() => removeIngredient(ingredient)}
                                  variant="ghost"
                                  size="sm"
                                  className="h-6 w-6 p-0"
                                  disabled={deletingIngredient === ingredient}
                                >
                                  {deletingIngredient === ingredient ? (
                                    <div className="w-4 h-4 border-2 border-gray-600 border-t-transparent rounded-full animate-spin" />
                                  ) : (
                                    <X className="w-4 h-4" />
                                  )}
                                </Button>
                              </div>
                            ))}
                            {fridgeItems.length === 0 && (
                              <p className="text-gray-500 text-center py-4">재료를 추가해보세요</p>
                            )}
                          </>
                        )}
                      </div>
                    </div>
                  </DialogContent>
                </Dialog>

                {fridgeItems.length > 0 && (
                  <div className="flex flex-wrap gap-1">
                    {fridgeItems.slice(0, 3).map((item, index) => (
                      <Badge key={index} variant="secondary" className="text-xs">
                        {item}
                      </Badge>
                    ))}
                    {fridgeItems.length > 3 && (
                      <Badge variant="secondary" className="text-xs">
                        +{fridgeItems.length - 3}
                      </Badge>
                    )}
                  </div>
                )}
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Error Message */}
        {error && (
          <Card className="mb-6 border-red-200 bg-red-50">
            <CardContent className="p-4">
              <p className="text-red-600 text-center">{error}</p>
            </CardContent>
          </Card>
        )}

        {/* Loading Skeleton */}
        {loading && (
          <div className="space-y-6">
            <div className="text-center">
              <div className="h-8 bg-gray-200 rounded w-48 mx-auto mb-2 animate-pulse"></div>
              <div className="w-16 h-1 bg-gray-200 mx-auto rounded-full animate-pulse"></div>
            </div>

            <div className="grid gap-6">
              {[1, 2, 3].map((i) => (
                <Card key={i} className="shadow-sm animate-pulse">
                  <CardHeader className="pb-4">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="h-6 bg-gray-200 rounded w-3/4 mb-2"></div>
                        <div className="flex gap-2">
                          <div className="h-5 bg-gray-200 rounded w-12"></div>
                          <div className="h-5 bg-gray-200 rounded w-12"></div>
                        </div>
                      </div>
                      <div className="h-4 bg-gray-200 rounded w-8"></div>
                    </div>
                  </CardHeader>

                  <CardContent className="space-y-4">
                    <div>
                      <div className="h-5 bg-gray-200 rounded w-16 mb-2"></div>
                      <div className="space-y-2">
                        <div className="h-4 bg-gray-200 rounded w-full"></div>
                        <div className="h-4 bg-gray-200 rounded w-3/4"></div>
                      </div>
                    </div>

                    <div className="border-t pt-4">
                      <div className="h-5 bg-gray-200 rounded w-20 mb-2"></div>
                      <div className="space-y-2">
                        <div className="h-4 bg-gray-200 rounded w-full"></div>
                        <div className="h-4 bg-gray-200 rounded w-2/3"></div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        )}

        {/* Results */}
        {hasSearched && recipes.length > 0 && (
          <div className="space-y-6">
            <div className="text-center">
              <h2 className="text-2xl font-bold text-gray-900 mb-2">추천 레시피 ({recipes.length}개)</h2>
              <div className="w-16 h-1 bg-gray-900 mx-auto rounded-full"></div>
            </div>

            <div className="grid gap-6">
              {recipes.map((recipe) => (
                <Card key={recipe.id} className="shadow-sm hover:shadow-md transition-shadow">
                  <CardHeader className="pb-4">
                    <div className="flex items-start justify-between">
                      <div>
                        <CardTitle className="text-xl text-gray-900 mb-2">{recipe.name}</CardTitle>
                        <div className="flex gap-2">
                          <Badge variant="outline">{recipe.category}</Badge>
                          <Badge variant="outline">{recipe.method}</Badge>
                        </div>
                      </div>
                      <div className="text-sm text-gray-500">#{recipe.id}</div>
                    </div>
                  </CardHeader>

                  <CardContent className="space-y-4">
                    <div>
                      <div className="flex items-center justify-between mb-2">
                        <h4 className="font-medium text-gray-900">재료</h4>
                        {(() => {
                          const matches = findMatchingIngredients(recipe.description, fridgeItems)
                          return (
                            matches.length > 0 && (
                              <div className="flex items-center gap-1">
                                <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                                <span className="text-xs text-green-600 font-medium">
                                  냉장고 재료 {matches.length}개 사용
                                </span>
                              </div>
                            )
                          )
                        })()}
                      </div>
                      <div
                        className="text-gray-600 text-sm leading-relaxed"
                        dangerouslySetInnerHTML={{
                          __html: highlightIngredients(recipe.description, fridgeItems),
                        }}
                      />
                    </div>

                    <div className="border-t pt-4">
                      <h4 className="font-medium text-gray-900 mb-2">추천 이유</h4>
                      <p className="text-gray-600 text-sm leading-relaxed">{recipe.reason}</p>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        )}

        {/* Empty State */}
        {hasSearched && recipes.length === 0 && !loading && !error && (
          <Card className="text-center py-12 shadow-sm">
            <CardContent>
              <ChefHat className="w-16 h-16 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">추천 결과가 없습니다</h3>
              <p className="text-gray-600">다른 검색어로 다시 시도해보세요</p>
            </CardContent>
          </Card>
        )}

        {/* Welcome Message */}
        {!hasSearched && (
          <Card className="text-center py-16 shadow-sm">
            <CardContent>
              <ChefHat className="w-20 h-20 text-gray-400 mx-auto mb-6" />
              <h3 className="text-2xl font-bold text-gray-900 mb-4">맛있는 요리를 찾아보세요</h3>
              <p className="text-gray-600 mb-6">냉장고에 있는 재료로 만들 수 있는 레시피를 추천해드립니다</p>
              <div className="flex flex-wrap justify-center gap-2">
                {["해물 풍미가 살아있는 얼큰한 찌개", "매콤한 면요리", "깊은 국물 요리", "부드러운 찜 요리"].map((suggestion) => (
                  <Button
                    key={suggestion}
                    variant="outline"
                    size="sm"
                    onClick={() => setQuery(suggestion)}
                    className="text-sm"
                  >
                    {suggestion}
                  </Button>
                ))}
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  )
}
