<template>
  <div class="globe">
    <h1>Globe.gl</h1>
  </div>
  <div class="container">
    <div ref="globeViz" id="globeViz"></div>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import Globe from "globe.gl";

const globeViz = ref(null);
const myImageUrl = "//unpkg.com/three-globe/example/img/earth-night.jpg";

const data_geo =
  "https://raw.githubusercontent.com/vasturiano/globe.gl/master/example/datasets/ne_110m_admin_0_countries.geojson";

const demo_grid =
  "https://dggrid-py-bozea3cspa-ew.a.run.app/api/grid_gen/ISEA7H/2";

// let url = demo_grid;
let url = data_geo;

onMounted(() => {
  const myGlobe = Globe();

  fetch(url)
    .then((res) => res.json())
    .then((countries) => {
      myGlobe(globeViz.value)
        .globeImageUrl(myImageUrl)
        .polygonsData(
          countries.features
          // countries.features.filter((d) => d.properties.ISO_A2 !== "AQ")
        )
        .polygonAltitude(0.005)
        .polygonStrokeColor(() => "rgb(211,211,211)")
        .polygonCapColor(() => "rgba(255, 165 ,0 , 0.5)")
        .polygonSideColor(() => "rgba(0, 100, 0, 0.15)");
    });
});
</script>
