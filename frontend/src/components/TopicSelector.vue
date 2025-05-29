<template>
  <div class="flex flex-col gap-2 min-w-[250px]">
    <label for="topic-select" class="font-semibold text-primary">
      Select a Topic:
    </label>
    <select
      id="topic-select"
      v-model="selectedValue"
      @change="updateTopic"
      class="p-2.5 border border-secondary rounded text-base bg-white cursor-pointer transition-all focus:outline-none focus:border-primary focus:ring-2 focus:ring-primary/20"
      :disabled="loading"
    >
      <option value="" disabled>Choose a news topic...</option>
      <option v-for="topic in topics" :key="topic" :value="topic">
        {{ formatTopicName(topic) }}
      </option>
    </select>

    <!-- Topic info -->
    <div v-if="selectedTopic && topicInfo" class="text-sm text-gray-600 mt-1">
      <span class="font-medium">{{ topicInfo.article_count || 0 }}</span>
      articles
      <span v-if="topicInfo.trend_score" class="ml-2">
        • Trending:
        <span :class="getTrendClass(topicInfo.trend_score)">
          {{ formatTrendScore(topicInfo.trend_score) }}
        </span>
      </span>
    </div>

    <!-- Loading state -->
    <div v-if="loading" class="text-sm text-gray-500">Loading topics...</div>
  </div>
</template>

<script setup>
import { computed, onMounted } from "vue";
import { useStore } from "vuex";

const store = useStore();

const selectedValue = computed({
  get: () => store.getters.selectedTopic,
  set: (value) => store.dispatch("selectTopic", value),
});

const topics = computed(() => store.getters.availableTopics);
const loading = computed(() => store.getters.isLoading);
const selectedTopic = computed(() => store.getters.selectedTopic);

// Get topic information from live trends
const topicInfo = computed(() => {
  const liveTrends = store.getters.liveTrends;
  return liveTrends.find((trend) => trend.topic === selectedTopic.value);
});

const updateTopic = () => {
  if (selectedValue.value) {
    store.dispatch("selectTopic", selectedValue.value);
  }
};

const formatTopicName = (topic) => {
  return topic
    .replace(/_/g, " ")
    .split(" ")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
    .join(" ");
};

const formatTrendScore = (score) => {
  if (score > 0.7) return "🔥 Hot";
  if (score > 0.4) return "📈 Rising";
  if (score > 0.2) return "📊 Stable";
  return "📉 Declining";
};

const getTrendClass = (score) => {
  if (score > 0.7) return "text-red-600 font-bold";
  if (score > 0.4) return "text-orange-600 font-semibold";
  if (score > 0.2) return "text-green-600";
  return "text-gray-500";
};

// Load topics on component mount
onMounted(() => {
  store.dispatch("loadAvailableTopics");
});
</script>
