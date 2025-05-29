<template>
  <div class="w-full">
    <div class="bg-white rounded-lg shadow-md p-6">
      <!-- Header -->
      <div class="flex justify-between items-center mb-4">
        <h3 class="text-xl font-semibold text-gray-800">
          Global Topic Trends: {{ formatTopicName(selectedTopic) }}
        </h3>
        <div class="flex items-center gap-2">
          <span class="text-sm text-gray-600">Last updated:</span>
          <span class="text-sm font-medium text-gray-800">{{
            lastUpdated
          }}</span>
          <button
            @click="refreshData"
            :disabled="isRefreshing"
            class="ml-2 px-3 py-1 text-xs bg-blue-100 text-blue-700 rounded hover:bg-blue-200 disabled:opacity-50"
          >
            {{ isRefreshing ? "Refreshing..." : "Refresh" }}
          </button>
        </div>
      </div>

      <!-- Loading state -->
      <div v-if="loading" class="flex items-center justify-center h-96">
        <div class="text-center">
          <div
            class="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"
          ></div>
          <p class="text-gray-600">Loading global trends...</p>
        </div>
      </div>

      <!-- Error state -->
      <div v-else-if="error" class="flex items-center justify-center h-96">
        <div class="text-center">
          <div class="text-red-500 text-5xl mb-4">⚠️</div>
          <p class="text-red-600 mb-2">{{ error }}</p>
          <button
            @click="retryLoad"
            class="px-4 py-2 bg-red-100 text-red-700 rounded hover:bg-red-200"
          >
            Retry
          </button>
        </div>
      </div>

      <!-- Map container -->
      <div v-show="!loading && !error" class="relative">
        <!-- Interactive Leaflet Map -->
        <div
          ref="mapContainer"
          id="map-container"
          key="leaflet-map-container"
          class="map-container w-full h-96 bg-gray-100 rounded-lg border border-gray-300 overflow-hidden"
          style="height: 400px; width: 100%; min-height: 400px"
        ></div>

        <!-- Map controls -->
        <div class="absolute top-2 right-2 z-[1000] flex flex-col gap-2">
          <button
            @click="resetMapView"
            class="px-3 py-1 bg-white shadow-md rounded text-sm hover:bg-gray-50"
            title="Reset view"
          >
            🌍
          </button>
          <button
            @click="toggleMapStyle"
            class="px-3 py-1 bg-white shadow-md rounded text-sm hover:bg-gray-50"
            title="Toggle map style"
          >
            🗺️
          </button>
          <button
            @click="resizeMap"
            class="px-3 py-1 bg-white shadow-md rounded text-sm hover:bg-gray-50"
            title="Resize map"
          >
            📐
          </button>
        </div>

        <!-- Map legend -->
        <div class="mt-4 flex items-center justify-between">
          <div class="flex items-center gap-4">
            <span class="text-sm font-medium text-gray-700"
              >Trend Intensity:</span
            >
            <div class="flex items-center gap-2">
              <div class="w-4 h-4 bg-green-200 rounded"></div>
              <span class="text-xs text-gray-600">Low</span>
              <div class="w-4 h-4 bg-yellow-400 rounded"></div>
              <span class="text-xs text-gray-600">Medium</span>
              <div class="w-4 h-4 bg-red-500 rounded"></div>
              <span class="text-xs text-gray-600">High</span>
              <div class="w-4 h-4 bg-gray-300 rounded"></div>
              <span class="text-xs text-gray-600">No data</span>
            </div>
          </div>
          <div class="text-sm text-gray-600">
            Click on countries to see detailed trends
          </div>
        </div>

        <!-- Country info popup -->
        <div
          v-if="hoveredCountry"
          class="absolute bottom-4 left-4 bg-white p-3 rounded-lg shadow-lg border z-[1000] max-w-xs"
        >
          <h4 class="font-semibold text-gray-800">{{ hoveredCountry.name }}</h4>
          <div class="text-sm text-gray-600 mt-1">
            <div v-if="hoveredCountry.data">
              <div>Articles: {{ hoveredCountry.data.article_count }}</div>
              <div>
                Trend: {{ formatTrendScore(hoveredCountry.data.trend_score) }}
              </div>
              <div v-if="hoveredCountry.data.sentiment_avg">
                Sentiment:
                {{ formatSentiment(hoveredCountry.data.sentiment_avg) }}
              </div>
            </div>
            <div v-else class="text-gray-500">No data available</div>
          </div>
        </div>
      </div>

      <!-- Country trends summary -->
      <div v-if="!loading && !error" class="mt-6">
        <h4 class="text-lg font-semibold text-gray-800 mb-3">
          Top Countries by Activity
        </h4>
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <div
            v-for="country in topCountries"
            :key="country.country"
            @click="selectCountry(country.country)"
            class="p-4 border rounded-lg hover:shadow-md cursor-pointer transition-all"
            :class="
              selectedCountry === country.country
                ? 'border-primary bg-blue-50'
                : 'border-gray-200'
            "
          >
            <div class="flex justify-between items-start mb-2">
              <h5 class="font-medium text-gray-800">{{ country.country }}</h5>
              <span
                class="text-xs px-2 py-1 rounded-full"
                :class="getTrendBadgeClass(country.trend_score)"
              >
                {{ formatTrendScore(country.trend_score) }}
              </span>
            </div>
            <div class="text-sm text-gray-600">
              <div>{{ country.article_count }} articles</div>
              <div v-if="country.sentiment_avg">
                Sentiment: {{ formatSentiment(country.sentiment_avg) }}
              </div>
            </div>
            <!-- Mini trend chart placeholder -->
            <div
              class="mt-2 h-8 bg-gray-100 rounded flex items-end justify-between px-1"
            >
              <div
                v-for="n in 7"
                :key="n"
                class="w-1 bg-blue-300 rounded-t"
                :style="{ height: Math.random() * 100 + '%' }"
              ></div>
            </div>
          </div>
        </div>
      </div>

      <!-- No data state -->
      <div
        v-if="!loading && !error && topCountries.length === 0"
        class="text-center py-12"
      >
        <div class="text-gray-400 text-5xl mb-4">📊</div>
        <p class="text-gray-600 mb-2">No trend data available</p>
        <p class="text-sm text-gray-500">
          Try selecting a different topic or date range
        </p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, onMounted, watch, nextTick, onUnmounted } from "vue";
