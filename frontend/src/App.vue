<template>
  <div class="min-h-screen bg-gray-50">
    <!-- Header -->
    <header class="bg-white shadow-sm border-b border-gray-200">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex justify-between items-center h-16">
          <div class="flex items-center space-x-4">
            <h1 class="text-3xl font-bold text-gray-900 mb-2">📰 TrendPulse</h1>
            <div class="hidden md:flex items-center space-x-2">
              <div
                :class="[
                  'w-2 h-2 rounded-full',
                  isConnected ? 'bg-green-500' : 'bg-red-500',
                ]"
              ></div>
              <span class="text-sm text-gray-600">
                {{ isConnected ? "Connected" : "Disconnected" }}
              </span>
            </div>
          </div>

          <div class="flex items-center space-x-4">
            <span class="text-sm text-gray-500">
              {{ recentActivity }} recent articles
            </span>
            <button
              @click="refreshData"
              :disabled="isRefreshing"
              class="px-3 py-1 text-sm bg-blue-100 text-blue-700 rounded hover:bg-blue-200 disabled:opacity-50"
            >
              {{ isRefreshing ? "Refreshing..." : "Refresh" }}
            </button>
          </div>
        </div>
      </div>
    </header>

    <!-- Error banner -->
    <div v-if="error" class="bg-red-100 border-l-4 border-red-500 p-4">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex">
          <div class="flex-shrink-0">
            <span class="text-red-500">⚠️</span>
          </div>
          <div class="ml-3">
            <p class="text-sm text-red-700">{{ error }}</p>
          </div>
          <div class="ml-auto pl-3">
            <button
              @click="dismissError"
              class="text-red-500 hover:text-red-600"
            >
              ✕
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Main content -->
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <!-- Controls -->
      <div class="bg-white rounded-lg shadow-md p-6 mb-8">
        <div class="flex flex-wrap gap-6 items-end">
          <TopicSelector />
          <DateRangeSlider />
        </div>
      </div>

      <!-- Dashboard grid -->
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <!-- Live feed sidebar -->
        <div class="lg:col-span-1">
          <LiveFeed />
        </div>

        <!-- Main visualization -->
        <div class="lg:col-span-2">
          <WorldMapVisualization />
        </div>
      </div>

      <!-- Analytics section -->
      <TrendAnalysis />
    </div>

    <!-- Footer -->
    <footer class="bg-white border-t border-gray-200 mt-16">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div class="flex justify-between items-center">
          <p class="text-sm text-gray-500">
            TrendPulse - Real-time global news analysis
          </p>
          <div class="flex space-x-6 text-sm text-gray-500">
            <span>{{
              selectedTopic
                ? formatTopicName(selectedTopic)
                : "No topic selected"
            }}</span>
            <span v-if="selectedCountry">{{ selectedCountry }}</span>
          </div>
        </div>
      </div>
    </footer>
  </div>
</template>

<script setup>
import { computed, ref, onMounted } from "vue";
import { useStore } from "vuex";
import TopicSelector from "./components/TopicSelector.vue";
import DateRangeSlider from "./components/DateRangeSlider.vue";
import LiveFeed from "./components/LiveFeed.vue";
import WorldMapVisualization from "./components/WorldMapVisualization.vue";
import TrendAnalysis from "./components/TrendAnalysis.vue";

const store = useStore();

// Local state
const isRefreshing = ref(false);

// Computed properties from store
const isConnected = computed(() => store.getters.isConnected);
const error = computed(() => store.getters.currentError);
const selectedTopic = computed(() => store.getters.selectedTopic);
const selectedCountry = computed(() => store.getters.selectedCountry);
const recentActivity = computed(() => store.getters.recentActivity);

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

const refreshData = async () => {
  isRefreshing.value = true;
  try {
    await store.dispatch("refreshNews");
  } finally {
    isRefreshing.value = false;
  }
};

const dismissError = () => {
  store.commit("SET_ERROR", null);
};

// Initialize app
onMounted(async () => {
  // Check backend connection
  await store.dispatch("checkBackendConnection");

  // Load initial data
  if (isConnected.value) {
    await Promise.all([
      store.dispatch("loadAvailableTopics"),
      store.dispatch("loadLiveTrends"),
      store.dispatch("loadCountriesTrends"),
      store.dispatch("loadStatistics"),
    ]);
  }
});
</script>
