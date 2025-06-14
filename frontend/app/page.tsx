// app/components/CleanRecipeRecommender.tsx
"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { ChefHat, Search, User, Refrigerator, Plus, X } from "lucide-react"
import type { Recipe, RecommendationResponse } from "../types/recipe"
import { Label } from "@/components/ui/label"

export default function CleanRecipeRecommender() {
  // recipes / fridge
  const [recipes, setRecipes] = useState<Recipe[]>([])
  const [fridgeItems, setFridgeItems] = useState<string[]>([])
  const [hasSearched, setHasSearched] = useState(false)

  // form & UI state
  const [query, setQuery] = useState("")
  const [newIngredient, setNewIngredient] = useState("")
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [fridgeLoading, setFridgeLoading] = useState(false)
  const [addingIngredient, setAddingIngredient] = useState(false)
  const [deletingIngredient, setDeletingIngredient] = useState<string | null>(null)

  // auth state
  const [isLoggedIn, setIsLoggedIn] = useState(false)
  const [username, setUsername] = useState("")
  const [loginUsername, setLoginUsername] = useState("")
  const [loginEmail, setLoginEmail] = useState("")
  const [loginLoading, setLoginLoading] = useState(false)
  const [logoutLoading, setLogoutLoading] = useState(false)
  const [isSignupMode, setIsSignupMode] = useState(false)
  const [signupUsername, setSignupUsername] = useState("")
  const [signupEmail, setSignupEmail] = useState("")
  const [signupLoading, setSignupLoading] = useState(false)
  const [userId, setUserId] = useState<number | null>(null)

  // ▶ 전체 상태 초기화 (첫 화면으로 돌아가기)
  const handleReset = () => {
    setHasSearched(false)
    setRecipes([])
    setQuery("")
    setError(null)
  }

  // (0) 한글만 남기고 나머지 제거하는 헬퍼
const normalizeHangul = (s: string) =>
  s.replace(/[^ㄱ-ㅣ가-힣]/g, "").trim();

// (2) 냉장고 재료와 매칭 (정규화 후 완전 일치할 때만)
const findMatchingIngredients = (
  description: string,
  fridgeItems: string[]
) => {
  const tokens = description.split(",").map((t) => t.trim());
  const matches: { ingredient: string; fridgeItem: string }[] = [];

  tokens.forEach((token) => {
    const normToken = normalizeHangul(token);
    fridgeItems.forEach((fridgeItem) => {
      const normFridge = normalizeHangul(fridgeItem);
      if (normToken && normToken === normFridge) {
        matches.push({ ingredient: token, fridgeItem });
      }
    });
  });

  return matches;
};

// (3) 하이라이트도 같은 로직
const highlightIngredients = (
  description: string,
  fridgeItems: string[]
) => {
  return description
    .split(",")
    .map((t) => {
      const raw = t.trim();
      const normRaw = normalizeHangul(raw);

      // 정규화 문자열이 냉장고 재료 중 하나와 완전 일치하면 하이라이트
      const isMatch = fridgeItems.some(
        (fridgeItem) => normRaw === normalizeHangul(fridgeItem)
      );

      return isMatch
        ? `<mark class="bg-green-100 text-green-800 px-1 rounded">${raw}</mark>`
        : raw;
    })
    .join(", ");
};

  // ▶ 회원가입
  const handleSignup = async () => {
    if (!signupUsername.trim() || !signupEmail.trim()) return
    setSignupLoading(true)
    setError(null)
    try {
      const res = await fetch("/api/users", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username: signupUsername, email: signupEmail }),
      })
      if (!res.ok) throw new Error(`회원가입 실패: ${res.status}`)
      const user = await res.json()
      setIsLoggedIn(true)
      setUsername(user.username)
      setUserId(user.id)
      setSignupUsername("")
      setSignupEmail("")
      setIsSignupMode(false)
    } catch (e: any) {
      console.error(e)
      setError(e.message)
    } finally {
      setSignupLoading(false)
    }
  }

  // ▶ 로그인
  const handleLogin = async () => {
    if (!loginUsername.trim() || !loginEmail.trim()) return
    setLoginLoading(true)
    setError(null)
    try {
      const res = await fetch("/api/users/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username: loginUsername, email: loginEmail }),
      })
      if (!res.ok) throw new Error(`로그인 실패: ${res.status}`)
      const user = await res.json()
      setIsLoggedIn(true)
      setUsername(user.username)
      setUserId(user.id)
      setLoginUsername("")
      setLoginEmail("")
    } catch (e: any) {
      console.error(e)
      setError(e.message)
    } finally {
      setLoginLoading(false)
    }
  }
  const handleLogout = () => {
    setIsLoggedIn(false)
    setUsername("")
  }

  // ▶ 레시피 추천
  const fetchRecommendations = async () => {
    if (!query.trim()) return
    setLoading(true)
    setError(null)
    try {
      const response = await fetch("/api/rag/recommend", {
        method: "POST",
        headers: {
          accept: "application/json",
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          user_id: userId,
          query,
          top_k: 20,
          boost: 0.2,
        }),
      })

      if (response.status === 422) {
        setError("로그인 후 레시피 추천을 이용해주세요.")
        return
      }

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const data: RecommendationResponse = await response.json()
      setRecipes(data.recommendations)
      setFridgeItems(data.fridge)
      setHasSearched(true)
    } catch (err) {
      setHasSearched(true)
    } finally {
      setLoading(false)
    }
  }

  // ▶ 냉장고 재료 조회
  const loadFridgeItems = async () => {
    if (userId == null) return
    setFridgeLoading(true)
    try {
      const res = await fetch(`/api/user_ingredients/${userId}`)
      if (!res.ok) throw new Error()
      const data: { name: string; quantity: number }[] = await res.json()
      setFridgeItems(data.map((d) => d.name))
    } catch {
      console.error("Failed to load fridge items")
    } finally {
      setFridgeLoading(false)
    }
  }

  // ▶ userId 세팅(=로그인 or 회원가입) 이후 자동으로 냉장고 재료 조회
  useEffect(() => {
    if (userId !== null) {
      loadFridgeItems()
    }
  }, [userId])

  // ▶ 냉장고 재료 삭제
  const removeIngredient = async (ingredient: string) => {
    if (userId == null) return
    setDeletingIngredient(ingredient)
    try {
      await fetch(`/api/user_ingredients/${userId}/${encodeURIComponent(ingredient)}`, {
        method: "DELETE",
      })
      setFridgeItems((prev) => prev.filter((i) => i !== ingredient))
    } catch {
      console.error("Failed to remove ingredient")
    } finally {
      setDeletingIngredient(null)
    }
  }

  // ▶ 냉장고 재료 추가
  const addIngredient = async () => {
    const ing = newIngredient.trim()
    if (!ing || fridgeItems.includes(ing)) return
    setAddingIngredient(true)
    setError(null)
    try {
      const res = await fetch("/api/user_ingredients", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: userId, name: ing, quantity: 1 }),
      })
      if (!res.ok) throw new Error(`Status ${res.status}`)
      setFridgeItems((prev) => [...prev, ing])
      setNewIngredient("")
    } catch {
      setError("재료 추가 실패")
    } finally {
      setAddingIngredient(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-4xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button
              onClick={handleReset}
              className="flex items-center gap-3 focus:outline-none"
            >
              <div className="w-10 h-10 bg-gray-900 rounded-lg flex items-center justify-center">
                <ChefHat className="w-6 h-6 text-white" />
              </div>
              <h1 className="text-2xl font-bold text-gray-900 cursor-pointer">
                레시피 추천
              </h1>
            </button>
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
                    <DialogTitle>{isSignupMode ? "회원가입" : "로그인"}</DialogTitle>
                  </DialogHeader>
                  <div className="space-y-4">
                    {isSignupMode ? (
                      // 회원가입 폼
                      <>
                        <div className="space-y-2">
                          <Label htmlFor="signup-email">이메일</Label>
                        <Input
                            id="signup-email"
                            type="email"
                          value={signupEmail}
                          onChange={(e) => setSignupEmail(e.target.value)}
                            placeholder="이메일을 입력하세요"
                          disabled={signupLoading}
                        />
                        </div>
                        <div className="space-y-2">
                          <Label htmlFor="signup-username">사용자명</Label>
                        <Input
                            id="signup-username"
                          value={signupUsername}
                          onChange={(e) => setSignupUsername(e.target.value)}
                            placeholder="사용자명을 입력하세요"
                          disabled={signupLoading}
                        />
                        </div>
                        <Button
                          onClick={handleSignup}
                          className="w-full"
                          disabled={
                            !signupUsername.trim() || !signupEmail.trim() || signupLoading
                          }
                        >
                          {signupLoading ? (
                            <>
                              <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2" />
                              회원가입 중...
                            </>
                          ) : (
                            "회원가입"
                          )}
                        </Button>
                        <div className="text-center">
                          <Button
                            variant="ghost"
                            onClick={() => setIsSignupMode(false)}
                            className="text-sm text-gray-600 hover:text-gray-900"
                            disabled={signupLoading}
                          >
                            이미 계정이 있으신가요? 로그인하기
                        </Button>
                        </div>
                      </>
                    ) : (
                      // 로그인 폼
                      <>
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
                      <Label htmlFor="login-email">이메일</Label>
                        <Input
                        id="login-email"
                        type="email"
                            value={loginEmail}
                            onChange={(e) => setLoginEmail(e.target.value)}
                        placeholder="이메일을 입력하세요"
                          disabled={loginLoading}
                        />
                        </div>
                    {error && <p className="text-red-600 text-center">{error}</p>}
                        <Button
                          onClick={handleLogin}
                          className="w-full"
                      disabled={!loginUsername.trim() || !loginEmail.trim() || loginLoading}
                        >
                          {loginLoading ? (
                            <>
                              <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2" />
                              로그인 중...
                            </>
                          ) : (
                            "로그인"
                          )}
                        </Button>
                        <div className="text-center">
                          <Button
                            variant="ghost"
                            onClick={() => setIsSignupMode(true)}
                            className="text-sm text-gray-600 hover:text-gray-900"
                            disabled={loginLoading}
                          >
                            계정이 없으신가요? 회원가입하기
                        </Button>
                        </div>
                      </>
                    )}
                  </div>
                </DialogContent>
              </Dialog>
            ) : (
              <Button
                onClick={handleLogout}
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
        {hasSearched && !loading && recipes.length > 0 && (
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
              <p className="text-gray-600 mb-6">냉장고에 있는 재료를 바탕으로 다양한 레시피를 추천해드려요.</p>
              <div className="flex flex-wrap justify-center gap-2">
                {["과일 샐러드", "해물 풍미가 살아있는 얼큰한 찌개", "고소한 후식", "건강한 밥 레시피"].map((suggestion) => (
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
