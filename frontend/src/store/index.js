import { createStore } from 'vuex'
import APIService from '@/services/APIService'

export default createStore({
    state: {
        // Connection status
        isBackendConnected: false,
        isLoading: false,
        error: null,

        // News topics and trends
        availableTopics: [],
        selectedTopic: 'Politics & Elections',
        selectedCountry: null,
        dateRange: {
            start: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0] + 'T00:00:00',
            end: new Date().toISOString().split('T')[0] + 'T23:59:59'
        },

        // Trend data
        liveTrends: [],
        topicTrends: [],
        topicAnalysis: null,
        countriesTrends: [], // For map visualization
        countryTopics: {},
        predictions: [],

        // Statistics
        statistics: {},

        // UI state
        mapView: {
            center: [20, 0],
            zoom: 2
        },
        showPredictions: false,
        refreshInterval: null
    },

    mutations: {
        SET_BACKEND_CONNECTED(state, status) {
            state.isBackendConnected = status
        },

        SET_LOADING(state, status) {
            state.isLoading = status
        },

        SET_ERROR(state, error) {
            state.error = error
        },

        SET_AVAILABLE_TOPICS(state, topics) {
            state.availableTopics = topics
        },

        SET_SELECTED_TOPIC(state, topic) {
            state.selectedTopic = topic
        },

        SET_SELECTED_COUNTRY(state, country) {
            state.selectedCountry = country
        },

        SET_DATE_RANGE(state, dateRange) {
            state.dateRange = dateRange
        },

        SET_LIVE_TRENDS(state, trends) {
            state.liveTrends = trends
        },

        SET_TOPIC_TRENDS(state, trends) {
            state.topicTrends = trends
        },

        SET_TOPIC_ANALYSIS(state, analysis) {
            state.topicAnalysis = analysis
        },

        SET_COUNTRY_TOPICS(state, { country, topics }) {
            state.countryTopics = {
                ...state.countryTopics,
                [country]: topics
            }
        },

        SET_PREDICTIONS(state, predictions) {
            state.predictions = predictions
        },

        SET_COUNTRIES_TRENDS(state, countriesTrends) {
            state.countriesTrends = countriesTrends
        },

        SET_STATISTICS(state, statistics) {
            state.statistics = statistics
        },

        SET_MAP_VIEW(state, view) {
            state.mapView = view
        },

        SET_SHOW_PREDICTIONS(state, show) {
            state.showPredictions = show
        },

        SET_REFRESH_INTERVAL(state, interval) {
            state.refreshInterval = interval
        }
    },

    actions: {
        async checkBackendConnection({ commit }) {
            try {
                await APIService.checkHealth()
                commit('SET_BACKEND_CONNECTED', true)
                commit('SET_ERROR', null)
                return true
            } catch (error) {
                commit('SET_BACKEND_CONNECTED', false)
                commit('SET_ERROR', 'Cannot connect to backend service')
                return false
            }
        },

        async loadAvailableTopics({ commit }) {
            try {
                commit('SET_LOADING', true)
                const response = await APIService.getTopics()
                commit('SET_AVAILABLE_TOPICS', response.topics || [])
                commit('SET_ERROR', null)
            } catch (error) {
                commit('SET_ERROR', 'Failed to load topics')
                console.error('Error loading topics:', error)
            } finally {
                commit('SET_LOADING', false)
            }
        },

        async loadLiveTrends({ commit }, limit = 10) {
            try {
                const response = await APIService.getLiveTrends(limit)
                commit('SET_LIVE_TRENDS', response.trending_topics || [])
                commit('SET_ERROR', null)
            } catch (error) {
                commit('SET_ERROR', 'Failed to load live trends')
                console.error('Error loading live trends:', error)
            }
        },

        async loadTopicTrends({ commit, state }, params = {}) {
            if (!state.selectedTopic) return

            try {
                commit('SET_LOADING', true)
                const trends = await APIService.getTopicTrends(state.selectedTopic, {
                    country: state.selectedCountry,
                    start_date: state.dateRange.start,
                    end_date: state.dateRange.end,
                    ...params
                })
                commit('SET_TOPIC_TRENDS', trends)
                commit('SET_ERROR', null)
            } catch (error) {
                commit('SET_ERROR', 'Failed to load topic trends')
                console.error('Error loading topic trends:', error)
            } finally {
                commit('SET_LOADING', false)
            }
        },

        async loadTopicAnalysis({ commit, state }, params = {}) {
            if (!state.selectedTopic) return

            try {
                commit('SET_LOADING', true)
                const analysis = await APIService.getTopicAnalysis(state.selectedTopic, {
                    start_date: state.dateRange.start,
                    end_date: state.dateRange.end,
                    ...params
                })
                commit('SET_TOPIC_ANALYSIS', analysis)
                commit('SET_ERROR', null)
            } catch (error) {
                // Don't set error for mock data fallback
                console.warn('Using fallback data for topic analysis:', error.message)
                commit('SET_ERROR', null)
            } finally {
                commit('SET_LOADING', false)
            }
        },

        async loadCountryTopics({ commit, state }, country) {
            try {
                const response = await APIService.getCountryTopics(country, {
                    start_date: state.dateRange.start,
                    end_date: state.dateRange.end
                })
                commit('SET_COUNTRY_TOPICS', {
                    country,
                    topics: response.topics || []
                })
                commit('SET_ERROR', null)
            } catch (error) {
                console.error(`Error loading topics for ${country}:`, error)
            }
        },

        async loadPredictions({ commit, state }, params = {}) {
            try {
                commit('SET_LOADING', true)
                const predictions = await APIService.getPredictions({
                    topic: state.selectedTopic,
                    country: state.selectedCountry,
                    ...params
                })
                commit('SET_PREDICTIONS', predictions)
                commit('SET_ERROR', null)
            } catch (error) {
                commit('SET_ERROR', 'Failed to load predictions')
                console.error('Error loading predictions:', error)
            } finally {
                commit('SET_LOADING', false)
            }
        },

        async loadCountriesTrends({ commit, state }, params = {}) {
            try {
                commit('SET_LOADING', true)
                const countriesTrends = await APIService.getCountriesTrends({
                    topic: state.selectedTopic,
                    start_date: state.dateRange.start,
                    end_date: state.dateRange.end,
                    ...params
                })
                commit('SET_COUNTRIES_TRENDS', countriesTrends)
                commit('SET_ERROR', null)
            } catch (error) {
                commit('SET_ERROR', 'Failed to load countries trends')
                console.error('Error loading countries trends:', error)
            } finally {
                commit('SET_LOADING', false)
            }
        },

        async loadStatistics({ commit }) {
            try {
                const statistics = await APIService.getStatistics()
                commit('SET_STATISTICS', statistics)
                commit('SET_ERROR', null)
            } catch (error) {
                commit('SET_ERROR', 'Failed to load statistics')
                console.error('Error loading statistics:', error)
            }
        },

        async refreshNews({ dispatch }) {
            try {
                await APIService.refreshNews()
                // Reload all data after refresh
                await Promise.all([
                    dispatch('loadLiveTrends'),
                    dispatch('loadTopicTrends'),
                    dispatch('loadStatistics')
                ])
            } catch (error) {
                console.error('Error refreshing news:', error)
            }
        },

        selectTopic({ commit, dispatch }, topic) {
            commit('SET_SELECTED_TOPIC', topic)
            dispatch('loadTopicTrends')
            dispatch('loadTopicAnalysis')
        },

        selectCountry({ commit, dispatch }, country) {
            commit('SET_SELECTED_COUNTRY', country)
            if (country) {
                dispatch('loadCountryTopics', country)
            }
            dispatch('loadTopicTrends')
        },

        updateDateRange({ commit, dispatch }, dateRange) {
            commit('SET_DATE_RANGE', dateRange)
            dispatch('loadTopicTrends')
        },

        startAutoRefresh({ commit, dispatch }, intervalMs = 300000) { // 5 minutes
            const interval = setInterval(() => {
                dispatch('loadLiveTrends')
            }, intervalMs)
            commit('SET_REFRESH_INTERVAL', interval)
        },

        stopAutoRefresh({ commit, state }) {
            if (state.refreshInterval) {
                clearInterval(state.refreshInterval)
                commit('SET_REFRESH_INTERVAL', null)
            }
        }
    },

    getters: {
        isConnected: state => state.isBackendConnected,
        isLoading: state => state.isLoading,
        currentError: state => state.error,

        availableTopics: state => state.availableTopics,
        selectedTopic: state => state.selectedTopic,
        selectedCountry: state => state.selectedCountry,

        liveTrends: state => state.liveTrends,
        topicTrends: state => state.topicTrends,
        topicAnalysis: state => state.topicAnalysis,
        countriesTrends: state => state.countriesTrends,
        predictions: state => state.predictions,

        topCountriesByArticles: state => {
            return state.statistics.top_countries || []
        },

        recentActivity: state => state.statistics.recent_activity_1h || 0,

        trendingTopicsMap: state => {
            const map = new Map()
            state.liveTrends.forEach(trend => {
                const country = trend.country
                if (!map.has(country)) {
                    map.set(country, [])
                }
                map.get(country).push(trend)
            })
            return map
        }
    }
}) 