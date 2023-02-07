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
        <label class="label">Enter DGGS resolution (~ 1-15):</label>
        <div class="control">
          <input class="input is-primary" type="text" v-model="sel_resolution">

        </div>
      </div>
      <div class="field">
        <div class="control">
          <button id="stats_button" class="button is-link">Stats</button>

        </div>
      </div>
      <div class="field">
        <label class="label">Select output format:</label>
        <div class="control select is-primary">
          <select v-model="sel_format">
            <option v-for="f in outformat_default.formats" :key="f" :value="f">{{ f }}</option>
          </select>

        </div>
      </div>
      <div class="field">
        <div class="control">
          <button id="gridgen_button" class="button is-info">Generate Grid</button>

        </div>
      </div>
      <div>dggs: {{ dggs_sel }} at resolution: 1
        with format: {{ sel_format }}
      </div>
    </div>

    <div class="column is-9 is-offset-3">
      <p>lorem ipsum</p>
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
import { reactive, computed } from 'vue'

onMounted(() => {
  // maybe initial ping to web service?
  console.log(`the component is now mounted.`)
})

const outformat_default = ref({ formats: ["GPKG", "SHAPEZIP", "FLATGEOBUF", "GEOJSON", "KML"] });
const sel_format = ref("GEOJSON");

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

const dggs_sel = ref("ISEA3H");

const max_resolution = reactive(20);
const sel_resolution = ref(1);

// depending on dggs and later also visible area, allow range of resolutions
// but for stats its fine
const allowResolutionsForDggs = computed(() => {
  // [0, 1, 2, 3, 4, 5, 6, 7, 8, 9] etc non right inclusive
  const arr = [...Array(max_resolution).keys()];
  return arr;
})

</script>