import { useStore } from "vuex";
import { format } from "date-fns";
import L from "leaflet";
import "leaflet/dist/leaflet.css";

// Fix Leaflet default icon issue
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl:
    "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
  iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
  shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
});

const store = useStore();

// Refs
const mapContainer = ref(null);
const isRefreshing = ref(false);
const map = ref(null);
const geoJsonLayer = ref(null);
const hoveredCountry = ref(null);
const currentMapStyle = ref("satellite");
const isDestroyed = ref(false);

// Computed properties
const loading = computed(() => store.getters.isLoading);
const error = computed(() => store.getters.currentError);
const selectedTopic = computed(() => store.getters.selectedTopic);
const selectedCountry = computed(() => store.getters.selectedCountry);
const countriesTrends = computed(() => store.getters.countriesTrends);
const liveTrends = computed(() => store.getters.liveTrends);

// Process trends data for display
const topCountries = computed(() => {
  // First try to use countriesTrends data
  if (countriesTrends.value && countriesTrends.value.length > 0) {
    return [...countriesTrends.value]
      .sort((a, b) => b.article_count - a.article_count)
      .slice(0, 9); // Top 9 countries
  }

  // Fallback: use statistics data
  const topCountriesStats = store.getters.topCountriesByArticles;
  if (topCountriesStats && topCountriesStats.length > 0) {
    console.log(
      "Using statistics data as fallback for countries list",
      topCountriesStats
    );
    return topCountriesStats
      .map((country) => ({
        country: country.country,
        article_count: country.article_count,
        trend_score: Math.min(country.article_count / 20.0, 1.0), // Simple trend score
        sentiment_avg: 0, // Default neutral sentiment
        latest_date: new Date().toISOString(),
        data_points: 1,
      }))
      .slice(0, 9);
  }

  // Final fallback: mock data for demonstration
  console.log("Using mock data for countries list");
  return [
    {
      country: "United States",
      article_count: 25,
      trend_score: 0.8,
      sentiment_avg: 0.1,
      latest_date: new Date().toISOString(),
      data_points: 1,
    },
    {
      country: "Germany",
      article_count: 15,
      trend_score: 0.6,
      sentiment_avg: -0.1,
      latest_date: new Date().toISOString(),
      data_points: 1,
    },
    {
      country: "United Kingdom",
      article_count: 12,
      trend_score: 0.5,
      sentiment_avg: 0.0,
      latest_date: new Date().toISOString(),
      data_points: 1,
    },
    {
      country: "Canada",
      article_count: 8,
      trend_score: 0.4,
      sentiment_avg: 0.2,
      latest_date: new Date().toISOString(),
      data_points: 1,
    },
    {
      country: "Australia",
      article_count: 6,
      trend_score: 0.3,
      sentiment_avg: 0.1,
      latest_date: new Date().toISOString(),
      data_points: 1,
    },
  ];
});

