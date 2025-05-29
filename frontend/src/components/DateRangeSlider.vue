<template>
  <div class="flex flex-col gap-3 flex-grow min-w-[300px]">
    <label class="font-semibold text-primary">Date Range</label>

    <!-- Quick preset buttons -->
    <div class="flex gap-2 flex-wrap">
      <button
        v-for="preset in datePresets"
        :key="preset.label"
        @click="selectPreset(preset)"
        :class="[
          'px-3 py-1 text-xs rounded-full border transition-all',
          isActivePreset(preset)
            ? 'bg-primary text-white border-primary'
            : 'bg-white text-gray-600 border-gray-300 hover:border-primary hover:text-primary',
        ]"
      >
        {{ preset.label }}
      </button>
    </div>

    <!-- Custom date inputs -->
    <div class="flex gap-2 items-center">
      <div class="flex flex-col flex-1">
        <label class="text-xs text-gray-600 mb-1">Start Date</label>
        <input
          type="date"
          v-model="startDate"
          @change="updateDateRange"
          :max="endDate"
          class="p-2 border border-gray-300 rounded text-sm focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary"
        />
      </div>

      <div class="text-gray-400 self-end pb-2">to</div>

      <div class="flex flex-col flex-1">
        <label class="text-xs text-gray-600 mb-1">End Date</label>
        <input
          type="date"
          v-model="endDate"
          @change="updateDateRange"
          :min="startDate"
          :max="today"
          class="p-2 border border-gray-300 rounded text-sm focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary"
        />
      </div>
    </div>

    <!-- Date range info -->
    <div class="text-xs text-gray-500">
      <span>{{ formatDateRange(startDate, endDate) }}</span>
      <span class="ml-2">{{ getDayCount(startDate, endDate) }} days</span>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, onMounted } from "vue";
import { useStore } from "vuex";
import { format, subDays, subMonths, differenceInDays } from "date-fns";

const store = useStore();

// Current date range from store
const dateRange = computed(() => store.state.dateRange);

// Local reactive refs for form inputs
const startDate = ref(dateRange.value.start);
const endDate = ref(dateRange.value.end);
const today = format(new Date(), "yyyy-MM-dd");

// Date presets
const datePresets = [
  {
    label: "Last 7 days",
    start: () => format(subDays(new Date(), 7), "yyyy-MM-dd"),
    end: () => today,
  },
  {
    label: "Last 30 days",
    start: () => format(subDays(new Date(), 30), "yyyy-MM-dd"),
    end: () => today,
  },
  {
    label: "Last 3 months",
    start: () => format(subMonths(new Date(), 3), "yyyy-MM-dd"),
    end: () => today,
  },
  {
    label: "Last 6 months",
    start: () => format(subMonths(new Date(), 6), "yyyy-MM-dd"),
    end: () => today,
  },
];

const updateDateRange = () => {
  const newRange = {
    start: startDate.value,
    end: endDate.value,
  };
  store.dispatch("updateDateRange", newRange);
};

const selectPreset = (preset) => {
  startDate.value = preset.start();
  endDate.value = preset.end();
  updateDateRange();
};

const isActivePreset = (preset) => {
  return startDate.value === preset.start() && endDate.value === preset.end();
};

const formatDateRange = (start, end) => {
  try {
    const startFormatted = format(new Date(start), "MMM d, yyyy");
    const endFormatted = format(new Date(end), "MMM d, yyyy");
    return `${startFormatted} - ${endFormatted}`;
  } catch {
    return "Invalid date range";
  }
};

const getDayCount = (start, end) => {
  try {
    return differenceInDays(new Date(end), new Date(start)) + 1;
  } catch {
    return 0;
  }
};

// Update local state when store changes
const updateLocalDates = () => {
  startDate.value = dateRange.value.start;
  endDate.value = dateRange.value.end;
};

onMounted(() => {
  updateLocalDates();
});
</script>
