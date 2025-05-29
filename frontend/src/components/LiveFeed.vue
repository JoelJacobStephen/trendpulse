<template>
  <div class="bg-white rounded-lg shadow-md p-6">
    <div class="flex justify-between items-center mb-4">
      <h3 class="text-xl font-semibold text-gray-800">
        🔴 Live Trending Topics
      </h3>
      <div class="flex items-center gap-2">
        <div class="flex items-center gap-2">
          <div class="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
          <span class="text-sm text-gray-600">Live</span>
        </div>
        <button
          @click="toggleAutoRefresh"
          :class="[
            'px-3 py-1 text-xs rounded transition-all',
            autoRefresh
              ? 'bg-green-100 text-green-700 hover:bg-green-200'
              : 'bg-gray-100 text-gray-700 hover:bg-gray-200',
          ]"
        >
          {{ autoRefresh ? "Auto-refresh ON" : "Auto-refresh OFF" }}
        </button>
      </div>
    </div>

    <!-- Loading state -->
    <div v-if="loading && liveTrends.length === 0" class="text-center py-8">
      <div
        class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-2"
      ></div>
      <p class="text-sm text-gray-600">Loading live trends...</p>
    </div>

    <!-- Error state -->
    <div v-else-if="error" class="text-center py-8">
      <div class="text-red-500 text-3xl mb-2">⚠️</div>
      <p class="text-red-600 text-sm">{{ error }}</p>
    </div>

    <!-- Live trends list -->
    <div v-else-if="liveTrends.length > 0" class="space-y-3">
      <div
        v-for="(trend, index) in liveTrends"
        :key="`${trend.topic}-${trend.country}`"
        @click="selectTrend(trend)"
        class="p-4 border border-gray-200 rounded-lg hover:shadow-md cursor-pointer transition-all group"
        :class="isSelectedTrend(trend) ? 'border-primary bg-blue-50' : ''"
      >
        <div class="flex items-start justify-between">
          <div class="flex-1">
            <div class="flex items-center gap-2 mb-1">
              <span class="text-sm font-bold text-gray-500"
                >#{{ index + 1 }}</span
              >
              <h4
                class="font-semibold text-gray-800 group-hover:text-primary transition-colors"
              >
                {{ formatTopicName(trend.topic) }}
              </h4>
              <span
                class="text-xs px-2 py-1 rounded-full"
                :class="getTrendBadgeClass(trend.trend_score)"
              >
                {{ formatTrendScore(trend.trend_score) }}
              </span>
            </div>

            <div class="flex items-center gap-4 text-sm text-gray-600 mb-2">
              <span class="flex items-center gap-1">
                🌍 {{ trend.country }}
                <span
                  v-if="trend.countries_count > 1"
                  class="text-xs text-gray-500"
                >
                  (+{{ trend.countries_count - 1 }} more)
                </span>
              </span>
              <span class="flex items-center gap-1">
                📄 {{ trend.article_count }} articles
              </span>
              <span
                v-if="trend.sentiment !== undefined"
                class="flex items-center gap-1"
              >
                {{ getSentimentEmoji(trend.sentiment) }}
                {{ formatSentiment(trend.sentiment) }}
              </span>
            </div>

            <!-- Trend change indicator -->
            <div
              v-if="trend.change_24h !== undefined"
              class="flex items-center gap-1 text-xs"
            >
              <span :class="getChangeClass(trend.change_24h)">
                {{ getChangeIcon(trend.change_24h) }}
                {{ formatChange(trend.change_24h) }}% (24h)
              </span>
            </div>
          </div>

          <!-- Trend score visualization -->
          <div class="flex flex-col items-end ml-4">
            <div class="w-16 h-2 bg-gray-200 rounded-full overflow-hidden">
              <div
                class="h-full rounded-full transition-all duration-300"
                :class="getTrendBarClass(trend.trend_score)"
                :style="{ width: `${Math.min(trend.trend_score * 100, 100)}%` }"
              ></div>
            </div>
            <span class="text-xs text-gray-500 mt-1">
              {{ Math.round(trend.trend_score * 100) }}%
            </span>
          </div>
        </div>
      </div>
    </div>

    <!-- No data state -->
    <div v-else class="text-center py-8">
      <div class="text-gray-400 text-3xl mb-2">📊</div>
      <p class="text-gray-600 mb-1">No trending topics yet</p>
      <p class="text-sm text-gray-500">Check back in a few minutes</p>
    </div>

    <!-- Last updated info -->
    <div
      v-if="lastUpdated"
      class="mt-4 pt-4 border-t border-gray-200 text-center"
    >
      <p class="text-xs text-gray-500">
        Last updated: {{ formatLastUpdated(lastUpdated) }}
        <span v-if="autoRefresh" class="ml-2">
          • Next update in {{ nextUpdateIn }}s
        </span>
      </p>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, onMounted, onUnmounted } from "vue";