// Create a map for quick country data lookup
const countryDataMap = computed(() => {
  // First try to use countriesTrends data
  if (countriesTrends.value && countriesTrends.value.length > 0) {
    return Object.fromEntries(
      countriesTrends.value.map((country) => [country.country, country])
    );
  }

  // Fallback: use statistics data if available
  const topCountries = store.getters.topCountriesByArticles;
  if (topCountries && topCountries.length > 0) {
    console.log("Using statistics data as fallback for map", topCountries);
    return Object.fromEntries(
      topCountries.map((country) => [
        country.country,
        {
          country: country.country,
          article_count: country.article_count,
          trend_score: Math.min(country.article_count / 20.0, 1.0), // Simple trend score
          sentiment_avg: 0, // Default neutral sentiment
          latest_date: new Date().toISOString(),
          data_points: 1,
        },
      ])
    );
  }

  // Final fallback: mock data for demonstration
  console.log("Using mock data for map demonstration");
  return {
    "United States": {
      country: "United States",
      article_count: 25,
      trend_score: 0.8,
      sentiment_avg: 0.1,
      latest_date: new Date().toISOString(),
      data_points: 1,
    },
    Germany: {
      country: "Germany",
      article_count: 15,
      trend_score: 0.6,
      sentiment_avg: -0.1,
      latest_date: new Date().toISOString(),
      data_points: 1,
    },
    "United Kingdom": {
      country: "United Kingdom",
      article_count: 12,
      trend_score: 0.5,
      sentiment_avg: 0.0,
      latest_date: new Date().toISOString(),
      data_points: 1,
    },
    Canada: {
      country: "Canada",
      article_count: 8,
      trend_score: 0.4,
      sentiment_avg: 0.2,
      latest_date: new Date().toISOString(),
      data_points: 1,
    },
    Australia: {
      country: "Australia",
      article_count: 6,
      trend_score: 0.3,
      sentiment_avg: 0.1,
      latest_date: new Date().toISOString(),
      data_points: 1,
    },
  };
});

const lastUpdated = computed(() => {
  const liveTrend = liveTrends.value.find(
    (trend) => trend.topic === selectedTopic.value
  );
  return liveTrend?.last_updated
    ? format(new Date(liveTrend.last_updated), "MMM d, HH:mm")
    : format(new Date(), "MMM d, HH:mm");
});

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

const formatTrendScore = (score) => {
  if (score > 0.7) return "🔥 Hot";
  if (score > 0.4) return "📈 Rising";
  if (score > 0.2) return "📊 Stable";
  return "📉 Low";
};

const getTrendBadgeClass = (score) => {
  if (score > 0.7) return "bg-red-100 text-red-700";
  if (score > 0.4) return "bg-orange-100 text-orange-700";
  if (score > 0.2) return "bg-green-100 text-green-700";
  return "bg-gray-100 text-gray-700";
};

const formatSentiment = (sentiment) => {
  if (sentiment > 0.1) return "😊 Positive";
  if (sentiment < -0.1) return "😟 Negative";
  return "😐 Neutral";
};

const selectCountry = (country) => {
  store.dispatch("selectCountry", country);

  // Zoom to country on map if available
  if (map.value && geoJsonLayer.value) {
    geoJsonLayer.value.eachLayer((layer) => {
      if (
        layer.feature.properties.NAME === country ||
        layer.feature.properties.NAME_EN === country ||
        layer.feature.properties.ADMIN === country
      ) {
        map.value.fitBounds(layer.getBounds(), { padding: [20, 20] });
      }
    });
  }
};

