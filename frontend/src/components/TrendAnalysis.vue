<template>
  <div class="mt-8 grid grid-cols-1 lg:grid-cols-2 gap-6">
    <!-- Topic Analysis -->
    <div class="bg-white rounded-lg shadow-md p-6">
      <h3
        class="text-xl font-semibold text-gray-800 mb-4 flex items-center gap-2"
      >
        📊 Topic Analysis: {{ formatTopicName(selectedTopic) }}
      </h3>

      <div v-if="loading" class="text-center py-8">
        <div
          class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-2"
        ></div>
        <p class="text-sm text-gray-600">Analyzing trends...</p>
      </div>

      <div v-else-if="topicAnalysis" class="space-y-4">
        <!-- Key metrics -->
        <div class="grid grid-cols-2 gap-4">
          <div class="text-center p-4 bg-blue-50 rounded-lg">
            <div class="text-2xl font-bold text-blue-600">
              {{ topicAnalysis.metrics.total_articles }}
            </div>
            <div class="text-sm text-gray-600">Total Articles</div>
          </div>
          <div class="text-center p-4 bg-green-50 rounded-lg">
            <div class="text-2xl font-bold text-green-600">
              {{ topicAnalysis.metrics.active_countries }}
            </div>
            <div class="text-sm text-gray-600">Active Countries</div>
          </div>
        </div>

        <!-- Trend Chart -->
        <div class="h-64">
          <canvas ref="trendChart"></canvas>
        </div>

        <!-- Trend summary -->
        <div class="p-4 bg-gray-50 rounded-lg">
          <h4 class="font-semibold mb-2">Trend Summary</h4>
          <div class="text-sm text-gray-700 space-y-1">
            <p>
              <strong>Peak activity:</strong>
              {{ formatDate(topicAnalysis.metrics.peak_date) || "N/A" }}
              <span
                v-if="topicAnalysis.metrics.peak_count"
                class="text-gray-500"
              >
                ({{ topicAnalysis.metrics.peak_count }} articles)
              </span>
            </p>
            <p>
              <strong>Average sentiment:</strong>
              <span
                :class="getSentimentClass(topicAnalysis.metrics.avg_sentiment)"
              >
                {{ formatSentiment(topicAnalysis.metrics.avg_sentiment) }}
              </span>
            </p>
            <p>
              <strong>Trend direction:</strong>
              <span
                :class="
                  getTrendDirectionClass(topicAnalysis.metrics.trend_direction)
                "
              >
                {{
                  formatTrendDirection(topicAnalysis.metrics.trend_direction)
                }}
              </span>
            </p>
          </div>
        </div>

        <!-- Top Countries -->
        <div
          v-if="
            topicAnalysis.top_countries &&
            topicAnalysis.top_countries.length > 0
          "
          class="space-y-2"
        >
          <h4 class="font-semibold">Top Countries</h4>
          <div class="space-y-1">
            <div
              v-for="country in topicAnalysis.top_countries.slice(0, 5)"
              :key="country.country"
              class="flex justify-between items-center text-sm"
            >
              <span>{{ country.country }}</span>
              <span class="text-gray-600"
                >{{ country.article_count }} articles</span
              >
            </div>
          </div>
        </div>
      </div>

      <div v-else class="text-center py-8 text-gray-500">
        <div class="text-3xl mb-2">📈</div>
        <p>Select a topic to see analysis</p>
      </div>
    </div>

    <!-- Top Stories -->
    <div class="bg-white rounded-lg shadow-md p-6">
      <h3
        class="text-xl font-semibold text-gray-800 mb-4 flex items-center gap-2"
      >
        📰 Top Stories: {{ formatTopicName(selectedTopic) }}
      </h3>

      <div v-if="loading" class="text-center py-8">
        <div
          class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-2"
        ></div>
        <p class="text-sm text-gray-600">Loading stories...</p>
      </div>

      <div
        v-else-if="
          topicAnalysis &&
          topicAnalysis.top_stories &&
          topicAnalysis.top_stories.length > 0
        "
        class="space-y-4"
      >
        <div
          v-for="(story, index) in topicAnalysis.top_stories"
          :key="story.id"
          class="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow cursor-pointer"
          @click="openStory(story.url)"
        >
          <div class="flex items-start justify-between mb-2">
            <div class="flex-1">
              <h4
                class="font-semibold text-gray-800 hover:text-primary transition-colors line-clamp-2"
              >
                {{ story.title }}
              </h4>
              <div class="flex items-center gap-3 text-sm text-gray-600 mt-1">
                <span class="flex items-center gap-1">
                  📰 {{ story.source }}
                </span>
                <span class="flex items-center gap-1">
                  🌍 {{ story.country }}
                </span>
                <span class="flex items-center gap-1">
                  🕒 {{ formatTimeAgo(story.published_date) }}
                </span>
              </div>
            </div>
            <div class="ml-3 flex flex-col items-end">
              <span class="text-xs font-bold text-gray-500"
                >#{{ index + 1 }}</span
              >
              <span
                v-if="story.sentiment_score !== null"
                class="text-xs px-2 py-1 rounded-full mt-1"
                :class="getSentimentBadgeClass(story.sentiment_score)"
              >
                {{ getSentimentEmoji(story.sentiment_score) }}
              </span>
            </div>
          </div>

          <p v-if="story.summary" class="text-sm text-gray-700 line-clamp-3">
            {{ story.summary }}
          </p>

          <div class="mt-2 flex justify-between items-center">
            <span class="text-xs text-gray-500">
              Click to read full article
            </span>
            <span class="text-xs text-blue-600 hover:text-blue-800">
              Read more →
            </span>
          </div>
        </div>
      </div>

      <div v-else class="text-center py-8 text-gray-500">
        <div class="text-3xl mb-2">📰</div>
        <p>No stories available</p>
        <p class="text-sm mt-1">Select a topic to see recent stories</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import {
  computed,
  ref,
  watch,
  onMounted,
  onBeforeUnmount,
  nextTick,
} from "vue";
import { useStore } from "vuex";
import { format, formatDistanceToNow } from "date-fns";
import Chart from "chart.js/auto";