import { useStore } from "vuex";
import { formatDistanceToNow } from "date-fns";

const store = useStore();

// Refs
const autoRefresh = ref(true);
const nextUpdateIn = ref(300); // 5 minutes
const countdownInterval = ref(null);

// Computed
const loading = computed(() => store.getters.isLoading);
const error = computed(() => store.getters.currentError);
const liveTrends = computed(() => store.getters.liveTrends.slice(0, 10)); // Top 10
const selectedTopic = computed(() => store.getters.selectedTopic);
const selectedCountry = computed(() => store.getters.selectedCountry);

const lastUpdated = computed(() => {
  const trends = store.getters.liveTrends;
  return trends.length > 0 ? new Date() : null;
});

// Methods
const formatTopicName = (topic) => {
  return (
    topic
      ?.replace(/_/g, " ")
      .split(" ")
      .map((word) => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
      .join(" ") || "Unknown"
  );
};

const formatTrendScore = (score) => {
  if (score > 0.8) return "Viral";
  if (score > 0.6) return "Hot";
  if (score > 0.4) return "Rising";
  if (score > 0.2) return "Stable";
  return "Low";
};

const getTrendBadgeClass = (score) => {
  if (score > 0.8) return "bg-red-500 text-white";
  if (score > 0.6) return "bg-red-100 text-red-700";
  if (score > 0.4) return "bg-orange-100 text-orange-700";
  if (score > 0.2) return "bg-green-100 text-green-700";
  return "bg-gray-100 text-gray-700";
};

const getTrendBarClass = (score) => {
  if (score > 0.8) return "bg-red-500";
  if (score > 0.6) return "bg-red-400";
  if (score > 0.4) return "bg-orange-400";
  if (score > 0.2) return "bg-green-400";
  return "bg-gray-400";
};

const formatSentiment = (sentiment) => {
  if (sentiment > 0.1) return "Positive";
  if (sentiment < -0.1) return "Negative";
  return "Neutral";
};

const getSentimentEmoji = (sentiment) => {
  if (sentiment > 0.1) return "😊";
  if (sentiment < -0.1) return "😟";
  return "😐";
};

const formatChange = (change) => {
  return change > 0 ? `+${change.toFixed(1)}` : change.toFixed(1);
};

const getChangeIcon = (change) => {
  if (change > 0) return "📈";
  if (change < 0) return "📉";
  return "➡️";
};

const getChangeClass = (change) => {
  if (change > 0) return "text-green-600";
  if (change < 0) return "text-red-600";
  return "text-gray-600";
};

const isSelectedTrend = (trend) => {
  return (
    selectedTopic.value === trend.topic &&
    (selectedCountry.value === trend.country || !selectedCountry.value)
  );
};

const selectTrend = (trend) => {
  store.dispatch("selectTopic", trend.topic);
  if (trend.country !== selectedCountry.value) {
    store.dispatch("selectCountry", trend.country);
  }
};

const formatLastUpdated = (date) => {
  return formatDistanceToNow(date, { addSuffix: true });
};

const toggleAutoRefresh = () => {
  autoRefresh.value = !autoRefresh.value;
  if (autoRefresh.value) {
    store.dispatch("startAutoRefresh");
    startCountdown();
  } else {
    store.dispatch("stopAutoRefresh");
    stopCountdown();
  }
};

const startCountdown = () => {
  nextUpdateIn.value = 300; // 5 minutes
  countdownInterval.value = setInterval(() => {
    nextUpdateIn.value--;
    if (nextUpdateIn.value <= 0) {
      nextUpdateIn.value = 300; // Reset
    }
  }, 1000);
};

const stopCountdown = () => {
  if (countdownInterval.value) {
    clearInterval(countdownInterval.value);
    countdownInterval.value = null;
  }
};

// Lifecycle
onMounted(() => {
  store.dispatch("loadLiveTrends");
  if (autoRefresh.value) {
    store.dispatch("startAutoRefresh");
    startCountdown();
  }
});

onUnmounted(() => {
  store.dispatch("stopAutoRefresh");
  stopCountdown();
});
</script>