const refreshData = async () => {
  isRefreshing.value = true;
  try {
    await Promise.all([
      store.dispatch("loadTopicTrends"),
      store.dispatch("loadCountriesTrends"),
      store.dispatch("loadLiveTrends"),
      store.dispatch("loadStatistics"),
    ]);
  } finally {
    isRefreshing.value = false;
  }
};

const retryLoad = () => {
  store.dispatch("loadTopicTrends");
};

// Map-specific methods
const initializeMap = async () => {
  console.log("Attempting to initialize map...");
  console.log("mapContainer.value:", mapContainer.value);

  // Check if map already exists or component is destroyed
  if (map.value) {
    console.log("Map already exists, skipping initialization");
    return;
  }

  if (isDestroyed.value) {
    console.log("Component is destroyed, skipping map initialization");
    return;
  }

  // Wait for the DOM element to be available
  let attempts = 0;
  const maxAttempts = 10;

  while (!mapContainer.value && attempts < maxAttempts) {
    console.log(`Waiting for map container... attempt ${attempts + 1}`);
    await new Promise((resolve) => setTimeout(resolve, 100));
    attempts++;
  }

  if (!mapContainer.value) {
    console.error("Map container ref not found, trying by ID...");
    // Fallback: try to get the element by ID
    const containerElement = document.getElementById("map-container");
    if (containerElement) {
      console.log("Found map container by ID");
      mapContainer.value = containerElement;
    } else {
      console.error("Map container not found by ref or ID");
      return;
    }
  }

  console.log("Map container found, initializing map...");

  try {
    // Ensure container has dimensions
    const containerRect = mapContainer.value.getBoundingClientRect();
    console.log("Container dimensions:", containerRect);

    if (containerRect.width === 0 || containerRect.height === 0) {
      console.error("Container has no dimensions, forcing dimensions...");
      // Force container dimensions
      mapContainer.value.style.height = "400px";
      mapContainer.value.style.width = "100%";
      mapContainer.value.style.display = "block";

      // Wait a bit for the style to apply
      await new Promise((resolve) => setTimeout(resolve, 50));
    }

    // Create map
    map.value = L.map(mapContainer.value, {
      center: [20, 0],
      zoom: 2,
      minZoom: 1,
      maxZoom: 10,
      worldCopyJump: true,
      zoomControl: false,
    });

    console.log("Map created successfully");

    // Add zoom control to bottom right
    L.control
      .zoom({
        position: "bottomright",
      })
      .addTo(map.value);

    // Add tile layer
    updateMapStyle();

    // Load and add country boundaries
    await loadCountryBoundaries();

    console.log("Map initialization complete");

    // Force map to recalculate its size immediately
    setTimeout(() => {
      if (map.value) {
        console.log("Invalidating map size...");
        map.value.invalidateSize();
      }
    }, 100);

    // Add another resize after a longer delay to ensure proper sizing
    setTimeout(() => {
      if (map.value && mapContainer.value) {
        console.log("Map still exists after 2 seconds, resizing...");
        map.value.invalidateSize();

        // Force container to be visible and properly sized
        const containerRect = mapContainer.value.getBoundingClientRect();
        console.log("Final container dimensions:", containerRect);

        if (containerRect.width === 0 || containerRect.height === 0) {
          console.log(
            "Container still has no dimensions, forcing visibility..."
          );
          mapContainer.value.style.display = "block";
          mapContainer.value.style.visibility = "visible";
          setTimeout(() => {
            if (map.value) {
              map.value.invalidateSize();
            }
          }, 50);
        }
      } else {
        console.error("Map disappeared after initialization!");
        console.log("map.value:", map.value);
        console.log("mapContainer.value:", mapContainer.value);
      }
    }, 2000);
  } catch (error) {
    console.error("Error initializing map:", error);
  }
};

const updateMapStyle = () => {
  if (!map.value) return;

  // Remove existing tile layers
  map.value.eachLayer((layer) => {
    if (layer instanceof L.TileLayer) {
      map.value.removeLayer(layer);
    }
  });

  // Add new tile layer based on current style
  let tileLayer;
  if (currentMapStyle.value === "satellite") {
    tileLayer = L.tileLayer(
      "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
      {
        attribution:
          "&copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community",
      }
    );
  } else {
    tileLayer = L.tileLayer(
      "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
      {
        attribution:
          '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
      }
    );
  }

  tileLayer.addTo(map.value);
};

