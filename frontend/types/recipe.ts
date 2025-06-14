export interface Recipe {
  id: number
  name: string
  category: string
  method: string
  description: string
  reason: string
}

export interface RecommendationResponse {
  fridge: string[]
  recommendations: Recipe[]
}
