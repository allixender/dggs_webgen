<template>
  <div class="info">
    <h1>DeckGl</h1>
    <h2 v-if="loading">loading ...</h2>
  </div>
  <div class="container">
    <div class="deck-container">
      <canvas id="deck"></canvas>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import { Deck, _GlobeView } from "@deck.gl/core";
import { GeoJsonLayer } from "@deck.gl/layers";

const loading = ref(false);

onMounted(() => {
  loading.value = true;

  const INITIAL_VIEW_STATE = {
    latitude: 51.47,
    longitude: 0.45,
    zoom: 1,
    minZoom: 1,
    maxZoom: 10,
  };
  const data_geo =
    "https://raw.githubusercontent.com/vasturiano/globe.gl/master/example/datasets/ne_110m_admin_0_countries.geojson";

  const demo_grid =
    "https://dggrid-py-xj6vl2xpya-lz.a.run.app/api/grid_gen/ISEA7H/2";

  fetch(demo_grid)
    .then((res) => res.json())
    .then((hexes) => {

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
            getLineWidth: 3,
            lineWidthScale: 10,
            lineWidthMinPixels: 1,
            getLineColor: [20, 20, 20, 150],
          }),
          new GeoJsonLayer({
            id: "hexes",
            data: hexes,
            getFillColor: [0, 0, 0],
            stroked: true,
            filled: false,
            pickable: false,
            getLineWidth: 5,
            lineWidthScale: 20,
            lineWidthMinPixels: 2,
            getLineColor: [200, 200, 200],
          }),
        ],
        parameters: { cull: true },
      });
      loading.value = false;
    });
});
</script>

<style scoped>
.deck-container {
  position: relative;
  width: 100%;
  height: 600px;
  margin: 0;
  padding: 0;
  overflow: hidden;
}
#deck {
  height: 100%;
}
</style>