const toggleMapStyle = () => {
  currentMapStyle.value =
    currentMapStyle.value === "satellite" ? "street" : "satellite";
  updateMapStyle();
};

const resetMapView = () => {
  if (map.value) {
    map.value.setView([20, 0], 2);
    // Also resize the map when resetting view
    setTimeout(() => {
      if (map.value) {
        map.value.invalidateSize();
      }
    }, 100);
  }
};

const resizeMap = () => {
  if (map.value && mapContainer.value) {
    console.log("Manually resizing map...");
    map.value.invalidateSize();
    const rect = mapContainer.value.getBoundingClientRect();
    console.log("Container dimensions:", rect);
  }
};

const loadCountryBoundaries = async () => {
  try {
    // Use a simplified world countries GeoJSON
    const response = await fetch(
      "https://raw.githubusercontent.com/holtzy/D3-graph-gallery/master/DATA/world.geojson"
    );

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const geoJsonData = await response.json();

    // Create GeoJSON layer with styling
    geoJsonLayer.value = L.geoJSON(geoJsonData, {
      style: (feature) => getCountryStyle(feature),
      onEachFeature: (feature, layer) => {
        const countryName =
          feature.properties.NAME ||
          feature.properties.NAME_EN ||
          feature.properties.ADMIN ||
          feature.properties.name ||
          feature.properties.NAME_LONG ||
          feature.properties.COUNTRY ||
          feature.properties.Country ||
          feature.properties.country ||
          "Unknown Country";

        // Try to find country data with different name variations
        let countryData = countryDataMap.value[countryName];

        // Try common name variations if not found
        if (!countryData) {
          const nameVariations = [
            countryName,
            // Handle common country name mappings
            countryName === "USA" ? "United States" : null,
            countryName === "United States of America" ? "United States" : null,
            countryName === "UK" ? "United Kingdom" : null,
            countryName === "Great Britain" ? "United Kingdom" : null,
            countryName === "Britain" ? "United Kingdom" : null,
            countryName?.replace(/^United States.*/, "United States"),
            countryName?.replace(/^United Kingdom.*/, "United Kingdom"),
            countryName?.replace(/^Germany.*/, "Germany"),
            countryName?.replace(/^Canada.*/, "Canada"),
            countryName?.replace(/^Australia.*/, "Australia"),
          ].filter(Boolean);

          for (const variation of nameVariations) {
            if (countryDataMap.value[variation]) {
              countryData = countryDataMap.value[variation];
              console.log(`Found match: "${countryName}" -> "${variation}"`);
              break;
            }
          }
        }

        // Add hover effects
        layer.on({
          mouseover: (e) => {
            const layer = e.target;
            layer.setStyle({
              weight: 3,
              color: "#666",
              dashArray: "",
              fillOpacity: 0.8,
            });

            hoveredCountry.value = {
              name: countryName,
              data: countryData,
            };

            // Optional: log successful hovers
            if (countryData) {
              console.log(
                `Hovering over ${countryName}: ${countryData.article_count} articles`
              );
            }
          },
          mouseout: (e) => {
            geoJsonLayer.value.resetStyle(e.target);
            hoveredCountry.value = null;
          },
          click: () => {
            if (countryData) {
              selectCountry(countryName);
            }
          },
        });

        // Add tooltip
        if (countryData) {
          layer.bindTooltip(
            `
            <strong>${countryName}</strong><br/>
            Articles: ${countryData.article_count}<br/>
            Trend: ${formatTrendScore(countryData.trend_score)}
          `,
            {
              permanent: false,
              sticky: true,
              className: "custom-tooltip",
            }
          );
        }
      },
    });

    geoJsonLayer.value.addTo(map.value);
  } catch (error) {
    console.error("Error loading country boundaries:", error);

    // Fallback: Add markers for countries with data
    addCountryMarkers();
  }
};

