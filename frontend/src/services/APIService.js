import axios from 'axios'

const API_BASE_URL = process.env.VUE_APP_API_URL || 'http://localhost:8000/api/v1'

const apiClient = axios.create({
    baseURL: API_BASE_URL,
    timeout: 10000,
    headers: {
        'Content-Type': 'application/json',
    }
})

// Request interceptor for adding auth tokens if needed
apiClient.interceptors.request.use(
    (config) => {
        // Add auth token here if needed in the future
        return config
    },
    (error) => {
        return Promise.reject(error)
    }
)

// Response interceptor for handling errors
apiClient.interceptors.response.use(
    (response) => {
        return response
    },
    (error) => {
        console.error('API Error:', error.response?.data || error.message)
        return Promise.reject(error)
    }
)

export default {
    // Health check
    async checkHealth() {
        try {
            const response = await apiClient.get('/health')
            return response.data
        } catch (error) {
            throw new Error('Backend service is unavailable')
        }
    },

    // Topics
    async getTopics() {
        const response = await apiClient.get('/topics')
        return response.data
    },

    // Trends
    async getTopicTrends(topic, params = {}) {
        const response = await apiClient.get(`/trends/${topic}`, { params })
        return response.data
    },

    async getTopicAnalysis(topic, params = {}) {
        try {
            const response = await apiClient.get(`/trends/${topic}/analysis`, { params })
            return response.data
        } catch (error) {
            // Fallback with mock data for testing when backend is unavailable
            console.warn('Backend unavailable, using mock data for topic analysis')
            return this.getMockTopicAnalysis(topic)
        }
    },

    // Mock data for testing when backend is unavailable
    getMockTopicAnalysis(topic) {
        const mockData = {
            topic: topic,
            date_range: {
                start_date: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString(),
                end_date: new Date().toISOString()
            },
            metrics: {
                total_articles: 245,
                active_countries: 12,
                avg_sentiment: 0.15,
                peak_date: '2024-01-15',
                peak_count: 45,
                trend_direction: 'rising'
            },
            time_series: this.generateMockTimeSeries(),
            top_stories: this.generateMockStories(topic),
            top_countries: [
                { country: 'United States', article_count: 89 },
                { country: 'United Kingdom', article_count: 56 },
                { country: 'Germany', article_count: 34 },
                { country: 'France', article_count: 28 },
                { country: 'Canada', article_count: 22 }
            ],
            analysis_timestamp: new Date().toISOString()
        }

        return mockData
    },

    generateMockTimeSeries() {
        const series = []
        const now = new Date()

        for (let i = 29; i >= 0; i--) {
            const date = new Date(now - i * 24 * 60 * 60 * 1000)
            const dateStr = date.toISOString().split('T')[0]
            const count = Math.floor(Math.random() * 50) + 10
            const sentiment = (Math.random() - 0.5) * 0.8

            series.push({
                date: dateStr,
                article_count: count,
                sentiment_avg: sentiment
            })
        }

        return series
    },

    generateMockStories(topic) {
        const stories = [
            {
                id: 1,
                title: `Breaking: Major developments in ${topic} sector`,
                url: 'https://example.com/story1',
                source: 'Global News Network',
                country: 'United States',
                published_date: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
                sentiment_score: 0.3,
                summary: `Latest updates show significant progress in ${topic}. Industry experts weigh in on the implications for global markets and policy changes.`
            },
            {
                id: 2,
                title: `Analysis: ${topic} trends reshaping international landscape`,
                url: 'https://example.com/story2',
                source: 'International Herald',
                country: 'United Kingdom',
                published_date: new Date(Date.now() - 5 * 60 * 60 * 1000).toISOString(),
                sentiment_score: -0.1,
                summary: `Comprehensive analysis of how recent ${topic} developments are influencing global strategies and regional partnerships.`
            },
            {
                id: 3,
                title: `Expert Opinion: Future of ${topic} in emerging markets`,
                url: 'https://example.com/story3',
                source: 'Economic Times',
                country: 'Germany',
                published_date: new Date(Date.now() - 8 * 60 * 60 * 1000).toISOString(),
                sentiment_score: 0.5,
                summary: `Leading economists discuss the potential impact of ${topic} innovations on developing economies and investment opportunities.`
            },
            {
                id: 4,
                title: `Policy Update: New regulations in ${topic} announced`,
                url: 'https://example.com/story4',
                source: 'Policy Review',
                country: 'France',
                published_date: new Date(Date.now() - 12 * 60 * 60 * 1000).toISOString(),
                sentiment_score: 0.0,
                summary: `Government officials outline new framework for ${topic} governance, addressing key stakeholder concerns and implementation timeline.`
            },
            {
                id: 5,
                title: `Market Watch: ${topic} stocks surge amid positive outlook`,
                url: 'https://example.com/story5',
                source: 'Financial Wire',
                country: 'Canada',
                published_date: new Date(Date.now() - 18 * 60 * 60 * 1000).toISOString(),
                sentiment_score: 0.7,
                summary: `Stock markets respond favorably to recent ${topic} announcements, with several major companies reporting strong quarterly results.`
            }
        ]

        return stories
    },

    async getCountryTopics(country, params = {}) {
        const response = await apiClient.get(`/countries/${country}/topics`, { params })
        return response.data
    },

    async getCountriesTrends(params = {}) {
        const response = await apiClient.get('/countries/trends', { params })
        return response.data
    },

    async getLiveTrends(limit = 10) {
        const response = await apiClient.get('/live', { params: { limit } })
        return response.data
    },

    // Predictions
    async getPredictions(params = {}) {
        const response = await apiClient.get('/predictions', { params })
        return response.data
    },

    // Articles
    async searchArticles(searchParams) {
        const response = await apiClient.get('/articles/search', { params: searchParams })
        return response.data
    },

    async getRecentArticles(params = {}) {
        const response = await apiClient.get('/articles/recent', { params })
        return response.data
    },

    // Statistics
    async getStatistics() {
        const response = await apiClient.get('/statistics')
        return response.data
    },

    // Admin functions
    async refreshNews() {
        const response = await apiClient.post('/refresh')
        return response.data
    }
} 