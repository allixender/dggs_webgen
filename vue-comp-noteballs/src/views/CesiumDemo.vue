<template>
  <div class="cesium">
    <h1>Cesium</h1>
    <h2 v-if="loading">loading ...</h2>
  </div>
  <div class="container">
    <div ref="cesiumContainer" id="cesiumContainer"></div>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
// import { Viewer } from "cesium";
import * as Cesium from "cesium";

const loading = ref(false);
const cesiumContainer = ref(null);

onMounted(async () => {
  Cesium.Ion.defaultAccessToken =
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJqdGkiOiJiOWZmNmQ4Zi00OWM5LTQ3ZjgtOGIzNC04ZThjMzNlMDVlOTUiLCJpZCI6MTE4NzUzLCJpYXQiOjE2NzE0NDIxMDN9.t4C10Kh6y6jFTmMG0WKoJ0fTpmODdcwRn_FYcatTjU0";
  const viewer = new Cesium.Viewer(cesiumContainer.value, {
    baseLayerPicker: false,
    geocoder: false,
    fullscreenButton: false,
    sceneModePicker: false,
    infoBox: false,
    navigationHelpButton: false,
    projectionPicker: false,
    timeline: false,
    clock: false,
    animation: false,
  });

  loading.value = true;

  // const resource = await Cesium.IonResource.fromAssetId(1450246);
  // const dataSource = await Cesium.GeoJsonDataSource.load(resource);
  const dataSource = await Cesium.GeoJsonDataSource.load(
    "https://dggrid-py-bozea3cspa-ew.a.run.app/api/grid_gen/ISEA7H/2",
    {
      stroke: Cesium.Color.AQUA,
      strokeWidth: 3,
    }
  );
  await viewer.dataSources.add(dataSource);
  await viewer.zoomTo(dataSource);
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
</style>