const addCountryMarkers = () => {
  // Fallback method: Add circle markers for countries with data
  const countryCoordinates = {
    US: [39.8283, -98.5795],
    Germany: [51.1657, 10.4515],
    Canada: [56.1304, -106.3468],
    UK: [55.3781, -3.436],
    France: [46.2276, 2.2137],
    Australia: [-25.2744, 133.7751],
    Japan: [36.2048, 138.2529],
    China: [35.8617, 104.1954],
    India: [20.5937, 78.9629],
    Brazil: [-14.235, -51.9253],
    Russia: [61.524, 105.3188],
    Global: [0, 0],
  };

  countriesTrends.value.forEach((countryData) => {
    const coords = countryCoordinates[countryData.country];
    if (coords) {
      const color = getCountryColor(countryData.trend_score);
      const marker = L.circleMarker(coords, {
        radius: Math.max(5, Math.min(20, countryData.article_count / 10)),
        fillColor: color,
        color: "white",
        weight: 2,
        opacity: 1,
        fillOpacity: 0.8,
      });

      marker.bindTooltip(
        `
        <strong>${countryData.country}</strong><br/>
        Articles: ${countryData.article_count}<br/>
        Trend: ${formatTrendScore(countryData.trend_score)}
      `,
        {
          permanent: false,
          sticky: true,
          className: "custom-tooltip",
        }
      );

      marker.on("click", () => {
        selectCountry(countryData.country);
      });

      marker.addTo(map.value);
    }
  });
};

const getCountryColor = (trendScore) => {
  if (trendScore > 0.7) return "#ef4444"; // Red for high
  if (trendScore > 0.4) return "#f59e0b"; // Orange for medium
  if (trendScore > 0.2) return "#10b981"; // Green for stable
  return "#6b7280"; // Gray for low
};

const getCountryStyle = (feature) => {
  const countryName =
    feature.properties.NAME ||
    feature.properties.NAME_EN ||
    feature.properties.ADMIN ||
    feature.properties.name ||
    feature.properties.NAME_LONG ||
    feature.properties.COUNTRY ||
    feature.properties.Country ||
    feature.properties.country ||
    "Unknown Country";

  // Try to find country data with different name variations
  let countryData = countryDataMap.value[countryName];

  // Try common name variations if not found
  if (!countryData) {
    const nameVariations = [
      countryName,
      // Handle common country name mappings
      countryName === "USA" ? "United States" : null,
      countryName === "United States of America" ? "United States" : null,
      countryName === "UK" ? "United Kingdom" : null,
      countryName === "Great Britain" ? "United Kingdom" : null,
      countryName === "Britain" ? "United Kingdom" : null,
      countryName?.replace(/^United States.*/, "United States"),
      countryName?.replace(/^United Kingdom.*/, "United Kingdom"),
      countryName?.replace(/^Germany.*/, "Germany"),
      countryName?.replace(/^Canada.*/, "Canada"),
      countryName?.replace(/^Australia.*/, "Australia"),
    ].filter(Boolean);

    for (const variation of nameVariations) {
      if (countryDataMap.value[variation]) {
        countryData = countryDataMap.value[variation];
        break;
      }
    }
  }

  if (!countryData) {
    return {
      fillColor: "#f0f0f0",
      weight: 1,
      opacity: 1,
      color: "#ccc",
      dashArray: "3",
      fillOpacity: 0.3,
    };
  }

  // Color based on trend score
  let fillColor;
  if (countryData.trend_score > 0.7) {
    fillColor = "#ef4444"; // Red for high
  } else if (countryData.trend_score > 0.4) {
    fillColor = "#f59e0b"; // Orange for medium
  } else if (countryData.trend_score > 0.2) {
    fillColor = "#10b981"; // Green for stable
  } else {
    fillColor = "#6b7280"; // Gray for low
  }

  return {
    fillColor: fillColor,
    weight: 2,
    opacity: 1,
    color: "white",
    dashArray: "",
    fillOpacity: 0.7,
  };
};

const updateMapData = () => {
  console.log("Updating map data...");
  if (!map.value) {
    console.log("Map not available, skipping update");
    return;
  }

  if (geoJsonLayer.value) {
    console.log("Updating GeoJSON layer styles");
    geoJsonLayer.value.eachLayer((layer) => {
      const style = getCountryStyle(layer.feature);
      layer.setStyle(style);
    });
  } else {
    console.log("GeoJSON layer not available");
  }
};