const store = useStore();

// Local state
const trendChart = ref(null);
const chartInstance = ref(null);
const isMounted = ref(false);

// Computed properties
const loading = computed(() => store.getters.isLoading);
const selectedTopic = computed(() => store.getters.selectedTopic);
const topicAnalysis = computed(() => store.getters.topicAnalysis);

// Methods

const formatTopicName = (topic) => {
  return (
    topic
      ?.replace(/_/g, " ")
      .split(" ")
      .map((word) => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
      .join(" ") || "Unknown Topic"
  );
};

const formatDate = (dateStr) => {
  if (!dateStr) return null;
  try {
    return format(new Date(dateStr), "MMM d, yyyy");
  } catch {
    return dateStr;
  }
};

const formatTimeAgo = (dateStr) => {
  if (!dateStr) return "Unknown";
  try {
    return formatDistanceToNow(new Date(dateStr), { addSuffix: true });
  } catch {
    return "Unknown";
  }
};

const formatSentiment = (sentiment) => {
  if (sentiment === null || sentiment === undefined) return "Unknown";
  if (sentiment > 0.1) return "😊 Positive";
  if (sentiment < -0.1) return "😟 Negative";
  return "😐 Neutral";
};

const getSentimentClass = (sentiment) => {
  if (sentiment === null || sentiment === undefined) return "text-gray-600";
  if (sentiment > 0.1) return "text-green-600";
  if (sentiment < -0.1) return "text-red-600";
  return "text-yellow-600";
};

const getSentimentEmoji = (sentiment) => {
  if (sentiment === null || sentiment === undefined) return "😐";
  if (sentiment > 0.1) return "😊";
  if (sentiment < -0.1) return "😟";
  return "😐";
};

const getSentimentBadgeClass = (sentiment) => {
  if (sentiment === null || sentiment === undefined)
    return "bg-gray-100 text-gray-700";
  if (sentiment > 0.1) return "bg-green-100 text-green-700";
  if (sentiment < -0.1) return "bg-red-100 text-red-700";
  return "bg-yellow-100 text-yellow-700";
};

const formatTrendDirection = (direction) => {
  const labels = {
    rising: "↑ Rising",
    falling: "↓ Declining",
    stable: "→ Stable",
  };
  return labels[direction] || "Unknown";
};

const getTrendDirectionClass = (direction) => {
  const classes = {
    rising: "text-green-600",
    falling: "text-red-600",
    stable: "text-blue-600",
  };
  return classes[direction] || "text-gray-600";
};

const openStory = (url) => {
  if (url) {
    window.open(url, "_blank");
  }
};

const initChart = () => {
  // First clean up any existing chart to prevent memory leaks
  if (chartInstance.value) {
    try {
      chartInstance.value.destroy();
    } catch (e) {
      console.warn("Error destroying chart instance:", e);
    }
    chartInstance.value = null;
  }
  
  // Validation checks - early return if conditions aren't met
  if (!isMounted.value) {
    console.log("Chart initialization skipped: component not mounted yet");
    return;
  }
  
  // Check if canvas element exists and is in the DOM
  const canvasElement = trendChart.value;
  if (!canvasElement) {
    console.error("Chart initialization failed: canvas element is null");
    return;
  }
  
  if (!document.body.contains(canvasElement)) {
    console.error("Chart initialization failed: canvas element is not in the DOM");
    return;
  }
  
  // Check if we have data to display
  if (!topicAnalysis.value || !topicAnalysis.value.time_series) {
    console.log("Chart initialization skipped: no time series data available");
    return;
  }
  
  try {
    const timeSeriesData = topicAnalysis.value.time_series;

    if (!timeSeriesData || timeSeriesData.length === 0) {
      console.log("No time series data available");
      return;
    }

    // Validate data before creating chart
    const validData = timeSeriesData.filter(
      (d) => d && d.date && typeof d.article_count === "number"
    );
    if (validData.length === 0) {
      console.warn("No valid chart data available");
      return;
    }

    console.log("Initializing chart with", validData.length, "data points");

    // Get the context directly from the canvas element
    const ctx = canvasElement.getContext('2d');
    if (!ctx) {
      console.error("Failed to get 2D rendering context from canvas");
      return;
    }
    
    chartInstance.value = new Chart(ctx, {
      type: "line",
      data: {
        labels: validData.map((d) => {
          try {
            return format(new Date(d.date), "MMM d");
          } catch (e) {
            return d.date;
          }
        }),
        datasets: [
          {
            label: "Article Count",
            data: validData.map((d) => d.article_count || 0),
            borderColor: "#3B82F6",
            backgroundColor: "rgba(59, 130, 246, 0.1)",
            borderWidth: 2,
            tension: 0.4,
            fill: true,
            pointBackgroundColor: "#3B82F6",
            pointBorderColor: "#ffffff",
            pointBorderWidth: 2,
            pointRadius: 4,
            pointHoverRadius: 6,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        layout: {
          padding: {
            top: 10,
            bottom: 10,
            left: 10,
            right: 10,
          },
        },
        elements: {
          point: {
            hoverRadius: 6,
          },
          line: {
            tension: 0.4,
          },
        },
        plugins: {
          legend: {
            display: false,
          },
          tooltip: {
            mode: "index",
            intersect: false,
            backgroundColor: "rgba(0, 0, 0, 0.8)",
            titleColor: "#ffffff",
            bodyColor: "#ffffff",
            borderColor: "#3B82F6",
            borderWidth: 1,
            callbacks: {
              title: function (context) {
                return `Date: ${context[0].label}`;
              },
              label: function (context) {
                return `Articles: ${context.parsed.y}`;
              },
            },
          },
        },
        scales: {
          y: {
            beginAtZero: true,
            grid: {
              display: true,
              color: "rgba(0, 0, 0, 0.1)",
            },
            ticks: {
              color: "#6B7280",
              font: {
                size: 12,
              },
            },
          },
          x: {
            grid: {
              display: false,
            },
            ticks: {
              color: "#6B7280",
              font: {
                size: 12,
              },
              maxTicksLimit: 10,
            },
          },
        },
        interaction: {
          intersect: false,
          mode: "index",
        },
      },
    });
  } catch (error) {
    console.error("Error initializing chart:", error);
    // Clean up any partial initialization
    if (chartInstance.value) {
      try {
        chartInstance.value.destroy();
      } catch (e) {
        console.warn("Error cleaning up chart after failure:", e);
      }
      chartInstance.value = null;
    }
  }
};

// Watch for changes in topic analysis data
watch(
  () => topicAnalysis.value,
  async (newValue) => {
    if (newValue && newValue.time_series) {
      console.log("Topic analysis data updated, initializing chart...");
      // Give the DOM time to fully render with multiple nextTick calls
      await nextTick();
      await nextTick();
      
      // Use a more reliable approach with multiple attempts
      let attempts = 0;
      const maxAttempts = 3;
      
      const tryInitChart = () => {
        attempts++;
        if (trendChart.value && document.body.contains(trendChart.value)) {
          initChart();
        } else if (attempts < maxAttempts) {
          console.warn(`Canvas element not ready, attempt ${attempts}/${maxAttempts}`);
          setTimeout(tryInitChart, 300);
        } else {
          console.error("Failed to initialize chart after multiple attempts");
        }
      };
      
      // Start the attempt sequence
      setTimeout(tryInitChart, 300);
    }
  },
  { deep: true }
);

watch(
  () => selectedTopic.value,
  (newTopic) => {
    console.log("Selected topic changed to:", newTopic);
    if (newTopic) {
      store.dispatch("loadTopicAnalysis");
    }
  }
);

// Load initial data when component is mounted
onMounted(async () => {
  console.log("TrendAnalysis component mounted");
  isMounted.value = true;

  // Wait for DOM to be fully ready
  await nextTick();
  await nextTick(); // Double nextTick for extra safety
  
  // Load topic analysis data regardless of canvas readiness
  if (selectedTopic.value) {
    console.log("Loading topic analysis for:", selectedTopic.value);
    store.dispatch("loadTopicAnalysis");
    // The watch on topicAnalysis will handle chart initialization
    // once the data is loaded, with retry logic if canvas isn't ready
  }
});

// Cleanup chart on component unmount
onBeforeUnmount(() => {
  console.log("TrendAnalysis component unmounting");
  isMounted.value = false;

  if (chartInstance.value) {
    console.log("Destroying chart instance");
    chartInstance.value.destroy();
    chartInstance.value = null;
  }
});
</script>

<style scoped>
.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.line-clamp-3 {
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
