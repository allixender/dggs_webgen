<template>
  <div class="box">
    <h1 class="title">Generate and download different Discrete Global Grid Systems</h1>
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
        <label class="label">Select output format:</label>
        <div class="control select is-primary">
          <select v-model="sel_format">
            <option v-for="f in outformat_default.formats" :key="f" :value="f">{{ f }}</option>
          </select>

        </div>
      </div>
      <div class="field">
        <div class="control">
          <button id="gridgen_button" class="button is-info" @click="getData">Generate Grid</button>

        </div>
      </div>
      <div>dggs: {{ dggs_sel }} at resolution: {{ sel_resolution }}
        with format: {{ sel_format }}
        <p v-if="loading">
          Loading...
        </p>
        <p v-if="error">
          {{ error_info }}
        </p>
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
import { reactive, computed } from 'vue'

onMounted(() => {
  // maybe initial ping to web service?
  console.log(`the component is now mounted.`)
})

const outformat_default = ref({ formats: ["FLATGEOBUF", "GEOJSON", "KML"] });
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

const loading = ref(false);
const error = ref(null);
const error_info = ref(null);

const getData = () => {
  error.value = false
  loading.value = true;
  const data_url = `https://dggrid-py-bozea3cspa-ew.a.run.app/api/grid_gen/${dggs_sel.value}/${sel_resolution.value}?format=${sel_format.value}`;

  fetch(data_url)
    .then(response => response.blob()).then((blob) => {
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.style.display = 'none';
      a.href = url;
      // the filename you want
      a.download = `${dggs_sel.value}.${sel_format.value}`;
      document.body.appendChild(a);
      a.click();
      // a.remove();

      loading.value = false;
    }).catch((error_obj) => {
      error.value = true;
      console.log(error_obj);
      error_info.value = 'Looks like there was a problem: \n' + error_obj;
      loading.value = false;
    });
}

</script>