// Watch for topic changes
watch(selectedTopic, (newTopic, oldTopic) => {
  console.log("Topic changed from", oldTopic, "to", newTopic);
  if (newTopic) {
    store.dispatch("loadTopicTrends");
    store.dispatch("loadCountriesTrends");
  }
});

// Watch for data changes to update map
watch(
  countriesTrends,
  () => {
    console.log("Countries trends data changed, updating map...");
    if (map.value) {
      updateMapData();
    } else {
      console.log("Map not available for update");
    }
  },
  { deep: true }
);

// Watch for loading state changes to resize map when it becomes visible
watch([loading, error], ([newLoading, newError], [oldLoading, oldError]) => {
  console.log("Loading/error state changed:", {
    newLoading,
    newError,
    oldLoading,
    oldError,
  });

  // If we just finished loading and there's no error, resize the map
  if (oldLoading && !newLoading && !newError && map.value) {
    console.log("Map container should now be visible, resizing...");
    setTimeout(() => {
      if (map.value && mapContainer.value) {
        console.log("Resizing map after visibility change");
        map.value.invalidateSize();

        // Double-check container dimensions
        const rect = mapContainer.value.getBoundingClientRect();
        console.log("Container dimensions after resize:", rect);
      }
    }, 100);
  }
});

// Watch for statistics changes to update map when fallback data is available
watch(
  () => store.getters.topCountriesByArticles,
  (newStats) => {
    if (
      newStats &&
      newStats.length > 0 &&
      (!countriesTrends.value || countriesTrends.value.length === 0)
    ) {
      console.log("Statistics data loaded, updating map with fallback data");
      updateMapData();
    }
  },
  { deep: true }
);

// Load initial data
onMounted(async () => {
  console.log("WorldMapVisualization mounted");

  if (selectedTopic.value) {
    store.dispatch("loadTopicTrends");
    store.dispatch("loadCountriesTrends");
  }
  store.dispatch("loadLiveTrends");
  store.dispatch("loadStatistics"); // Load statistics as fallback data

  // Initialize map after DOM is ready with multiple nextTick calls
  await nextTick();
  await nextTick(); // Double nextTick for better DOM readiness

  // Use a longer delay to ensure DOM is fully rendered
  setTimeout(async () => {
    console.log("Starting map initialization...");
    console.log("Document ready state:", document.readyState);
    console.log(
      "Map container element exists:",
      !!document.getElementById("map-container")
    );
    console.log("Map container ref exists:", !!mapContainer.value);
    await initializeMap();
  }, 300);
});

// Cleanup
onUnmounted(() => {
  console.log("Component unmounting, cleaning up map...");
  isDestroyed.value = true;

  if (map.value) {
    try {
      map.value.remove();
      map.value = null;
      geoJsonLayer.value = null;
      console.log("Map cleaned up successfully");
    } catch (error) {
      console.error("Error cleaning up map:", error);
    }
  }
});
</script>

<style scoped>
/* Custom tooltip styling */
:deep(.custom-tooltip) {
  background: white;
  border: 1px solid #ccc;
  border-radius: 4px;
  padding: 8px;
  font-size: 12px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

/* Ensure map container has proper styling */
:deep(.leaflet-container) {
  height: 100% !important;
  width: 100% !important;
  background: #f0f0f0;
}

/* Fix for Leaflet marker icons */
:deep(.leaflet-default-icon-path) {
  background-image: url("https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png");
}

/* Ensure the map container itself has proper dimensions */
.map-container {
  height: 400px !important;
  width: 100% !important;
  min-height: 400px !important;
  max-height: 400px !important;
  position: relative;
  display: block !important;
  visibility: visible !important;
  background-color: #f0f0f0 !important;
  overflow: hidden !important;
}

/* Additional map container styling */
#map-container {
  height: 400px !important;
  width: 100% !important;
  min-height: 400px !important;
  max-height: 400px !important;
  display: block !important;
  visibility: visible !important;
  box-sizing: border-box !important;
}

/* Ensure Leaflet container fills the entire space */
:deep(.leaflet-container) {
  height: 400px !important;
  width: 100% !important;
  max-height: 400px !important;
  background: #f0f0f0;
  position: relative !important;
}
</style>
