<template>
  <div class="box">
    <h1 class="title">Visualise different Discrete Global Grid Systems</h1>
  </div>

  <div class="columns">
    <div class="column is-3">
      <div class="field">
        <label class="label">Select DGGS Type:</label>
        <div class="control select is-primary">
          <select v-model="dggs_sel">
            <option v-for="f in dggs_types.types" :key="f" :value="f">{{ f }}</option>
          </select>
        </div>
      </div>
      <div class="field">
        <div class="control">
          <button id="gridgen_button" class="button is-info" @click="loadNew">View Grid</button>

        </div>
      </div>
      <div>dggs: {{ dggs_sel }} at 2 resolutions
        <p v-if="view_info"> {{ view_info }}</p>
      </div>
    </div>

    <div class="column is-9 is-offset-3">
      <div class="container">
        <div class="deck-container">
          <canvas id="deck"></canvas>
        </div>
      </div>
    </div>
  </div>

  <div class="columns pt-2">
    <div class="column">

      <Footer />

    </div>
  </div>

</template>

<script setup>
import Footer from '@/components/Footer.vue';
import { ref, onMounted } from 'vue';
import { Deck, _GlobeView } from "@deck.gl/core";
import { GeoJsonLayer } from "@deck.gl/layers";

const loading = ref(false);
const error = ref(null);
const error_info = ref(null);

const cesiumContainer = ref(null);

const dggs_types = ref({
  types: ["ISEA3H",
    "ISEA4H",
    "ISEA4T",
    "ISEA4D",
    "ISEA43H",
    "ISEA7H",
    "FULLER3H",
    "FULLER4H",
    "FULLER4T",
    "FULLER4D",
    "FULLER43H",
    "FULLER7H",
    "H3",
    "RHEALPIX"]
});

const demos = {
  "FULLER3H": [4, 5],
  "FULLER4D": [3, 4],
  "FULLER4H": [3, 4],
  "FULLER4T": [3, 4],
  "FULLER7H": [2, 3],
  "FULLER43H": [4, 5],
  "H3": [1, 2],
  "ISEA3H": [4, 5],
  "ISEA4D": [3, 4],
  "ISEA4T": [3, 4],
  "ISEA7H": [2, 3],
  "RHEALPIX": [2, 3],
  "ISEA4H": [3, 4],
  "ISEA43H": [4, 5]
};

const dggs_sel = ref("ISEA3H");

const view_info = ref(null);

// onMounted(async () => {
const loadNew = (async () => {
  loading.value = true;

  const sample = demos[dggs_sel.value];

  const id1 = sample[0];
  const id2 = sample[1];
  view_info.value = `Resolutions ${sample[0]} ${sample[1]}`;

  const INITIAL_VIEW_STATE = {
    latitude: 51.47,
    longitude: 0.45,
    zoom: 1,
    minZoom: 1,
    maxZoom: 10,
  };
  const data_geo =
    "https://storage.googleapis.com/geo-assets/dggs-dev/demo-grids/ne_110m_admin_0_countries.geojson";

  const demo_grid =
    `https://storage.googleapis.com/geo-assets/dggs-dev/demo-grids/${dggs_sel.value}_${id1}_global_split.geojson`;

  const demo_grid1 =
    `https://storage.googleapis.com/geo-assets/dggs-dev/demo-grids/${dggs_sel.value}_${id2}_global_split.geojson`;

  const deckgl = new Deck({
    id: "deck-container",
    canvas: "deck",
    views: new _GlobeView({
      resolution: 10,
    }),
    initialViewState: INITIAL_VIEW_STATE,
    controller: true,
    layers: [
      new GeoJsonLayer({
        id: "natural_earth",
        data: data_geo,
        getFillColor: () => [100, 250, 150, 150],
        stroked: true,
        filled: true,
        pickable: false,
        getLineWidth: 0,
        lineWidthScale: 0,
        lineWidthMinPixels: 0,
        getLineColor: [100, 250, 150, 150],
      }),
      new GeoJsonLayer({
        id: "hexes",
        data: demo_grid1,
        getFillColor: [0, 0, 0],
        stroked: true,
        filled: false,
        pickable: false,
        getLineWidth: 5,
        lineWidthScale: 20,
        lineWidthMinPixels: 2,
        getLineColor: [200, 200, 200],
      }),
      new GeoJsonLayer({
        id: "hexes1",
        data: demo_grid,
        getFillColor: [0, 0, 0],
        stroked: true,
        filled: false,
        pickable: false,
        getLineWidth: 6,
        lineWidthScale: 20,
        lineWidthMinPixels: 3,
        getLineColor: [100, 200, 300],
      }),
    ],
    parameters: { cull: true },
  });

  loading.value = false;
});

</script>

<style scoped>
html,
body,
#cesiumContainer {
  width: 100%;
  height: 100%;
  margin: 0;
  padding: 0;
  overflow: hidden;
}

.deck-container {
  position: relative;
  width: 100%;
  height: 600px;
  /* height: 100%; */
  margin: 0;
  padding: 0;
  overflow: hidden;
}

#deck {
  height: 100%;
}
</style>
